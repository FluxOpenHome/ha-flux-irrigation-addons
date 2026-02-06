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


def _zone_name(entity_id: str) -> str:
    """Derive zone name from entity_id by stripping the domain prefix."""
    if "." in entity_id:
        return entity_id.split(".", 1)[1]
    return entity_id


def _resolve_zone_entity(zone_id: str, config) -> str:
    """Resolve a zone_id to a full entity_id, validating it's allowed.

    Tries switch.{zone_id} and valve.{zone_id} to support both entity types.
    Also accepts a full entity_id directly if it's in the allowed list.
    """
    # Check if zone_id is already a full entity_id
    if zone_id in config.allowed_zone_entities:
        return zone_id

    # Try common zone domains
    for domain in ("switch", "valve"):
        entity_id = f"{domain}.{zone_id}"
        if entity_id in config.allowed_zone_entities:
            return entity_id

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

    # Verify zone exists in HA
    entity = await ha_client.get_entity_state(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")

    # Turn on the zone (supports both switch and valve entities)
    svc_domain, svc_name = _get_zone_service(entity_id, "on")
    service_data = {"entity_id": entity_id}
    success = await ha_client.call_service(svc_domain, svc_name, service_data)

    if not success:
        raise HTTPException(status_code=502, detail="Failed to communicate with Home Assistant.")

    # If duration specified, fire an event that the user's automation can handle
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

    entity_id = _resolve_zone_entity(zone_id, config)

    # Verify zone exists in HA
    entity = await ha_client.get_entity_state(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")

    svc_domain, svc_name = _get_zone_service(entity_id, "off")
    service_data = {"entity_id": entity_id}
    success = await ha_client.call_service(svc_domain, svc_name, service_data)

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
