"""
Flux Open Home - Homeowner Dashboard API
==========================================
Unauthenticated endpoints for the homeowner dashboard UI.
These run behind HA ingress (already authenticated) and only work in homeowner mode.
"""

import asyncio
import json
import os
import re
import httpx
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Any
from config import get_config
import ha_client
import run_log
from config_changelog import log_change, get_actor, friendly_entity_name


_ZONE_NUMBER_RE = re.compile(r'zone[_]?(\d+)', re.IGNORECASE)


def _extract_zone_number(entity_id: str) -> int:
    """Extract the numeric zone number from an entity_id (e.g., 'switch.xxx_zone_3' → 3)."""
    m = _ZONE_NUMBER_RE.search(entity_id)
    return int(m.group(1)) if m else 0


router = APIRouter(prefix="/admin/api/homeowner", tags=["Homeowner Dashboard"])

ALIASES_FILE = "/data/homeowner_aliases.json"


def _require_homeowner_mode():
    """No-op — homeowner endpoints are always available.

    Previously this blocked requests when not in homeowner mode, but the
    dashboard auto-refreshes every 30 seconds. If the user switches to
    management mode from the Configuration page while the homeowner tab
    is still open, the refresh calls would fail with 400 errors.

    The mode setting only controls which HTML page is served by default
    at GET /admin. The underlying API should work regardless of mode
    since it runs behind authenticated HA ingress.
    """
    pass


def _require_data_control(request: Request):
    """Block destructive data operations in managed mode.

    When system_mode is 'managed', only requests from the management
    company (identified by X-Actor: Management header or query param)
    are allowed to clear logs, reset data, etc.  Homeowner requests
    get a 403.

    In standalone mode, no restrictions — homeowner has full control.

    Note: Nabu Casa proxy passes extra_headers as query params because
    HA rest_command cannot forward custom HTTP headers.
    """
    config = get_config()
    if config.system_mode != "managed":
        return  # Standalone — no restrictions
    actor = request.headers.get("X-Actor", "") or request.query_params.get("X-Actor", "")
    if actor == "Management":
        return  # Management company — allowed
    raise HTTPException(
        status_code=403,
        detail="Data management is controlled by your irrigation management company.",
    )


# --- Zone Aliases ---

def _load_aliases() -> dict:
    """Load homeowner zone aliases from persistent storage."""
    if not os.path.exists(ALIASES_FILE):
        return {}
    try:
        with open(ALIASES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_aliases(aliases: dict):
    """Save homeowner zone aliases to persistent storage."""
    os.makedirs(os.path.dirname(ALIASES_FILE), exist_ok=True)
    with open(ALIASES_FILE, "w") as f:
        json.dump(aliases, f, indent=2)


# --- Models ---

class ZoneStartRequest(BaseModel):
    duration_minutes: Optional[int] = Field(
        default=None, ge=1, le=480,
        description="Duration in minutes (1-480). If omitted, runs until manually stopped.",
    )


class EntitySetRequest(BaseModel):
    state: Optional[str] = None
    value: Optional[Any] = None
    option: Optional[str] = None


class UpdateAliasesRequest(BaseModel):
    zone_aliases: dict


class SaveZoneHeadsRequest(BaseModel):
    heads: list = Field(default_factory=list, description="List of head detail objects")
    notes: str = Field("", max_length=2000, description="General zone notes")
    show_gpm_on_card: bool = Field(False, description="Show total GPM on zone card")
    show_head_count_on_card: bool = Field(False, description="Show head count on zone card")
    area_sqft: float = Field(0, ge=0, description="Zone area in square feet")
    soil_type: str = Field("", description="Soil type: sandy, sandy_loam, loam, clay_loam, silty_clay, clay, rock_gravel")


class UpdateNotificationPrefsRequest(BaseModel):
    enabled: Optional[bool] = None
    service_appointments: Optional[bool] = None
    system_changes: Optional[bool] = None
    weather_changes: Optional[bool] = None
    moisture_changes: Optional[bool] = None
    equipment_changes: Optional[bool] = None
    duration_changes: Optional[bool] = None
    report_changes: Optional[bool] = None


class RecordNotificationRequest(BaseModel):
    event_type: str = Field(..., description="Notification category key")
    title: str = Field(..., max_length=200)
    message: str = Field("", max_length=1000)


class UpdateHANotificationSettingsRequest(BaseModel):
    enabled: Optional[bool] = None
    ha_notify_service: Optional[str] = Field(None, max_length=200)
    notify_service_appointments: Optional[bool] = None
    notify_system_changes: Optional[bool] = None
    notify_weather_changes: Optional[bool] = None
    notify_moisture_changes: Optional[bool] = None
    notify_equipment_changes: Optional[bool] = None
    notify_duration_changes: Optional[bool] = None
    notify_report_changes: Optional[bool] = None


# --- Helper functions ---

def _zone_name(entity_id: str) -> str:
    if "." in entity_id:
        return entity_id.split(".", 1)[1]
    return entity_id


def _resolve_zone_entity(zone_id: str, config) -> str:
    if zone_id in config.allowed_zone_entities:
        return zone_id
    for domain in ("switch", "valve"):
        entity_id = f"{domain}.{zone_id}"
        if entity_id in config.allowed_zone_entities:
            return entity_id
    raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")


def _get_zone_service(entity_id: str, action: str) -> tuple[str, str]:
    domain = entity_id.split(".")[0] if "." in entity_id else "switch"
    if domain == "valve":
        return ("valve", "open" if action == "on" else "close")
    else:
        return ("switch", "turn_on" if action == "on" else "turn_off")


# --- Endpoints ---

@router.get("/status", summary="Get system status")
async def homeowner_status():
    """Get comprehensive system status for the homeowner dashboard."""
    _require_homeowner_mode()
    config = get_config()

    ha_connected = await ha_client.check_connection()

    zones = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    max_zones = config.detected_zone_count  # 0 = no limit (no expansion board)
    if max_zones > 0:
        zones = [z for z in zones if _extract_zone_number(z.get("entity_id", "")) <= max_zones]

    # Exclude pump/master valve zones via zone mode entities (authoritative source)
    _ZONE_MODE_RE = re.compile(r"zone_\d+_mode", re.IGNORECASE)
    mode_eids = [e for e in config.allowed_control_entities if _ZONE_MODE_RE.search(e)]
    special_zone_nums = set()
    if mode_eids:
        mode_entities = await ha_client.get_entities_by_ids(mode_eids)
        for me in mode_entities:
            mode_val = (me.get("state") or "").lower()
            zone_num = _extract_zone_number(me.get("entity_id", ""))
            if re.search(r'pump|relay', mode_val, re.IGNORECASE):
                if zone_num:
                    special_zone_nums.add(zone_num)
            elif re.search(r'master.*valve|valve.*master', mode_val, re.IGNORECASE):
                if zone_num:
                    special_zone_nums.add(zone_num)
    zones = [z for z in zones if _extract_zone_number(z.get("entity_id", "")) not in special_zone_nums]

    # Exclude "not used" zones from count
    used_zones = [z for z in zones if not is_zone_not_used(z.get("entity_id", ""))]
    active_zones = [z for z in used_zones if z.get("state") == "on"]
    sensors = await ha_client.get_entities_by_ids(config.allowed_sensor_entities)

    # Check schedule state for pause/rain delay
    from routes.schedule import _load_schedules
    schedule_data = _load_schedules()

    rain_delay_until = schedule_data.get("rain_delay_until")
    rain_delay_active = False
    if rain_delay_until:
        try:
            delay_end = datetime.fromisoformat(rain_delay_until)
            rain_delay_active = datetime.now(timezone.utc) < delay_end
        except ValueError:
            pass

    active_zone_eid = None
    active_zone_name = None
    if active_zones:
        az = active_zones[0]
        active_zone_eid = az.get("entity_id")
        attrs = az.get("attributes", {})
        active_zone_name = attrs.get("friendly_name") or active_zone_eid

    # --- Weather multiplier (read directly from weather rules file) ---
    weather_multiplier = 1.0
    try:
        from routes.weather import _load_weather_rules
        weather_rules = _load_weather_rules()
        weather_multiplier = weather_rules.get("watering_multiplier", 1.0)
    except Exception:
        pass

    # --- Moisture probe status (enabled flag only; multiplier is per-zone) ---
    moisture_enabled = False
    try:
        from routes.moisture import _load_data as _load_moisture_data
        moisture_data = _load_moisture_data()
        moisture_enabled = moisture_data.get("enabled", False)
    except Exception:
        pass

    return {
        "online": True,
        "ha_connected": ha_connected,
        "system_paused": schedule_data.get("system_paused", False),
        "weather_schedule_disabled": schedule_data.get("weather_schedule_disabled", False),
        "weather_disable_reason": schedule_data.get("weather_disable_reason", ""),
        "total_zones": len(used_zones),
        "active_zones": len(active_zones),
        "active_zone_entity_id": active_zone_eid,
        "active_zone_name": active_zone_name,
        "total_sensors": len(sensors),
        "rain_delay_active": rain_delay_active,
        "rain_delay_until": rain_delay_until if rain_delay_active else None,
        "moisture_enabled": moisture_enabled,
        "weather_multiplier": weather_multiplier,
        "uptime_check": datetime.now(timezone.utc).isoformat(),
        # Include homeowner contact/address info (synced live to management)
        "address": config.homeowner_address or "",
        "city": config.homeowner_city or "",
        "state": config.homeowner_state or "",
        "zip": config.homeowner_zip or "",
        "phone": config.homeowner_phone or "",
        "first_name": config.homeowner_first_name or "",
        "last_name": config.homeowner_last_name or "",
    }


@router.get("/zones", summary="List all zones")
async def homeowner_zones():
    """Get status of all irrigation zones."""
    _require_homeowner_mode()
    config = get_config()

    entities = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    zones = []
    max_zones = config.detected_zone_count  # 0 = no limit (no expansion board)
    for entity in entities:
        # Filter zones beyond the detected expansion board zone count
        if max_zones > 0:
            zn = _extract_zone_number(entity["entity_id"])
            if zn > max_zones:
                continue
        attrs = entity.get("attributes", {})
        zones.append({
            "entity_id": entity["entity_id"],
            "name": _zone_name(entity["entity_id"]),
            "state": entity.get("state", "unknown"),
            "friendly_name": attrs.get("friendly_name"),
            "last_changed": entity.get("last_changed"),
            "attributes": attrs,
        })
    return zones


# --- Not Used Zones (backend storage) ---
NOT_USED_ZONES_FILE = "/data/not_used_zones.json"


def load_not_used_zones() -> dict:
    """Load the not-used zones map from disk. Returns {zone_number_str: True}."""
    if os.path.exists(NOT_USED_ZONES_FILE):
        try:
            with open(NOT_USED_ZONES_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_not_used_zones(data: dict):
    """Save not-used zones map to disk."""
    os.makedirs(os.path.dirname(NOT_USED_ZONES_FILE), exist_ok=True)
    with open(NOT_USED_ZONES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def is_zone_not_used(zone_entity_id: str) -> bool:
    """Check if a zone is marked as 'not used' by its entity_id."""
    zn = _extract_zone_number(zone_entity_id)
    if zn <= 0:
        return False
    return str(zn) in load_not_used_zones()


@router.get("/zones/not-used", summary="Get not-used zones")
async def get_not_used_zones():
    """Get the map of zones marked as 'not used'."""
    return {"zones": load_not_used_zones()}


@router.put("/zones/not-used", summary="Update not-used zones")
async def set_not_used_zones(request: Request):
    """Set the map of zones marked as 'not used'. Body: {zones: {zone_number: true/false}}."""
    try:
        body = await request.json()
    except Exception:
        return {"success": False, "error": "Invalid JSON body"}
    # Support both {zones: {...}} wrapper and flat {zone_number: true} format
    zones_map = body.get("zones", body) if isinstance(body, dict) else body
    # Only keep truthy values
    clean = {str(k): True for k, v in zones_map.items() if v}
    _save_not_used_zones(clean)
    return {"success": True, "zones": clean}


@router.post("/zones/{zone_id}/start", summary="Start a zone")
async def homeowner_start_zone(zone_id: str, body: ZoneStartRequest, request: Request):
    """Start an irrigation zone, optionally with a timed duration."""
    _require_homeowner_mode()
    config = get_config()

    entity_id = _resolve_zone_entity(zone_id, config)
    entity = await ha_client.get_entity_state(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")

    svc_domain, svc_name = _get_zone_service(entity_id, "on")
    success = await ha_client.call_service(svc_domain, svc_name, {"entity_id": entity_id})
    if not success:
        raise HTTPException(status_code=502, detail="Failed to communicate with Home Assistant.")

    run_log.log_zone_event(
        entity_id=entity_id, state="on", source="dashboard",
        zone_name=_zone_name(entity_id),
    )

    # If duration specified, apply combined multiplier and schedule automatic shutoff
    adjusted_duration = body.duration_minutes
    moisture_skip = False
    if body.duration_minutes:
        try:
            from routes.moisture import get_combined_multiplier
            mult_result = await get_combined_multiplier(entity_id)
            if mult_result.get("moisture_skip"):
                moisture_skip = True
            elif mult_result["combined_multiplier"] != 1.0:
                adjusted_duration = max(1, round(body.duration_minutes * mult_result["combined_multiplier"]))
                if adjusted_duration != body.duration_minutes:
                    print(f"[HOMEOWNER] Duration adjusted: {body.duration_minutes} → {adjusted_duration} min "
                          f"(weather={mult_result['weather_multiplier']}, "
                          f"moisture={mult_result['moisture_multiplier']})")
        except Exception as e:
            print(f"[HOMEOWNER] Multiplier lookup failed, using original duration: {e}")

    # Build warning for moisture skip (zone keeps running — user chose manual start)
    moisture_warning = ""
    if moisture_skip:
        try:
            moisture_warning = mult_result.get("moisture_reason", "Soil moisture above skip threshold")
        except Exception:
            moisture_warning = "Soil moisture above skip threshold"
        print(f"[HOMEOWNER] Manual start with moisture warning: {entity_id} — {moisture_warning}")

    if adjusted_duration:
        from routes.zones import _timed_run_tasks, _timed_shutoff
        existing = _timed_run_tasks.pop(entity_id, None)
        if existing and not existing.done():
            existing.cancel()
        task = asyncio.create_task(_timed_shutoff(entity_id, adjusted_duration))
        _timed_run_tasks[entity_id] = task

    message = f"Zone '{zone_id}' started"
    desc = f"Started {_zone_name(entity_id).replace('_', ' ').title()}"
    if body.duration_minutes:
        if adjusted_duration != body.duration_minutes:
            message += f" for {adjusted_duration} minutes (adjusted from {body.duration_minutes})"
        else:
            message += f" for {adjusted_duration} minutes"
        desc += f" for {body.duration_minutes} min"

    log_change(get_actor(request), "Zone Control", desc, {"entity_id": entity_id})

    resp = {"success": True, "zone_id": zone_id, "action": "start", "message": message}
    if moisture_warning:
        resp["warning"] = moisture_warning
    return resp


@router.post("/zones/{zone_id}/stop", summary="Stop a zone")
async def homeowner_stop_zone(zone_id: str, request: Request):
    """Stop an irrigation zone."""
    _require_homeowner_mode()
    config = get_config()

    entity_id = _resolve_zone_entity(zone_id, config)
    entity = await ha_client.get_entity_state(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")

    # Cancel any active timed run
    from routes.zones import _timed_run_tasks
    existing = _timed_run_tasks.pop(entity_id, None)
    if existing and not existing.done():
        existing.cancel()

    svc_domain, svc_name = _get_zone_service(entity_id, "off")
    success = await ha_client.call_service(svc_domain, svc_name, {"entity_id": entity_id})
    if not success:
        raise HTTPException(status_code=502, detail="Failed to communicate with Home Assistant.")

    run_log.log_zone_event(
        entity_id=entity_id, state="off", source="dashboard",
        zone_name=_zone_name(entity_id),
    )

    log_change(get_actor(request), "Zone Control",
               f"Stopped {_zone_name(entity_id).replace('_', ' ').title()}",
               {"entity_id": entity_id})

    return {"success": True, "zone_id": zone_id, "action": "stop", "message": f"Zone '{zone_id}' stopped"}


@router.post("/zones/stop_all", summary="Emergency stop all zones")
async def homeowner_stop_all(request: Request):
    """Emergency stop — turn off all irrigation zones."""
    _require_homeowner_mode()
    config = get_config()

    # Cancel all active timed runs
    from routes.zones import _timed_run_tasks
    for eid, task in list(_timed_run_tasks.items()):
        if not task.done():
            task.cancel()
    _timed_run_tasks.clear()

    entities = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    stopped = []
    for entity in entities:
        entity_id = entity["entity_id"]
        state = entity.get("state", "")
        if state in ("on", "open"):
            svc_domain, svc_name = _get_zone_service(entity_id, "off")
            await ha_client.call_service(svc_domain, svc_name, {"entity_id": entity_id})
            run_log.log_zone_event(
                entity_id=entity_id, state="off", source="stop_all",
                zone_name=_zone_name(entity_id),
            )
            stopped.append(entity_id)

    log_change(get_actor(request), "Zone Control", "Emergency stop — all zones",
               {"stopped": len(stopped)})

    return {
        "success": True,
        "zone_id": "all",
        "action": "stop_all",
        "message": f"Stopped {len(stopped)} active zone(s)",
    }


@router.get("/sensors", summary="Get all sensor readings")
async def homeowner_sensors():
    """Get current readings from all irrigation sensors."""
    _require_homeowner_mode()
    config = get_config()

    entities = await ha_client.get_entities_by_ids(config.allowed_sensor_entities)
    sensors = []
    warnings = []

    for entity in entities:
        attrs = entity.get("attributes", {})
        state = entity.get("state", "unknown")
        sensors.append({
            "entity_id": entity["entity_id"],
            "name": _zone_name(entity["entity_id"]),
            "state": state,
            "unit_of_measurement": attrs.get("unit_of_measurement"),
            "device_class": attrs.get("device_class"),
            "friendly_name": attrs.get("friendly_name"),
            "last_changed": entity.get("last_changed"),
            "last_updated": entity.get("last_updated"),
            "attributes": attrs,
        })
        if state in ("unavailable", "unknown"):
            warnings.append(f"Sensor '{attrs.get('friendly_name') or entity['entity_id']}' is {state}")

    system_status = "ok"
    if any(s["state"] in ("unavailable", "unknown") for s in sensors):
        system_status = "warning"
    elif len(sensors) == 0:
        system_status = "error"
        warnings.append("No irrigation sensors found")

    return {
        "total_sensors": len(sensors),
        "sensors": sensors,
        "system_status": system_status,
        "warnings": warnings,
    }


@router.get("/entities", summary="List all device control entities")
async def homeowner_entities():
    """Get current state of all device control entities."""
    _require_homeowner_mode()
    config = get_config()

    states = await ha_client.get_entities_by_ids(config.allowed_control_entities)
    entities = []
    for entity in states:
        eid = entity.get("entity_id", "")
        attrs = entity.get("attributes", {})
        domain = eid.split(".")[0] if "." in eid else ""
        entities.append({
            "entity_id": eid,
            "name": _zone_name(eid),
            "domain": domain,
            "state": entity.get("state", "unknown"),
            "friendly_name": attrs.get("friendly_name"),
            "last_changed": entity.get("last_changed"),
            "last_updated": entity.get("last_updated"),
            "attributes": attrs,
        })

    return {"total": len(entities), "entities": entities}


@router.post("/entities/{entity_id:path}/set", summary="Set entity value")
async def homeowner_set_entity(
    entity_id: str,
    body: EntitySetRequest,
    request: Request,
    force: bool = Query(False, description="Skip probe wake conflict check"),
):
    """Set the value of a device control entity."""
    _require_homeowner_mode()
    config = get_config()

    if entity_id not in config.allowed_control_entities:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")

    domain = entity_id.split(".")[0] if "." in entity_id else ""

    # Pre-flight conflict check for zone duration changes
    if domain == "number" and body.value is not None and not force:
        try:
            from routes.moisture import check_timeline_conflicts, _find_duration_entities
            dur_entities = _find_duration_entities(config.allowed_control_entities)
            if entity_id in dur_entities:
                conflicts = await check_timeline_conflicts(
                    override_zone_duration={entity_id: float(body.value)}
                )
                if conflicts:
                    return JSONResponse(content={
                        "success": False,
                        "status": "conflict",
                        "conflicts": conflicts,
                        "entity_id": entity_id,
                        "proposed_value": body.value,
                        "message": "This duration change would prevent probe wake scheduling",
                    })
        except ImportError:
            pass
        except Exception as e:
            print(f"[HOMEOWNER] Conflict check failed for {entity_id}: {e}")

    # Fetch current state before changing it (for changelog old → new)
    old_state = await ha_client.get_entity_state(entity_id)
    old_val = old_state.get("state", "unknown") if old_state else "unknown"

    from routes.entities import _get_set_service
    svc_domain, svc_name, extra_data = _get_set_service(domain, body)
    service_data = {"entity_id": entity_id, **extra_data}

    success = await ha_client.call_service(svc_domain, svc_name, service_data)
    if not success:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to call {svc_domain}.{svc_name} for {entity_id}.",
        )

    # If this is a duration entity, always update stored base_durations so the
    # user-set value is treated as the base.  When Apply Factors is active,
    # re-apply the factor immediately so HA gets base × multiplier.
    if domain == "number" and body.value is not None:
        try:
            from routes.moisture import (
                _load_data as _load_moisture_data,
                _save_data as _save_moisture_data,
                apply_adjusted_durations,
                _find_duration_entities,
            )
            from config import get_config as _get_config
            cfg = _get_config()
            dur_entities = _find_duration_entities(cfg.allowed_control_entities)
            if entity_id in dur_entities:
                mdata = _load_moisture_data()
                base_durations = mdata.get("base_durations", {})
                base_durations[entity_id] = base_durations.get(entity_id, {})
                base_durations[entity_id]["base_value"] = float(body.value)
                base_durations[entity_id]["captured_at"] = datetime.now(timezone.utc).isoformat()
                mdata["base_durations"] = base_durations
                _save_moisture_data(mdata)
                print(f"[HOMEOWNER] Updated base duration for {entity_id} to {body.value}")
                if mdata.get("apply_factors_to_schedule"):
                    await apply_adjusted_durations()
        except Exception as e:
            print(f"[HOMEOWNER] Base duration update after set failed: {e}")

    # Log configuration change with old → new
    actor = get_actor(request)
    fname = friendly_entity_name(entity_id)
    new_val = body.value if body.value is not None else body.state if body.state is not None else body.option
    log_change(actor, "Schedule", f"Set {fname}: {old_val} -> {new_val}",
               {"entity_id": entity_id, "old_value": old_val, "new_value": new_val})

    return {
        "success": True,
        "entity_id": entity_id,
        "action": f"{svc_domain}.{svc_name}",
        "message": f"Called {svc_domain}.{svc_name} on {entity_id}",
    }


@router.post("/system/pause", summary="Pause irrigation system")
async def homeowner_pause(request: Request):
    """Pause all irrigation. Active zones will be stopped."""
    _require_homeowner_mode()
    config = get_config()

    zones = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    for zone in zones:
        state = zone.get("state", "")
        if state in ("on", "open"):
            entity_id = zone["entity_id"]
            svc_domain, svc_name = _get_zone_service(entity_id, "off")
            await ha_client.call_service(svc_domain, svc_name, {"entity_id": entity_id})
            run_log.log_zone_event(
                entity_id=entity_id, state="off", source="system_pause",
                zone_name=_zone_name(entity_id),
            )

    # Disable ESPHome schedule programs so the controller can't start runs
    import schedule_control
    saved_states = await schedule_control.disable_schedules()

    from routes.schedule import _load_schedules, _save_schedules
    data = _load_schedules()
    data["system_paused"] = True
    if saved_states:
        data["saved_schedule_states"] = saved_states
    _save_schedules(data)

    await ha_client.fire_event(
        "flux_irrigation_system_paused",
        {"source": "homeowner_dashboard"},
    )

    log_change(get_actor(request), "System", "Paused irrigation system")

    return {"success": True, "system_paused": True, "message": "Irrigation system paused."}


@router.post("/system/resume", summary="Resume irrigation system")
async def homeowner_resume(request: Request):
    """Resume the irrigation system after a pause."""
    _require_homeowner_mode()

    # Restore ESPHome schedule programs to their prior state
    import schedule_control
    from routes.schedule import _load_schedules, _save_schedules
    data = _load_schedules()
    saved_states = data.get("saved_schedule_states", {})
    await schedule_control.restore_schedules(saved_states)

    data["system_paused"] = False
    data["weather_schedule_disabled"] = False
    data.pop("weather_paused", None)
    data.pop("weather_pause_reason", None)
    data.pop("weather_disable_reason", None)
    data.pop("saved_schedule_states", None)
    _save_schedules(data)

    await ha_client.fire_event(
        "flux_irrigation_system_resumed",
        {"source": "homeowner_dashboard"},
    )

    log_change(get_actor(request), "System", "Resumed irrigation system")

    return {"success": True, "system_paused": False, "message": "Irrigation system resumed."}


@router.get("/history/runs", summary="Get run history")
async def homeowner_history(
    hours: int = Query(24, ge=1, le=8760, description="Hours of history (max 1 year)"),
    zone_id: Optional[str] = Query(None, description="Filter by entity_id"),
):
    """Get irrigation run history from the local JSONL log.

    Each event includes weather conditions captured at the time it happened.
    """
    _require_homeowner_mode()

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    events = run_log.get_run_history(hours=hours, zone_id=zone_id)

    # Get current weather for the summary header
    current_weather = {}
    try:
        from routes.weather import _get_current_weather_snapshot
        current_weather = _get_current_weather_snapshot()
    except Exception:
        pass

    return {
        "period_start": start_time.isoformat(),
        "period_end": end_time.isoformat(),
        "events": events,
        "total_run_events": len([e for e in events if e.get("state") in ("on", "open")]),
        "current_weather": current_weather,
    }


@router.get("/geocode", summary="Geocode an address")
async def homeowner_geocode(q: str = Query(..., min_length=3, description="Address to geocode")):
    """Proxy geocoding via Nominatim so the browser doesn't need cross-origin access."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"format": "json", "limit": "1", "q": q},
                headers={"User-Agent": "FluxIrrigationAPI/1.1.11"},
            )
            resp.raise_for_status()
            results = resp.json()
            if results and len(results) > 0:
                return {"lat": float(results[0]["lat"]), "lon": float(results[0]["lon"])}
            return {"lat": None, "lon": None}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Geocoding failed: {e}")


@router.get("/weather", summary="Get weather data for dashboard")
async def homeowner_weather():
    """Get current weather conditions and active adjustments for the dashboard."""
    config = get_config()
    from routes.weather import get_weather_data, _load_weather_rules, _load_external_weather

    # Check if external weather is available (pushed by management server)
    has_external = _load_external_weather(max_age_minutes=10.0) is not None

    weather_configured = config.weather_entity_id or config.weather_source == "nws" or has_external
    if not has_external and (not config.weather_enabled or not weather_configured):
        return {"weather_enabled": False, "weather": {"error": "Not configured"}}

    weather = await get_weather_data()
    rules_data = _load_weather_rules()

    # Determine weather source for badge display
    # If external weather is being pushed by management server, show "management"
    # regardless of the underlying API (OWM, etc.)
    if has_external:
        weather_source = "management"
    else:
        weather_source = config.weather_source or "ha_entity"

    return {
        "weather_enabled": True,
        "weather": weather,
        "weather_source": weather_source,
        "active_adjustments": rules_data.get("active_adjustments", []),
        "watering_multiplier": rules_data.get("watering_multiplier", 1.0),
        "last_evaluation": rules_data.get("last_evaluation"),
    }


@router.get("/history/runs/csv", summary="Export run history as CSV")
async def homeowner_history_csv(
    hours: int = Query(24, ge=1, le=8760, description="Hours of history (max 1 year)"),
):
    """Export irrigation run history as a downloadable CSV file."""
    from fastapi.responses import Response

    _require_homeowner_mode()

    events = run_log.get_run_history(hours=hours)

    lines = ["timestamp,zone_name,entity_id,state,source,duration_minutes,weather_condition,temperature,humidity,wind_speed,watering_multiplier,weather_rules,moisture_multiplier,combined_multiplier,probe_top_pct,probe_mid_pct,probe_bottom_pct,probe_profile"]
    for e in events:
        dur = ""
        if e.get("duration_seconds") is not None:
            dur = str(round(e["duration_seconds"] / 60, 1))
        wx = e.get("weather") or {}
        mo = e.get("moisture") or {}
        rules_str = ";".join(wx.get("active_adjustments", []))
        # Moisture/combined multiplier only for schedule events
        moisture_mult = ""
        combined_mult = ""
        probe_top = ""
        probe_mid = ""
        probe_bottom = ""
        probe_profile = ""
        if e.get("source") == "schedule":
            if mo.get("moisture_multiplier") is not None:
                moisture_mult = str(mo["moisture_multiplier"])
            if mo.get("combined_multiplier") is not None:
                combined_mult = str(mo["combined_multiplier"])
            sr = mo.get("sensor_readings") or {}
            if sr.get("T") is not None:
                probe_top = str(sr["T"])
            if sr.get("M") is not None:
                probe_mid = str(sr["M"])
            if sr.get("B") is not None:
                probe_bottom = str(sr["B"])
            if mo.get("profile"):
                probe_profile = mo["profile"]
        line = ",".join([
            e.get("timestamp", ""),
            _csv_escape(e.get("zone_name", "")),
            e.get("entity_id", ""),
            e.get("state", ""),
            e.get("source", ""),
            dur,
            _csv_escape(str(wx.get("condition", ""))),
            _csv_escape(str(wx.get("temperature", ""))),
            _csv_escape(str(wx.get("humidity", ""))),
            _csv_escape(str(wx.get("wind_speed", ""))),
            _csv_escape(str(wx.get("watering_multiplier", ""))),
            _csv_escape(rules_str),
            moisture_mult,
            combined_mult,
            probe_top,
            probe_mid,
            probe_bottom,
            _csv_escape(probe_profile),
        ])
        lines.append(line)

    csv_content = "\n".join(lines) + "\n"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=irrigation_history_{hours}h.csv"},
    )


@router.get("/weather/log", summary="Get weather event log")
async def homeowner_weather_log(
    limit: int = Query(200, ge=1, le=10000),
    hours: int = Query(0, ge=0, le=8760),
):
    """Get the weather event log for the homeowner dashboard."""
    from routes.weather import get_weather_log
    return {"events": get_weather_log(limit=limit, hours=hours)}


@router.get("/weather/debug", summary="Weather data collection diagnostics")
async def homeowner_weather_debug():
    """Diagnostic endpoint to check weather data collection status."""
    import os
    from config import get_config
    from routes.weather import WEATHER_LOG_FILE, get_weather_log, get_weather_data

    config = get_config()
    result = {
        "weather_enabled": config.weather_enabled,
        "weather_source": config.weather_source,
        "weather_entity_id": config.weather_entity_id or None,
        "has_address": bool(config.homeowner_address or config.homeowner_zip),
        "log_file_exists": os.path.exists(WEATHER_LOG_FILE),
        "log_file_size_bytes": 0,
        "total_log_entries": 0,
        "entries_last_24h": 0,
        "event_types": {},
        "latest_entry": None,
        "live_weather_test": None,
    }

    if os.path.exists(WEATHER_LOG_FILE):
        result["log_file_size_bytes"] = os.path.getsize(WEATHER_LOG_FILE)

    all_entries = get_weather_log(limit=10000, hours=0)
    result["total_log_entries"] = len(all_entries)

    recent = get_weather_log(limit=10000, hours=24)
    result["entries_last_24h"] = len(recent)

    # Count event types
    for e in all_entries:
        evt = e.get("event", "unknown")
        result["event_types"][evt] = result["event_types"].get(evt, 0) + 1

    if all_entries:
        result["latest_entry"] = all_entries[-1]

    # Try live fetch
    try:
        weather = await get_weather_data()
        result["live_weather_test"] = {
            "success": "error" not in weather,
            "condition": weather.get("condition"),
            "temperature": weather.get("temperature"),
            "humidity": weather.get("humidity"),
            "error": weather.get("error"),
        }
    except Exception as e:
        result["live_weather_test"] = {"success": False, "error": str(e)}

    return result


@router.get("/weather/log/csv", summary="Export weather log as CSV")
async def homeowner_weather_log_csv(
    hours: int = Query(0, ge=0, le=8760),
):
    """Export the weather event log as a downloadable CSV."""
    from fastapi.responses import Response
    from routes.weather import get_weather_log

    events = get_weather_log(limit=10000, hours=hours)

    lines = ["timestamp,event,condition,temperature,humidity,wind_speed,watering_multiplier,rules_triggered,reason"]
    for e in events:
        rules = ";".join(e.get("triggered_rules", []))
        line = ",".join([
            _csv_escape(e.get("timestamp", "")),
            _csv_escape(e.get("event", "")),
            _csv_escape(str(e.get("condition", ""))),
            _csv_escape(str(e.get("temperature", ""))),
            _csv_escape(str(e.get("humidity", ""))),
            _csv_escape(str(e.get("wind_speed", ""))),
            _csv_escape(str(e.get("watering_multiplier", ""))),
            _csv_escape(rules),
            _csv_escape(e.get("reason", "")),
        ])
        lines.append(line)

    csv_content = "\n".join(lines) + "\n"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=weather_log.csv"},
    )


def _csv_escape(value: str) -> str:
    """Escape a value for CSV output."""
    if not value or value == "None":
        return ""
    if "," in value or '"' in value or "\n" in value:
        return '"' + value.replace('"', '""') + '"'
    return value


@router.delete("/weather/log", summary="Clear weather event log")
async def homeowner_clear_weather_log(request: Request):
    """Clear the weather event log."""
    _require_data_control(request)
    from routes.weather import WEATHER_LOG_FILE
    try:
        if os.path.exists(WEATHER_LOG_FILE):
            os.remove(WEATHER_LOG_FILE)
        log_change(get_actor(request), "Weather", "Cleared weather event log")
        return {"success": True, "message": "Weather log cleared"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/history/runs", summary="Clear run history")
async def homeowner_clear_history(request: Request):
    """Clear the local run history log."""
    _require_data_control(request)
    success = run_log.clear_run_history()
    if success:
        log_change(get_actor(request), "Run History", "Cleared all run history")
        return {"success": True, "message": "Run history cleared"}
    return {"success": False, "error": "Failed to clear run history"}


@router.get("/debug/moisture-log", summary="Get moisture skip debug log")
async def homeowner_moisture_debug_log(lines: int = Query(200, ge=1, le=500)):
    """Get the moisture skip debug log for troubleshooting schedule skip issues."""
    _require_homeowner_mode()
    from routes.moisture import get_debug_log, clear_debug_log
    return {"lines": get_debug_log(lines)}


@router.delete("/debug/moisture-log", summary="Clear moisture debug log")
async def homeowner_clear_moisture_debug_log(request: Request):
    """Clear the moisture skip debug log."""
    _require_data_control(request)
    from routes.moisture import clear_debug_log
    clear_debug_log()
    return {"success": True}


@router.get("/debug/remote-log", summary="Get remote device debug log")
async def homeowner_remote_debug_log(lines: int = Query(200, ge=1, le=500)):
    """Get the remote device sync debug log for troubleshooting entity mirroring."""
    _require_homeowner_mode()
    from run_log import get_remote_debug_log
    return {"lines": get_remote_debug_log(lines)}


@router.delete("/debug/remote-log", summary="Clear remote device debug log")
async def homeowner_clear_remote_debug_log(request: Request):
    """Clear the remote device debug log."""
    _require_data_control(request)
    from run_log import clear_remote_debug_log
    clear_remote_debug_log()
    return {"success": True}


@router.get("/zone_aliases", summary="Get zone aliases")
async def homeowner_get_aliases():
    """Get the homeowner's zone display name aliases."""
    _require_homeowner_mode()
    return _load_aliases()


@router.put("/zone_aliases", summary="Update zone aliases")
async def homeowner_update_aliases(body: UpdateAliasesRequest, request: Request):
    """Update the homeowner's zone display name aliases."""
    _require_homeowner_mode()
    old_aliases = _load_aliases()
    _save_aliases(body.zone_aliases)

    # Log individual alias changes with old → new
    actor = get_actor(request)
    all_keys = set(list(old_aliases.keys()) + list(body.zone_aliases.keys()))
    changes_logged = False
    for key in sorted(all_keys):
        old_name = old_aliases.get(key, "")
        new_name = body.zone_aliases.get(key, "")
        if old_name != new_name:
            zone_label = key.split(".", 1)[1].replace("_", " ").title() if "." in key else key
            if old_name and new_name:
                log_change(actor, "Schedule", f"Zone alias {zone_label}: {old_name} -> {new_name}")
            elif new_name:
                log_change(actor, "Schedule", f"Zone alias {zone_label}: (default) -> {new_name}")
            else:
                log_change(actor, "Schedule", f"Zone alias {zone_label}: {old_name} -> (default)")
            changes_logged = True
    if not changes_logged:
        log_change(actor, "Schedule", "Updated zone aliases (no changes)")

    return {"success": True, "zone_aliases": body.zone_aliases}


# --- Configuration Change Log ---

@router.get("/changelog", summary="Get configuration change log")
async def homeowner_changelog(
    limit: int = Query(200, ge=1, le=1000, description="Max entries"),
):
    """Get the configuration change log, newest first."""
    from config_changelog import get_changelog as _get_changelog
    return {"entries": _get_changelog(limit=limit)}


@router.get("/changelog/csv", summary="Export change log as CSV")
async def homeowner_changelog_csv():
    """Export the configuration change log as a downloadable CSV file."""
    from fastapi.responses import Response
    from config_changelog import export_changelog_csv
    csv_content = export_changelog_csv()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=config_changelog.csv"},
    )


# --- Zone Nozzle / Head Details ---

@router.get("/zone_heads/reference", summary="Get nozzle type reference data")
async def homeowner_nozzle_reference():
    """Get professional sprinkler head type reference data for the UI."""
    import zone_nozzle_data
    return zone_nozzle_data.get_reference_data()


@router.get("/zone_heads", summary="Get all zones head details")
async def homeowner_get_all_zone_heads():
    """Get head/nozzle details for all zones."""
    _require_homeowner_mode()
    import zone_nozzle_data
    return zone_nozzle_data.get_all_zones_heads()


@router.get("/zone_heads/{entity_id:path}", summary="Get zone head details")
async def homeowner_get_zone_heads(entity_id: str):
    """Get head/nozzle details for a specific zone."""
    _require_homeowner_mode()
    import zone_nozzle_data
    return zone_nozzle_data.get_zone_heads(entity_id)


@router.put("/zone_heads/{entity_id:path}", summary="Save zone head details")
async def homeowner_save_zone_heads(entity_id: str, body: SaveZoneHeadsRequest, request: Request):
    """Save head/nozzle details for a specific zone."""
    _require_homeowner_mode()
    import zone_nozzle_data

    # Validate each head has required fields
    for i, head in enumerate(body.heads):
        if not isinstance(head, dict):
            raise HTTPException(status_code=400, detail=f"Head {i} must be an object")
        if not head.get("nozzle_type"):
            raise HTTPException(status_code=400, detail=f"Head {i + 1} is missing nozzle type")

    result = zone_nozzle_data.save_zone_heads(
        entity_id, body.heads, body.notes,
        body.show_gpm_on_card, body.show_head_count_on_card,
        area_sqft=body.area_sqft, soil_type=body.soil_type
    )

    log_change(get_actor(request), "Zone Details",
               f"Updated head details for {entity_id.split('.', 1)[-1].replace('_', ' ').title()} ({len(body.heads)} head(s))",
               {"entity_id": entity_id, "head_count": len(body.heads)})

    return {"success": True, **result}


@router.delete("/zone_heads/{entity_id:path}", summary="Delete zone head details")
async def homeowner_delete_zone_heads(entity_id: str, request: Request):
    """Remove all head/nozzle details for a specific zone."""
    _require_homeowner_mode()
    import zone_nozzle_data
    deleted = zone_nozzle_data.delete_zone_heads(entity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No head data for zone '{entity_id}'")

    log_change(get_actor(request), "Zone Details",
               f"Cleared head details for {entity_id.split('.', 1)[-1].replace('_', ' ').title()}",
               {"entity_id": entity_id})

    return {"success": True, "message": f"Head details removed for {entity_id}"}


# --- Pump Settings ---


class SavePumpSettingsRequest(BaseModel):
    pump_entity_id: str = ""
    pump_type: str = ""
    voltage: float = 240
    hp: float = 0
    kw: float = 0
    brand: str = ""
    model: str = ""
    year_installed: str = ""
    cost_per_kwh: float = 0.12
    peak_rate_per_kwh: float = 0.0
    pressure_psi: float = 0.0
    max_gpm: float = 0.0
    max_head_ft: float = 0.0


@router.get("/pump_settings", summary="Get pump settings")
async def homeowner_get_pump_settings():
    """Get the pump configuration (HP/kW, voltage, brand, electricity rates)."""
    _require_homeowner_mode()
    import pump_data
    return pump_data.get_pump_settings()


@router.put("/pump_settings", summary="Save pump settings")
async def homeowner_save_pump_settings(body: SavePumpSettingsRequest, request: Request):
    """Save pump settings. HP and kW are auto-synced (1 HP = 0.7457 kW)."""
    _require_homeowner_mode()
    import pump_data
    old = pump_data.get_pump_settings()
    result = pump_data.save_pump_settings(body.dict())

    # Log changes
    changes = []
    for key in ("pump_type", "voltage", "hp", "kw", "brand", "model", "year_installed", "cost_per_kwh", "peak_rate_per_kwh", "pressure_psi", "max_gpm", "max_head_ft"):
        old_val = old.get(key)
        new_val = result.get(key)
        if str(old_val) != str(new_val):
            changes.append(f"{key}: {old_val} → {new_val}")
    if changes:
        log_change(get_actor(request), "Pump Settings", "; ".join(changes), result)

    return result


@router.get("/pump_stats", summary="Get pump usage statistics")
async def homeowner_get_pump_stats(
    hours: int = Query(720, ge=1, le=8760, description="Hours of history (max 1 year)"),
):
    """Get pump usage statistics (cycles, run hours, kWh, estimated cost)."""
    _require_homeowner_mode()
    import pump_data
    settings = pump_data.get_pump_settings()
    eid = settings.get("pump_entity_id", "")
    if not eid:
        return {
            "pump_entity_id": "",
            "cycles": 0,
            "run_hours": 0,
            "total_seconds": 0,
            "total_kwh": 0,
            "estimated_cost": 0,
            "power_kw": 0,
            "hours": hours,
        }
    return pump_data.get_pump_stats(hours=hours, pump_entity_id=eid, settings=settings)


# --- Water Source Settings ---


class SaveWaterSettingsRequest(BaseModel):
    water_source: str = ""
    cost_per_1000_gal: float = 0.0
    pressure_psi: float = 50.0


@router.get("/water_settings", summary="Get water source settings")
async def homeowner_get_water_settings():
    """Get the water source configuration (city/reclaimed/well, cost per 1,000 gal)."""
    _require_homeowner_mode()
    import water_data
    return water_data.get_water_settings()


@router.put("/water_settings", summary="Save water source settings")
async def homeowner_save_water_settings(body: SaveWaterSettingsRequest, request: Request):
    """Save water source settings. Well water auto-zeros cost."""
    _require_homeowner_mode()
    import water_data
    old = water_data.get_water_settings()
    result = water_data.save_water_settings(body.dict())

    # Log changes
    changes = []
    for key in ("water_source", "cost_per_1000_gal", "pressure_psi"):
        old_val = old.get(key)
        new_val = result.get(key)
        if str(old_val) != str(new_val):
            changes.append(f"{key}: {old_val} \u2192 {new_val}")
    if changes:
        log_change(get_actor(request), "Water Settings", "; ".join(changes), result)

    return result


@router.post("/water_settings/reset_savings", summary="Reset water savings counter")
async def homeowner_reset_water_savings(request: Request):
    """Set a timestamp so the water savings counter only shows events after now.

    Run history is NOT deleted — only the savings display resets.
    """
    _require_data_control(request)
    import water_data
    from datetime import datetime, timezone
    settings = water_data.get_water_settings()
    settings["water_savings_reset_at"] = datetime.now(timezone.utc).isoformat()
    water_data.save_water_settings(settings)
    log_change(get_actor(request), "Water Settings", "Reset water savings counter")
    return {"success": True, "water_savings_reset_at": settings["water_savings_reset_at"]}


# --- Report Settings ---


class SaveReportSettingsRequest(BaseModel):
    company_name: str = ""
    custom_footer: str = ""
    accent_color: str = "#1a7a4c"
    hidden_sections: list = []


@router.get("/report_settings", summary="Get PDF report settings")
async def homeowner_get_report_settings():
    """Get the current PDF report branding/settings."""
    _require_homeowner_mode()
    import report_settings
    return report_settings.get_report_settings()


@router.put("/report_settings", summary="Save PDF report settings")
async def homeowner_save_report_settings(body: SaveReportSettingsRequest, request: Request):
    """Save PDF report branding settings (company name, accent color, sections, footer)."""
    _require_homeowner_mode()
    import report_settings
    old = report_settings.get_report_settings()
    result = report_settings.save_report_settings(body.dict())

    # Log changes
    changes = []
    for key in ("company_name", "custom_footer", "accent_color"):
        old_val = old.get(key, "")
        new_val = result.get(key, "")
        if str(old_val) != str(new_val):
            label = key.replace("_", " ").title()
            changes.append(f"{label}: {old_val or '(empty)'} \u2192 {new_val or '(empty)'}")
    old_hidden = set(old.get("hidden_sections", []))
    new_hidden = set(result.get("hidden_sections", []))
    if old_hidden != new_hidden:
        changes.append(f"Hidden sections: {sorted(new_hidden) if new_hidden else '(none)'}")
    if changes:
        log_change(get_actor(request), "Report Settings", "; ".join(changes))

    return result


@router.post("/report_settings/logo", summary="Upload custom report logo")
async def upload_report_logo(request: Request):
    """Upload a custom logo image for the PDF report cover page (max 2MB)."""
    _require_homeowner_mode()
    import report_settings
    form = await request.form()
    file = form.get("logo")
    if not file:
        raise HTTPException(400, "No logo file provided")
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(400, "Logo file too large (max 2MB)")
    report_settings.save_logo(contents)
    log_change(get_actor(request), "Report Settings", "Custom logo uploaded")
    return {"success": True, "message": "Logo uploaded"}


@router.post("/report_settings/logo_base64", summary="Upload custom report logo (base64)")
async def upload_report_logo_base64(request: Request):
    """Upload a custom logo as base64-encoded JSON (for management proxy compatibility)."""
    _require_homeowner_mode()
    import report_settings
    import base64
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")
    b64_data = body.get("logo_base64", "")
    if not b64_data:
        raise HTTPException(400, "No logo_base64 field provided")
    try:
        contents = base64.b64decode(b64_data)
    except Exception:
        raise HTTPException(400, "Invalid base64 data")
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(400, "Logo file too large (max 2MB)")
    report_settings.save_logo(contents)
    log_change(get_actor(request), "Report Settings", "Custom logo uploaded")
    return {"success": True, "message": "Logo uploaded"}


@router.delete("/report_settings/logo", summary="Remove custom report logo")
async def delete_report_logo(request: Request):
    """Remove the custom logo, reverting to default Flux Open Home logo."""
    _require_homeowner_mode()
    import report_settings
    report_settings.delete_logo()
    log_change(get_actor(request), "Report Settings", "Custom logo removed")
    return {"success": True, "message": "Logo removed"}


@router.get("/report_settings/logo", summary="Get custom report logo")
async def get_report_logo():
    """Serve the custom logo image, or 404 if none uploaded."""
    _require_homeowner_mode()
    import report_settings
    path = report_settings.get_logo_path()
    if not path:
        raise HTTPException(404, "No custom logo")
    return FileResponse(path, media_type="image/png")


@router.get("/assets/gophr-logo", summary="Serve Gophr logo SVG")
async def homeowner_gophr_logo():
    """Serve the Gophr logo SVG for inline display."""
    import os
    # In Docker, gophr.svg is at /app/gophr.svg (same dir as the app package).
    # Locally it's one level up from app/.
    app_dir = os.path.dirname(os.path.dirname(__file__))  # app/
    svg_path = os.path.join(app_dir, "gophr.svg")
    if not os.path.exists(svg_path):
        svg_path = os.path.join(app_dir, "..", "gophr.svg")
    svg_path = os.path.abspath(svg_path)
    if not os.path.exists(svg_path):
        raise HTTPException(404, "Logo not found")
    return FileResponse(svg_path, media_type="image/svg+xml",
                        headers={"Cache-Control": "public, max-age=86400"})


# --- Notification Preferences ---


@router.get("/notification-preferences", summary="Get notification preferences")
async def get_notification_preferences():
    """Get homeowner notification preferences."""
    import homeowner_notification_store as hns
    return hns.get_preferences()


@router.put("/notification-preferences", summary="Update notification preferences")
async def update_notification_preferences(body: UpdateNotificationPrefsRequest, request: Request):
    """Update homeowner notification preferences (partial merge)."""
    import homeowner_notification_store as hns
    updated = hns.update_preferences(body.dict(exclude_none=True))
    log_change(get_actor(request), "Notification Preferences", "Updated notification preferences")
    return updated


# --- Notifications ---


@router.get("/notifications", summary="Get recent notifications")
async def get_notifications(limit: int = Query(50, ge=1, le=200)):
    """Get recent notification events with unread count."""
    import homeowner_notification_store as hns
    events = hns.get_events(limit=limit)
    unread_count = hns.get_unread_count()
    return {"events": events, "unread_count": unread_count}


@router.put("/notifications/{event_id}/read", summary="Mark notification as read")
async def mark_notification_read(event_id: str):
    """Mark a single notification event as read."""
    import homeowner_notification_store as hns
    if not hns.mark_read(event_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.put("/notifications/read-all", summary="Mark all notifications as read")
async def mark_all_notifications_read():
    """Mark all notification events as read."""
    import homeowner_notification_store as hns
    count = hns.mark_all_read()
    return {"success": True, "marked": count}


@router.delete("/notifications/clear", summary="Clear all notifications")
async def clear_all_notifications():
    """Remove all notification events."""
    import homeowner_notification_store as hns
    count = hns.clear_all()
    return {"success": True, "cleared": count}


@router.post("/notifications/record", summary="Record a notification event")
async def record_notification(body: RecordNotificationRequest):
    """Record a notification event (called by management proxy).

    The store checks preferences internally — if the homeowner has
    disabled this category, the event is silently dropped.

    Also sends an HA push notification if configured.
    """
    import homeowner_notification_store as hns
    event = hns.record_event(body.event_type, body.title, body.message)
    print(f"[RECORD_NOTIF] event_type={body.event_type}, title={body.title}, recorded={event is not None}")

    # Also send HA push notification if configured
    try:
        import homeowner_notification_config as hnc
        should = hnc.should_notify(body.event_type)
        print(f"[RECORD_NOTIF] should_notify({body.event_type}) = {should}")
        if should:
            config = hnc.load_config()
            service_name = config["ha_notify_service"]
            print(f"[RECORD_NOTIF] Sending HA notification via notify.{service_name}")
            result = await ha_client.call_service("notify", service_name, {
                "message": body.message or body.title,
                "title": "Flux: " + body.title,
            })
            print(f"[RECORD_NOTIF] HA notification result: {result}")
    except Exception as exc:
        print(f"[RECORD_NOTIF] HA notification EXCEPTION: {exc}")

    return {"recorded": event is not None, "event": event}


# --- HA Notification Settings ---


@router.get("/ha-notification-settings", summary="Get homeowner HA notification settings")
async def get_ha_notification_settings():
    """Get the current HA push notification configuration."""
    import homeowner_notification_config as hnc
    return hnc.get_settings()


@router.put("/ha-notification-settings", summary="Update homeowner HA notification settings")
async def update_ha_notification_settings(body: UpdateHANotificationSettingsRequest, request: Request):
    """Update the HA push notification configuration."""
    import homeowner_notification_config as hnc
    result = hnc.update_settings(
        enabled=body.enabled,
        ha_notify_service=body.ha_notify_service,
        notify_service_appointments=body.notify_service_appointments,
        notify_system_changes=body.notify_system_changes,
        notify_weather_changes=body.notify_weather_changes,
        notify_moisture_changes=body.notify_moisture_changes,
        notify_equipment_changes=body.notify_equipment_changes,
        notify_duration_changes=body.notify_duration_changes,
        notify_report_changes=body.notify_report_changes,
    )
    log_change(get_actor(request), "HA Notification Settings", "Updated HA notification settings")
    return result


@router.get("/ha-notification-settings/services", summary="Discover available HA notify services")
async def discover_homeowner_notify_services():
    """Query Home Assistant for all available notify.* services."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ha_client.HA_BASE_URL}/services",
            headers=ha_client._get_headers(),
            timeout=10.0,
        )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to query HA services")

    services = []
    for domain_entry in response.json():
        if domain_entry.get("domain") == "notify":
            for svc_name, svc_info in domain_entry.get("services", {}).items():
                if svc_name == "send_message":
                    continue
                label = svc_info.get("name") or svc_name.replace("_", " ").title()
                services.append({"id": svc_name, "name": label})
            break

    return {"services": services}


@router.post("/ha-notification-settings/test", summary="Send a test HA notification")
async def test_homeowner_ha_notification():
    """Send a test notification through the configured HA notify service."""
    import homeowner_notification_config as hnc
    settings = hnc.get_settings()
    if not settings.get("ha_notify_service"):
        raise HTTPException(status_code=400, detail="No HA notify service configured")

    service_name = settings["ha_notify_service"]
    success = await ha_client.call_service("notify", service_name, {
        "message": "🧪 Test notification from Flux Open Home — HA notifications are working!",
        "title": "Flux Open Home Test",
    })
    if not success:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to call notify.{service_name} — check that the service exists in Home Assistant",
        )
    return {"success": True, "message": f"Test notification sent via notify.{service_name}"}
