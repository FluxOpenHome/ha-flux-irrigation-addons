"""
Schedule management endpoints.
Read and update irrigation schedules stored as HA input helpers or via events.
"""

import json
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
from auth import require_permission, ApiKeyConfig
from config import get_config
import ha_client
import audit_log


router = APIRouter(prefix="/schedule", tags=["Schedule"])

# Local schedule storage (persisted in add-on data)
SCHEDULE_FILE = "/data/schedules.json"


class ZoneScheduleEntry(BaseModel):
    zone_id: str
    duration_minutes: int = Field(ge=1, le=480)


class ScheduleProgram(BaseModel):
    program_id: str
    name: str
    enabled: bool = True
    days: list[str] = Field(
        description="Days of the week: mon, tue, wed, thu, fri, sat, sun"
    )
    start_time: str = Field(
        description="Start time in HH:MM format (24-hour)",
        pattern=r"^\d{2}:\d{2}$",
    )
    zones: list[ZoneScheduleEntry]
    rain_delay_skip: bool = Field(
        default=True,
        description="Skip this program if rain sensor is active",
    )


class ScheduleResponse(BaseModel):
    programs: list[ScheduleProgram]
    system_paused: bool = False
    rain_delay_active: bool = False
    rain_delay_until: Optional[str] = None


class RainDelayRequest(BaseModel):
    hours: int = Field(ge=1, le=168, description="Rain delay duration in hours (1-168)")


def _load_schedules() -> dict:
    """Load schedules from persistent storage."""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"programs": [], "system_paused": False, "rain_delay_until": None}


def _save_schedules(data: dict):
    """Save schedules to persistent storage."""
    os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=2)


@router.get(
    "",
    response_model=ScheduleResponse,
    dependencies=[Depends(require_permission("schedule.read"))],
    summary="Get the current irrigation schedule",
)
async def get_schedule(request: Request):
    """Get all irrigation schedule programs and system status."""
    key_config: ApiKeyConfig = request.state.api_key_config
    data = _load_schedules()

    programs = [ScheduleProgram(**p) for p in data.get("programs", [])]

    # Check rain delay status
    rain_delay_until = data.get("rain_delay_until")
    rain_delay_active = False
    if rain_delay_until:
        from datetime import datetime, timezone
        try:
            delay_end = datetime.fromisoformat(rain_delay_until)
            rain_delay_active = datetime.now(timezone.utc) < delay_end
        except ValueError:
            rain_delay_active = False

    audit_log.log_action(
        api_key_name=key_config.name,
        method="GET",
        path="/api/schedule",
        action="get_schedule",
        details={"program_count": len(programs)},
        client_ip=request.client.host if request.client else None,
    )

    return ScheduleResponse(
        programs=programs,
        system_paused=data.get("system_paused", False),
        rain_delay_active=rain_delay_active,
        rain_delay_until=rain_delay_until if rain_delay_active else None,
    )


@router.put(
    "",
    response_model=ScheduleResponse,
    dependencies=[Depends(require_permission("schedule.write"))],
    summary="Update the irrigation schedule",
)
async def update_schedule(programs: list[ScheduleProgram], request: Request):
    """Replace all irrigation schedule programs."""
    key_config: ApiKeyConfig = request.state.api_key_config

    # Validate day names
    valid_days = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
    for program in programs:
        invalid_days = set(program.days) - valid_days
        if invalid_days:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid days in program '{program.name}': {invalid_days}",
            )

    # Load existing data to preserve system state
    data = _load_schedules()
    data["programs"] = [p.model_dump() for p in programs]
    _save_schedules(data)

    # Fire an event so the homeowner's HA automations can react
    await ha_client.fire_event(
        "flux_irrigation_schedule_updated",
        {
            "source": f"api:{key_config.name}",
            "program_count": len(programs),
            "programs": [p.model_dump() for p in programs],
        },
    )

    audit_log.log_action(
        api_key_name=key_config.name,
        method="PUT",
        path="/api/schedule",
        action="update_schedule",
        details={
            "program_count": len(programs),
            "program_names": [p.name for p in programs],
        },
        client_ip=request.client.host if request.client else None,
    )

    return await get_schedule(request)


@router.post(
    "/program",
    response_model=ScheduleResponse,
    dependencies=[Depends(require_permission("schedule.write"))],
    summary="Add a schedule program",
)
async def add_program(program: ScheduleProgram, request: Request):
    """Add a new irrigation schedule program."""
    key_config: ApiKeyConfig = request.state.api_key_config
    data = _load_schedules()

    # Check for duplicate program_id
    existing_ids = [p["program_id"] for p in data.get("programs", [])]
    if program.program_id in existing_ids:
        raise HTTPException(
            status_code=409,
            detail=f"Program with ID '{program.program_id}' already exists.",
        )

    data["programs"].append(program.model_dump())
    _save_schedules(data)

    await ha_client.fire_event(
        "flux_irrigation_schedule_updated",
        {
            "source": f"api:{key_config.name}",
            "action": "add_program",
            "program": program.model_dump(),
        },
    )

    audit_log.log_action(
        api_key_name=key_config.name,
        method="POST",
        path="/api/schedule/program",
        action="add_program",
        details={"program_id": program.program_id, "program_name": program.name},
        client_ip=request.client.host if request.client else None,
    )

    return await get_schedule(request)


@router.delete(
    "/program/{program_id}",
    response_model=ScheduleResponse,
    dependencies=[Depends(require_permission("schedule.write"))],
    summary="Delete a schedule program",
)
async def delete_program(program_id: str, request: Request):
    """Remove an irrigation schedule program."""
    key_config: ApiKeyConfig = request.state.api_key_config
    data = _load_schedules()

    original_count = len(data.get("programs", []))
    data["programs"] = [
        p for p in data.get("programs", []) if p["program_id"] != program_id
    ]

    if len(data["programs"]) == original_count:
        raise HTTPException(
            status_code=404,
            detail=f"Program '{program_id}' not found.",
        )

    _save_schedules(data)

    await ha_client.fire_event(
        "flux_irrigation_schedule_updated",
        {
            "source": f"api:{key_config.name}",
            "action": "delete_program",
            "program_id": program_id,
        },
    )

    audit_log.log_action(
        api_key_name=key_config.name,
        method="DELETE",
        path=f"/api/schedule/program/{program_id}",
        action="delete_program",
        details={"program_id": program_id},
        client_ip=request.client.host if request.client else None,
    )

    return await get_schedule(request)


@router.post(
    "/rain_delay",
    dependencies=[Depends(require_permission("system.control"))],
    summary="Set a rain delay",
)
async def set_rain_delay(body: RainDelayRequest, request: Request):
    """Set a rain delay to pause irrigation for a specified number of hours."""
    from datetime import datetime, timedelta, timezone

    key_config: ApiKeyConfig = request.state.api_key_config
    data = _load_schedules()

    delay_until = datetime.now(timezone.utc) + timedelta(hours=body.hours)
    data["rain_delay_until"] = delay_until.isoformat()
    _save_schedules(data)

    await ha_client.fire_event(
        "flux_irrigation_rain_delay",
        {
            "source": f"api:{key_config.name}",
            "hours": body.hours,
            "until": delay_until.isoformat(),
        },
    )

    audit_log.log_action(
        api_key_name=key_config.name,
        method="POST",
        path="/api/schedule/rain_delay",
        action="set_rain_delay",
        details={"hours": body.hours, "until": delay_until.isoformat()},
        client_ip=request.client.host if request.client else None,
    )

    return {"success": True, "rain_delay_until": delay_until.isoformat()}


@router.delete(
    "/rain_delay",
    dependencies=[Depends(require_permission("system.control"))],
    summary="Cancel rain delay",
)
async def cancel_rain_delay(request: Request):
    """Cancel an active rain delay."""
    key_config: ApiKeyConfig = request.state.api_key_config
    data = _load_schedules()

    data["rain_delay_until"] = None
    _save_schedules(data)

    await ha_client.fire_event(
        "flux_irrigation_rain_delay_cancelled",
        {"source": f"api:{key_config.name}"},
    )

    audit_log.log_action(
        api_key_name=key_config.name,
        method="DELETE",
        path="/api/schedule/rain_delay",
        action="cancel_rain_delay",
        client_ip=request.client.host if request.client else None,
    )

    return {"success": True, "message": "Rain delay cancelled"}
