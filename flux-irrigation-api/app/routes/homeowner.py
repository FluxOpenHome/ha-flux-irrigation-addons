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
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query, Request
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
    active_zones = [z for z in zones if z.get("state") == "on"]
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
        "total_zones": len(zones),
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

    # If moisture says skip, turn the zone back off and return a skip response
    if moisture_skip:
        svc_domain_off, svc_name_off = _get_zone_service(entity_id, "off")
        await ha_client.call_service(svc_domain_off, svc_name_off, {"entity_id": entity_id})
        run_log.log_zone_event(
            entity_id=entity_id, state="off", source="moisture_skip",
            zone_name=_zone_name(entity_id),
        )
        return {"success": True, "zone_id": zone_id, "action": "skipped",
                "message": f"Zone '{zone_id}' skipped — soil moisture above threshold"}

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

    return {"success": True, "zone_id": zone_id, "action": "start", "message": message}


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
async def homeowner_set_entity(entity_id: str, body: EntitySetRequest, request: Request):
    """Set the value of a device control entity."""
    _require_homeowner_mode()
    config = get_config()

    if entity_id not in config.allowed_control_entities:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")

    domain = entity_id.split(".")[0] if "." in entity_id else ""

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
    data.pop("weather_paused", None)
    data.pop("weather_pause_reason", None)
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
                headers={"User-Agent": "FluxIrrigationAPI/1.1.8"},
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
    if not config.weather_enabled or not config.weather_entity_id:
        return {"weather_enabled": False, "weather": {"error": "Not configured"}}

    from routes.weather import get_weather_data, _load_weather_rules
    weather = await get_weather_data()
    rules_data = _load_weather_rules()
    return {
        "weather_enabled": True,
        "weather": weather,
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
    limit: int = Query(200, ge=1, le=1000),
    hours: int = Query(0, ge=0, le=8760),
):
    """Get the weather event log for the homeowner dashboard."""
    from routes.weather import get_weather_log
    return {"events": get_weather_log(limit=limit, hours=hours)}


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
async def homeowner_clear_weather_log():
    """Clear the weather event log."""
    from routes.weather import WEATHER_LOG_FILE
    try:
        if os.path.exists(WEATHER_LOG_FILE):
            os.remove(WEATHER_LOG_FILE)
        return {"success": True, "message": "Weather log cleared"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/history/runs", summary="Clear run history")
async def homeowner_clear_history():
    """Clear the local run history log."""
    _require_homeowner_mode()
    success = run_log.clear_run_history()
    if success:
        return {"success": True, "message": "Run history cleared"}
    return {"success": False, "error": "Failed to clear run history"}


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
