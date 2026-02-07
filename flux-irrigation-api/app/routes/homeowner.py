"""
Flux Open Home - Homeowner Dashboard API
==========================================
Unauthenticated endpoints for the homeowner dashboard UI.
These run behind HA ingress (already authenticated) and only work in homeowner mode.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, Any
from config import get_config
import ha_client


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
        "uptime_check": datetime.now(timezone.utc).isoformat(),
        # Include homeowner address info for map display
        "address": config.homeowner_address or "",
        "city": config.homeowner_city or "",
        "state": config.homeowner_state or "",
        "zip": config.homeowner_zip or "",
    }


@router.get("/zones", summary="List all zones")
async def homeowner_zones():
    """Get status of all irrigation zones."""
    _require_homeowner_mode()
    config = get_config()

    entities = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    zones = []
    for entity in entities:
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
async def homeowner_start_zone(zone_id: str, body: ZoneStartRequest):
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

    # If duration specified, schedule automatic shutoff using zones module
    if body.duration_minutes:
        from routes.zones import _timed_run_tasks, _timed_shutoff
        existing = _timed_run_tasks.pop(entity_id, None)
        if existing and not existing.done():
            existing.cancel()
        task = asyncio.create_task(_timed_shutoff(entity_id, body.duration_minutes))
        _timed_run_tasks[entity_id] = task

    message = f"Zone '{zone_id}' started"
    if body.duration_minutes:
        message += f" for {body.duration_minutes} minutes"

    return {"success": True, "zone_id": zone_id, "action": "start", "message": message}


@router.post("/zones/{zone_id}/stop", summary="Stop a zone")
async def homeowner_stop_zone(zone_id: str):
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

    return {"success": True, "zone_id": zone_id, "action": "stop", "message": f"Zone '{zone_id}' stopped"}


@router.post("/zones/stop_all", summary="Emergency stop all zones")
async def homeowner_stop_all():
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
            stopped.append(entity_id)

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
async def homeowner_set_entity(entity_id: str, body: EntitySetRequest):
    """Set the value of a device control entity."""
    _require_homeowner_mode()
    config = get_config()

    if entity_id not in config.allowed_control_entities:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")

    domain = entity_id.split(".")[0] if "." in entity_id else ""

    from routes.entities import _get_set_service
    svc_domain, svc_name, extra_data = _get_set_service(domain, body)
    service_data = {"entity_id": entity_id, **extra_data}

    success = await ha_client.call_service(svc_domain, svc_name, service_data)
    if not success:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to call {svc_domain}.{svc_name} for {entity_id}.",
        )

    return {
        "success": True,
        "entity_id": entity_id,
        "action": f"{svc_domain}.{svc_name}",
        "message": f"Called {svc_domain}.{svc_name} on {entity_id}",
    }


@router.post("/system/pause", summary="Pause irrigation system")
async def homeowner_pause():
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

    from routes.schedule import _load_schedules, _save_schedules
    data = _load_schedules()
    data["system_paused"] = True
    _save_schedules(data)

    await ha_client.fire_event(
        "flux_irrigation_system_paused",
        {"source": "homeowner_dashboard"},
    )

    return {"success": True, "system_paused": True, "message": "Irrigation system paused."}


@router.post("/system/resume", summary="Resume irrigation system")
async def homeowner_resume():
    """Resume the irrigation system after a pause."""
    _require_homeowner_mode()

    from routes.schedule import _load_schedules, _save_schedules
    data = _load_schedules()
    data["system_paused"] = False
    _save_schedules(data)

    await ha_client.fire_event(
        "flux_irrigation_system_resumed",
        {"source": "homeowner_dashboard"},
    )

    return {"success": True, "system_paused": False, "message": "Irrigation system resumed."}


@router.get("/history/runs", summary="Get run history")
async def homeowner_history(
    hours: int = Query(24, ge=1, le=720, description="Hours of history"),
):
    """Get irrigation run history for all zones."""
    _require_homeowner_mode()
    config = get_config()

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    events = []
    zone_entities = await ha_client.get_entities_by_ids(config.allowed_zone_entities)

    for entity in zone_entities:
        entity_id = entity["entity_id"]
        zone_name_str = _zone_name(entity_id)

        history = await ha_client.get_history(
            entity_id=entity_id,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
        )

        if history and len(history) > 0:
            prev_event = None
            for entry in history[0]:
                event = {
                    "entity_id": entity_id,
                    "zone_name": zone_name_str,
                    "state": entry.get("state", "unknown"),
                    "timestamp": entry.get("last_changed", ""),
                    "duration_seconds": None,
                }

                if prev_event and prev_event["state"] == "on" and event["state"] == "off":
                    try:
                        on_time = datetime.fromisoformat(prev_event["timestamp"])
                        off_time = datetime.fromisoformat(event["timestamp"])
                        event["duration_seconds"] = (off_time - on_time).total_seconds()
                    except ValueError:
                        pass

                events.append(event)
                prev_event = event

    events.sort(key=lambda e: e["timestamp"], reverse=True)

    return {
        "period_start": start_time.isoformat(),
        "period_end": end_time.isoformat(),
        "events": events,
        "total_run_events": len([e for e in events if e["state"] == "on"]),
    }


@router.get("/zone_aliases", summary="Get zone aliases")
async def homeowner_get_aliases():
    """Get the homeowner's zone display name aliases."""
    _require_homeowner_mode()
    return _load_aliases()


@router.put("/zone_aliases", summary="Update zone aliases")
async def homeowner_update_aliases(body: UpdateAliasesRequest):
    """Update the homeowner's zone display name aliases."""
    _require_homeowner_mode()
    _save_aliases(body.zone_aliases)
    return {"success": True, "zone_aliases": body.zone_aliases}
