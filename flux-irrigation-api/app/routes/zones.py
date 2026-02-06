"""
Zone management endpoints.
List zones, start/stop individual zones, get zone status.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
from auth import require_permission, ApiKeyConfig
from config import get_config
import ha_client
import audit_log


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

    entities = await ha_client.get_entities_by_prefix(config.irrigation_entity_prefix)

    zones = []
    for entity in entities:
        attrs = entity.get("attributes", {})
        zones.append(
            ZoneStatus(
                entity_id=entity["entity_id"],
                name=entity["entity_id"].replace(config.irrigation_entity_prefix, ""),
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

    entity_id = f"{config.irrigation_entity_prefix}{zone_id}"
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

    entity_id = f"{config.irrigation_entity_prefix}{zone_id}"

    # Verify zone exists
    entity = await ha_client.get_entity_state(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")

    # Turn on the zone
    service_data = {"entity_id": entity_id}
    success = await ha_client.call_service("switch", "turn_on", service_data)

    if not success:
        raise HTTPException(status_code=502, detail="Failed to communicate with Home Assistant.")

    # If duration specified, schedule an auto-off via an HA automation/script
    # or fire an event that the user's automation can handle
    if body.duration_minutes:
        await ha_client.fire_event(
            "flux_irrigation_timed_run",
            {
                "entity_id": entity_id,
                "zone_id": zone_id,
                "duration_minutes": body.duration_minutes,
                "source": f"api:{key_config.name}",
            },
        )

    message = f"Zone '{zone_id}' started"
    if body.duration_minutes:
        message += f" for {body.duration_minutes} minutes"

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

    return ZoneActionResponse(
        success=True,
        zone_id=zone_id,
        action="start",
        message=message,
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

    entity_id = f"{config.irrigation_entity_prefix}{zone_id}"

    # Verify zone exists
    entity = await ha_client.get_entity_state(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")

    service_data = {"entity_id": entity_id}
    success = await ha_client.call_service("switch", "turn_off", service_data)

    if not success:
        raise HTTPException(status_code=502, detail="Failed to communicate with Home Assistant.")

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

    entities = await ha_client.get_entities_by_prefix(config.irrigation_entity_prefix)
    stopped = []

    for entity in entities:
        entity_id = entity["entity_id"]
        if entity.get("state") == "on":
            await ha_client.call_service(
                "switch", "turn_off", {"entity_id": entity_id}
            )
            stopped.append(entity_id)

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
