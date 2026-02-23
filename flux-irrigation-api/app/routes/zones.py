"""
Zone management endpoints.
List zones, start/stop individual zones, get zone status.
"""

import asyncio
import re
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
from auth import require_permission, ApiKeyConfig
from config import get_config
import ha_client
import audit_log
import run_log
from config_changelog import log_change, get_actor
from routes.homeowner import is_zone_not_used


_ZONE_NUMBER_RE = re.compile(r'zone[_]?(\d+)', re.IGNORECASE)


def _extract_zone_number(entity_id: str) -> int:
    """Extract the numeric zone number from an entity_id (e.g., 'switch.xxx_zone_3' → 3)."""
    m = _ZONE_NUMBER_RE.search(entity_id)
    return int(m.group(1)) if m else 0

# Track active timed-run tasks so they can be cancelled on manual stop
_timed_run_tasks: dict[str, asyncio.Task] = {}


async def _timed_shutoff(entity_id: str, duration_minutes: int):
    """Background task: wait for duration then turn off the zone."""
    try:
        await asyncio.sleep(duration_minutes * 60)
        # Turn off the zone after the timer expires
        svc_domain, svc_name = _get_zone_service(entity_id, "off")
        await ha_client.call_service(svc_domain, svc_name, {"entity_id": entity_id})
        run_log.log_zone_event(
            entity_id=entity_id, state="off", source="timed_shutoff",
            zone_name=_zone_name(entity_id),
            duration_seconds=duration_minutes * 60,
        )
        print(f"[ZONES] Timed run complete: {entity_id} turned off after {duration_minutes} min")
    except asyncio.CancelledError:
        print(f"[ZONES] Timed run cancelled for {entity_id}")
    finally:
        _timed_run_tasks.pop(entity_id, None)


router = APIRouter(prefix="/zones", tags=["Zones"])


class ZoneStatus(BaseModel):
    entity_id: str
    name: str
    state: str  # "on" or "off"
    friendly_name: Optional[str] = None
    last_changed: Optional[str] = None
    attributes: dict = {}


class ZoneStartRequest(BaseModel):
    duration_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        le=480,
        description="Duration in minutes (1-480). If omitted, runs until manually stopped.",
    )


class ZoneActionResponse(BaseModel):
    success: bool
    zone_id: str
    action: str
    message: str
    warning: str = ""


def _zone_name(entity_id: str) -> str:
    """Derive zone name from entity_id by stripping the domain prefix."""
    if "." in entity_id:
        return entity_id.split(".", 1)[1]
    return entity_id


def _resolve_zone_entity(zone_id: str, config) -> str:
    """Resolve a zone_id to a full entity_id, validating it's allowed.

    Tries multiple resolution strategies:
    1. Direct match (zone_id is already a full entity_id)
    2. Prefix match (switch.{zone_id} or valve.{zone_id})
    3. Zone number match (zone_id is "2" → find entity with zone_2 in name)
    """
    # Check if zone_id is already a full entity_id
    if zone_id in config.allowed_zone_entities:
        return zone_id

    # Try common zone domains
    for domain in ("switch", "valve"):
        entity_id = f"{domain}.{zone_id}"
        if entity_id in config.allowed_zone_entities:
            return entity_id

    # Try matching by zone number (e.g., zone_id="2" matches "switch.xxx_zone_2")
    try:
        target_num = int(zone_id)
        for entity_id in config.allowed_zone_entities:
            if _extract_zone_number(entity_id) == target_num:
                return entity_id
    except (ValueError, TypeError):
        pass

    raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")


def _get_zone_service(entity_id: str, action: str) -> tuple[str, str]:
    """Get the correct HA service domain and service name for a zone entity.

    Args:
        entity_id: The full entity_id (e.g., switch.zone_1 or valve.zone_1)
        action: Either "on" or "off"

    Returns:
        Tuple of (service_domain, service_name)
    """
    domain = entity_id.split(".")[0] if "." in entity_id else "switch"

    if domain == "valve":
        return ("valve", "open" if action == "on" else "close")
    else:
        return ("switch", "turn_on" if action == "on" else "turn_off")


@router.get(
    "",
    response_model=list[ZoneStatus],
    dependencies=[Depends(require_permission("zones.read"))],
    summary="List all irrigation zones",
)
async def list_zones(request: Request):
    """Get the current status of all irrigation zones."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    entities = await ha_client.get_entities_by_ids(config.allowed_zone_entities)

    # Filter by expansion board zone count
    max_zones = config.detected_zone_count  # 0 = no limit (no expansion board)
    if max_zones > 0:
        entities = [e for e in entities if _extract_zone_number(e.get("entity_id", "")) <= max_zones]

    # NOTE: Pump/master valve zones are NOT filtered out here — the UI
    # renders them with special icons and sorts them to the end.  They are
    # only excluded from the *zone count* in the system status endpoint.

    # Exclude "not used" zones
    entities = [e for e in entities if not is_zone_not_used(e.get("entity_id", ""))]

    zones = []
    for entity in entities:
        attrs = entity.get("attributes", {})
        zones.append(
            ZoneStatus(
                entity_id=entity["entity_id"],
                name=_zone_name(entity["entity_id"]),
                state=entity.get("state", "unknown"),
                friendly_name=attrs.get("friendly_name"),
                last_changed=entity.get("last_changed"),
                attributes=attrs,
            )
        )

    audit_log.log_action(
        api_key_name=key_config.name,
        method="GET",
        path="/api/zones",
        action="list_zones",
        details={"zone_count": len(zones)},
        client_ip=request.client.host if request.client else None,
    )

    return zones


@router.get(
    "/{zone_id}",
    response_model=ZoneStatus,
    dependencies=[Depends(require_permission("zones.read"))],
    summary="Get a single zone's status",
)
async def get_zone(zone_id: str, request: Request):
    """Get the current status of a specific irrigation zone."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    entity_id = _resolve_zone_entity(zone_id, config)
    entity = await ha_client.get_entity_state(entity_id)

    if entity is None:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")

    attrs = entity.get("attributes", {})

    audit_log.log_action(
        api_key_name=key_config.name,
        method="GET",
        path=f"/api/zones/{zone_id}",
        action="get_zone",
        details={"entity_id": entity_id},
        client_ip=request.client.host if request.client else None,
    )

    return ZoneStatus(
        entity_id=entity["entity_id"],
        name=zone_id,
        state=entity.get("state", "unknown"),
        friendly_name=attrs.get("friendly_name"),
        last_changed=entity.get("last_changed"),
        attributes=attrs,
    )


@router.post(
    "/{zone_id}/start",
    response_model=ZoneActionResponse,
    dependencies=[Depends(require_permission("zones.control"))],
    summary="Start an irrigation zone",
)
async def start_zone(zone_id: str, body: ZoneStartRequest, request: Request):
    """Turn on a specific irrigation zone, optionally for a set duration."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    entity_id = _resolve_zone_entity(zone_id, config)

    # Check schedule state for informational warning (never blocks manual starts)
    schedule_warning = ""
    from routes.schedule import _load_schedules
    schedule_data = _load_schedules()
    if schedule_data.get("weather_schedule_disabled"):
        reason = schedule_data.get("weather_disable_reason", "weather conditions")
        schedule_warning = f"Schedule disabled due to {reason}"
    elif schedule_data.get("system_paused"):
        schedule_warning = "System is paused"

    # Verify zone exists in HA
    entity = await ha_client.get_entity_state(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")

    # Pre-announce the source so the WebSocket watcher knows this is an API
    # start even if the log entry hasn't been written yet (race condition fix).
    run_log.pre_announce_zone_source(entity_id, "api")

    # Turn on the zone (supports both switch and valve entities)
    svc_domain, svc_name = _get_zone_service(entity_id, "on")
    service_data = {"entity_id": entity_id}
    success = await ha_client.call_service(svc_domain, svc_name, service_data)

    if not success:
        raise HTTPException(status_code=502, detail="Failed to communicate with Home Assistant.")

    run_log.log_zone_event(
        entity_id=entity_id, state="on", source="api",
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
                    print(f"[ZONES] Duration adjusted: {body.duration_minutes} → {adjusted_duration} min "
                          f"(weather={mult_result['weather_multiplier']}, "
                          f"moisture={mult_result['moisture_multiplier']})")
        except Exception as e:
            print(f"[ZONES] Multiplier lookup failed, using original duration: {e}")

    # Build warning for moisture skip (zone keeps running — user chose manual start)
    moisture_warning = ""
    if moisture_skip:
        try:
            moisture_warning = mult_result.get("moisture_reason", "Soil moisture above skip threshold")
        except Exception:
            moisture_warning = "Soil moisture above skip threshold"
        print(f"[ZONES] Manual start with moisture warning: {entity_id} — {moisture_warning}")

    if adjusted_duration:
        # Cancel any existing timed run for this entity
        existing = _timed_run_tasks.pop(entity_id, None)
        if existing and not existing.done():
            existing.cancel()
        # Schedule the new timed shutoff
        task = asyncio.create_task(
            _timed_shutoff(entity_id, adjusted_duration)
        )
        _timed_run_tasks[entity_id] = task
        print(f"[ZONES] Timed run started: {entity_id} for {adjusted_duration} min")

    message = f"Zone '{zone_id}' started"
    if body.duration_minutes:
        if adjusted_duration != body.duration_minutes:
            message += f" for {adjusted_duration} minutes (adjusted from {body.duration_minutes})"
        else:
            message += f" for {adjusted_duration} minutes"

    # Log configuration change
    actor = get_actor(request)
    desc = f"Started {_zone_name(entity_id).replace('_', ' ').title()}"
    if body.duration_minutes:
        desc += f" for {body.duration_minutes} min"
    log_change(actor, "Zone Control", desc, {"entity_id": entity_id})

    audit_log.log_action(
        api_key_name=key_config.name,
        method="POST",
        path=f"/api/zones/{zone_id}/start",
        action="start_zone",
        details={
            "entity_id": entity_id,
            "duration_minutes": body.duration_minutes,
        },
        client_ip=request.client.host if request.client else None,
    )

    # Combine warnings
    warnings = [w for w in (schedule_warning, moisture_warning) if w]
    combined_warning = " | ".join(warnings) if warnings else ""

    return ZoneActionResponse(
        success=True,
        zone_id=zone_id,
        action="start",
        message=message,
        warning=combined_warning,
    )


@router.post(
    "/{zone_id}/stop",
    response_model=ZoneActionResponse,
    dependencies=[Depends(require_permission("zones.control"))],
    summary="Stop an irrigation zone",
)
async def stop_zone(zone_id: str, request: Request):
    """Turn off a specific irrigation zone."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    entity_id = _resolve_zone_entity(zone_id, config)

    # Verify zone exists in HA
    entity = await ha_client.get_entity_state(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")

    # Cancel any active timed run for this zone
    existing = _timed_run_tasks.pop(entity_id, None)
    if existing and not existing.done():
        existing.cancel()

    svc_domain, svc_name = _get_zone_service(entity_id, "off")
    service_data = {"entity_id": entity_id}
    success = await ha_client.call_service(svc_domain, svc_name, service_data)

    if not success:
        raise HTTPException(status_code=502, detail="Failed to communicate with Home Assistant.")

    run_log.log_zone_event(
        entity_id=entity_id, state="off", source="api",
        zone_name=_zone_name(entity_id),
    )

    # Signal the remote that a manual stop occurred
    await run_log.signal_manual_stop()

    log_change(get_actor(request), "Zone Control",
               f"Stopped {_zone_name(entity_id).replace('_', ' ').title()}",
               {"entity_id": entity_id})

    audit_log.log_action(
        api_key_name=key_config.name,
        method="POST",
        path=f"/api/zones/{zone_id}/stop",
        action="stop_zone",
        details={"entity_id": entity_id},
        client_ip=request.client.host if request.client else None,
    )

    return ZoneActionResponse(
        success=True,
        zone_id=zone_id,
        action="stop",
        message=f"Zone '{zone_id}' stopped",
    )


@router.post(
    "/stop_all",
    response_model=ZoneActionResponse,
    dependencies=[Depends(require_permission("zones.control"))],
    summary="Stop all irrigation zones",
)
async def stop_all_zones(request: Request):
    """Emergency stop - turn off all irrigation zones."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    # Cancel all active timed runs
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
            await ha_client.call_service(
                svc_domain, svc_name, {"entity_id": entity_id}
            )
            run_log.log_zone_event(
                entity_id=entity_id, state="off", source="stop_all",
                zone_name=_zone_name(entity_id),
            )
            stopped.append(entity_id)

    # Signal the remote that a manual stop occurred
    if stopped:
        await run_log.signal_manual_stop()

    log_change(get_actor(request), "Zone Control", "Emergency stop — all zones",
               {"stopped": len(stopped)})

    audit_log.log_action(
        api_key_name=key_config.name,
        method="POST",
        path="/api/zones/stop_all",
        action="stop_all_zones",
        details={"stopped_zones": stopped},
        client_ip=request.client.host if request.client else None,
    )

    return ZoneActionResponse(
        success=True,
        zone_id="all",
        action="stop_all",
        message=f"Stopped {len(stopped)} active zone(s)",
    )
