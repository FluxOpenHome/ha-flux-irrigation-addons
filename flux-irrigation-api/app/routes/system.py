"""
System control endpoints.
Pause/resume the irrigation system, health checks, and system info.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Optional
from auth import require_permission, authenticate, ApiKeyConfig
from config import get_config
import ha_client
import audit_log


router = APIRouter(prefix="/system", tags=["System"])


class SystemStatus(BaseModel):
    online: bool
    ha_connected: bool
    system_paused: bool
    total_zones: int
    active_zones: int
    active_zone_entity_id: Optional[str] = None
    active_zone_name: Optional[str] = None
    total_sensors: int
    rain_delay_active: bool
    rain_delay_until: Optional[str] = None
    api_version: str = "1.0.0"
    uptime_check: str


class PauseResponse(BaseModel):
    success: bool
    system_paused: bool
    message: str


@router.get(
    "/health",
    summary="Health check (no auth required)",
)
async def health_check():
    """Basic health check endpoint. No authentication required."""
    ha_connected = await ha_client.check_connection()
    return {
        "status": "healthy" if ha_connected else "degraded",
        "ha_connected": ha_connected,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/status",
    response_model=SystemStatus,
    dependencies=[Depends(require_permission("zones.read"))],
    summary="Get full system status",
)
async def get_system_status(request: Request):
    """Get a comprehensive status overview of the irrigation system."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    ha_connected = await ha_client.check_connection()

    # Count zones and active zones
    zones = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    active_zones = [z for z in zones if z.get("state") == "on"]

    # Count sensors
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

    audit_log.log_action(
        api_key_name=key_config.name,
        method="GET",
        path="/api/system/status",
        action="get_system_status",
        client_ip=request.client.host if request.client else None,
    )

    # Get the first active zone's info (only one can run at a time)
    active_zone_eid = None
    active_zone_name = None
    if active_zones:
        az = active_zones[0]
        active_zone_eid = az.get("entity_id")
        attrs = az.get("attributes", {})
        active_zone_name = attrs.get("friendly_name") or active_zone_eid

    return SystemStatus(
        online=True,
        ha_connected=ha_connected,
        system_paused=schedule_data.get("system_paused", False),
        total_zones=len(zones),
        active_zones=len(active_zones),
        active_zone_entity_id=active_zone_eid,
        active_zone_name=active_zone_name,
        total_sensors=len(sensors),
        rain_delay_active=rain_delay_active,
        rain_delay_until=rain_delay_until if rain_delay_active else None,
        uptime_check=datetime.now(timezone.utc).isoformat(),
    )


@router.post(
    "/pause",
    response_model=PauseResponse,
    dependencies=[Depends(require_permission("system.control"))],
    summary="Pause the irrigation system",
)
async def pause_system(request: Request):
    """Pause all irrigation. Active zones will be stopped and schedules suspended."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    # Stop all active zones (supports both switch and valve entities)
    import run_log
    zones = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    for zone in zones:
        state = zone.get("state", "")
        if state in ("on", "open"):
            entity_id = zone["entity_id"]
            domain = entity_id.split(".")[0] if "." in entity_id else "switch"
            if domain == "valve":
                await ha_client.call_service("valve", "close", {"entity_id": entity_id})
            else:
                await ha_client.call_service("switch", "turn_off", {"entity_id": entity_id})
            attrs = zone.get("attributes", {})
            run_log.log_zone_event(
                entity_id=entity_id, state="off", source="system_pause",
                zone_name=attrs.get("friendly_name", entity_id),
            )

    # Disable ESPHome schedule programs so the controller can't start runs
    import schedule_control
    saved_states = await schedule_control.disable_schedules()

    # Update schedule state
    from routes.schedule import _load_schedules, _save_schedules
    data = _load_schedules()
    data["system_paused"] = True
    if saved_states:
        data["saved_schedule_states"] = saved_states
    _save_schedules(data)

    await ha_client.fire_event(
        "flux_irrigation_system_paused",
        {"source": f"api:{key_config.name}"},
    )

    audit_log.log_action(
        api_key_name=key_config.name,
        method="POST",
        path="/api/system/pause",
        action="pause_system",
        client_ip=request.client.host if request.client else None,
    )

    return PauseResponse(
        success=True,
        system_paused=True,
        message="Irrigation system paused. All active zones stopped.",
    )


@router.post(
    "/resume",
    response_model=PauseResponse,
    dependencies=[Depends(require_permission("system.control"))],
    summary="Resume the irrigation system",
)
async def resume_system(request: Request):
    """Resume the irrigation system after a pause."""
    key_config: ApiKeyConfig = request.state.api_key_config

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
        {"source": f"api:{key_config.name}"},
    )

    audit_log.log_action(
        api_key_name=key_config.name,
        method="POST",
        path="/api/system/resume",
        action="resume_system",
        client_ip=request.client.host if request.client else None,
    )

    return PauseResponse(
        success=True,
        system_paused=False,
        message="Irrigation system resumed.",
    )
