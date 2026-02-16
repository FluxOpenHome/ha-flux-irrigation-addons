"""
System control endpoints.
Pause/resume the irrigation system, health checks, and system info.
"""

import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Optional
from auth import require_permission, authenticate, ApiKeyConfig
from config import get_config
import ha_client
import audit_log
from config_changelog import log_change, get_actor
from routes.homeowner import is_zone_not_used

_ZONE_NUMBER_RE = re.compile(r'zone[_]?(\d+)', re.IGNORECASE)


def _extract_zone_number(entity_id: str) -> int:
    m = _ZONE_NUMBER_RE.search(entity_id)
    return int(m.group(1)) if m else 0


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
    has_pump_relay: bool = False
    has_master_valve: bool = False
    # Weather multiplier (system-wide); moisture is per-zone, not in status
    weather_multiplier: float = 1.0
    moisture_enabled: bool = False
    # Contact/address info — synced live to management company
    address: str = ""
    city: str = ""
    state: str = ""
    zip: str = ""
    phone: str = ""
    first_name: str = ""
    last_name: str = ""


class PauseResponse(BaseModel):
    success: bool
    system_paused: bool
    message: str


@router.get(
    "/health",
    summary="Health check (no auth required)",
)
async def health_check():
    """Basic health check endpoint. No authentication required.

    Includes a 'revoked' flag so the management company can detect
    that the homeowner explicitly revoked access — no auth needed
    to read this, so it works even after the API key is deleted.
    """
    import json, os
    ha_connected = await ha_client.check_connection()

    # Check if the homeowner has revoked management access
    revoked = False
    try:
        options_path = "/data/options.json"
        if os.path.exists(options_path):
            with open(options_path, "r") as f:
                options = json.load(f)
            revoked = options.get("connection_revoked", False)
    except Exception:
        pass

    return {
        "status": "healthy" if ha_connected else "degraded",
        "ha_connected": ha_connected,
        "revoked": revoked,
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

    # Count zones and active zones (filter by detected_zone_count for expansion boards)
    zones = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    max_zones = config.detected_zone_count  # 0 = no limit (no expansion board)
    if max_zones > 0:
        zones = [z for z in zones if _extract_zone_number(z.get("entity_id", "")) <= max_zones]
    # Filter out pump start relay and master valve — they are not actual zones
    _NON_ZONE_RE = re.compile(r"pump|master.?valve", re.IGNORECASE)
    zones = [z for z in zones if not _NON_ZONE_RE.search(z.get("entity_id", ""))]

    # Detect pump relay / master valve via zone mode entities
    has_pump_relay = False
    has_master_valve = False
    _ZONE_MODE_RE = re.compile(r"zone_\d+_mode", re.IGNORECASE)
    mode_eids = [e for e in config.allowed_control_entities if _ZONE_MODE_RE.search(e)]
    if mode_eids:
        mode_entities = await ha_client.get_entities_by_ids(mode_eids)
        for me in mode_entities:
            mode_val = (me.get("state") or "").lower()
            if "pump" in mode_val or "relay" in mode_val:
                has_pump_relay = True
                # Also filter this zone out of the count
                zone_num = _extract_zone_number(me.get("entity_id", ""))
                zones = [z for z in zones if _extract_zone_number(z.get("entity_id", "")) != zone_num]
            elif "master" in mode_val and "valve" in mode_val:
                has_master_valve = True
                zone_num = _extract_zone_number(me.get("entity_id", ""))
                zones = [z for z in zones if _extract_zone_number(z.get("entity_id", "")) != zone_num]

    # Exclude "not used" zones from the count
    used_zones = [z for z in zones if not is_zone_not_used(z.get("entity_id", ""))]
    active_zones = [z for z in used_zones if z.get("state") == "on"]

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

    # --- Weather multiplier ---
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

    return SystemStatus(
        online=True,
        ha_connected=ha_connected,
        system_paused=schedule_data.get("system_paused", False),
        total_zones=len(used_zones),
        active_zones=len(active_zones),
        active_zone_entity_id=active_zone_eid,
        active_zone_name=active_zone_name,
        total_sensors=len(sensors),
        rain_delay_active=rain_delay_active,
        rain_delay_until=rain_delay_until if rain_delay_active else None,
        uptime_check=datetime.now(timezone.utc).isoformat(),
        has_pump_relay=has_pump_relay,
        has_master_valve=has_master_valve,
        weather_multiplier=weather_multiplier,
        moisture_enabled=moisture_enabled,
        # Live contact/address info for management company sync
        address=config.homeowner_address or "",
        city=config.homeowner_city or "",
        state=config.homeowner_state or "",
        zip=config.homeowner_zip or "",
        phone=config.homeowner_phone or "",
        first_name=config.homeowner_first_name or "",
        last_name=config.homeowner_last_name or "",
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

    log_change(get_actor(request), "System", "Paused irrigation system")

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

    log_change(get_actor(request), "System", "Resumed irrigation system")

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
