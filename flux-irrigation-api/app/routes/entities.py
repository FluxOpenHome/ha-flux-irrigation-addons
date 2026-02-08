"""
Device control entity endpoints.
List, read, and control all non-zone/non-sensor entities on the irrigation device
(numbers, selects, switches, buttons, text inputs, lights, etc.).
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Any
from auth import require_permission, ApiKeyConfig
from config import get_config
import ha_client
import audit_log
from config_changelog import log_change, get_actor, friendly_entity_name


router = APIRouter(prefix="/entities", tags=["Entities"])


class EntityState(BaseModel):
    entity_id: str
    name: str
    domain: str
    state: str
    friendly_name: Optional[str] = None
    last_changed: Optional[str] = None
    last_updated: Optional[str] = None
    attributes: dict = {}


class EntityListResponse(BaseModel):
    total: int
    entities: list[EntityState]


class EntitySetRequest(BaseModel):
    """Flexible request body for setting entity values.
    Which field to use depends on the entity domain:
      - switch/light: state ("on" or "off")
      - number: value (numeric)
      - select: option (string from options list)
      - text: value (string)
      - button: no body needed (just POST to trigger)
    """
    state: Optional[str] = None
    value: Optional[Any] = None
    option: Optional[str] = None


class EntitySetResponse(BaseModel):
    success: bool
    entity_id: str
    action: str
    message: str


def _entity_name(entity_id: str) -> str:
    """Derive entity name from entity_id by stripping the domain prefix."""
    if "." in entity_id:
        return entity_id.split(".", 1)[1]
    return entity_id


def _resolve_control_entity(entity_id: str, config) -> str:
    """Validate that an entity_id is in the allowed control entities list."""
    if entity_id in config.allowed_control_entities:
        return entity_id
    raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")


# --- Domain-specific service routing ---

_DOMAIN_SERVICES = {
    "switch": {
        "on": ("switch", "turn_on"),
        "off": ("switch", "turn_off"),
    },
    "light": {
        "on": ("light", "turn_on"),
        "off": ("light", "turn_off"),
    },
    "number": ("number", "set_value"),
    "select": ("select", "select_option"),
    "text": ("text", "set_value"),
    "button": ("button", "press"),
}


def _get_set_service(domain: str, body: EntitySetRequest) -> tuple[str, str, dict]:
    """Determine the HA service call for setting an entity value.

    Returns: (service_domain, service_name, service_data_extras)
    """
    if domain in ("switch", "light"):
        state = (body.state or "").lower()
        if state not in ("on", "off"):
            raise HTTPException(
                status_code=400,
                detail=f"For {domain} entities, provide 'state' as 'on' or 'off'.",
            )
        svc_domain, svc_name = _DOMAIN_SERVICES[domain][state]
        return svc_domain, svc_name, {}

    if domain == "number":
        if body.value is None:
            raise HTTPException(
                status_code=400,
                detail="For number entities, provide 'value' (numeric).",
            )
        return "number", "set_value", {"value": body.value}

    if domain == "select":
        if not body.option:
            raise HTTPException(
                status_code=400,
                detail="For select entities, provide 'option' (string).",
            )
        return "select", "select_option", {"option": body.option}

    if domain == "text":
        if body.value is None:
            raise HTTPException(
                status_code=400,
                detail="For text entities, provide 'value' (string).",
            )
        return "text", "set_value", {"value": str(body.value)}

    if domain == "button":
        return "button", "press", {}

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported entity domain '{domain}'. Cannot determine service call.",
    )


# --- Endpoints ---


@router.get(
    "",
    response_model=EntityListResponse,
    dependencies=[Depends(require_permission("entities.read"))],
    summary="List all device control entities",
)
async def list_entities(request: Request):
    """Get current state of all device control entities (non-zone, non-sensor)."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    print(f"[ENTITIES] list_entities called: device={config.irrigation_device_id or '(none)'}, "
          f"allowed_control_entities={len(config.allowed_control_entities)} "
          f"({config.allowed_control_entities[:5]}{'...' if len(config.allowed_control_entities) > 5 else ''})")

    states = await ha_client.get_entities_by_ids(config.allowed_control_entities)

    entities = []
    for entity in states:
        eid = entity.get("entity_id", "")
        attrs = entity.get("attributes", {})
        domain = eid.split(".")[0] if "." in eid else ""
        entities.append(
            EntityState(
                entity_id=eid,
                name=_entity_name(eid),
                domain=domain,
                state=entity.get("state", "unknown"),
                friendly_name=attrs.get("friendly_name"),
                last_changed=entity.get("last_changed"),
                last_updated=entity.get("last_updated"),
                attributes=attrs,
            )
        )

    audit_log.log_action(
        api_key_name=key_config.name,
        method="GET",
        path="/api/entities",
        action="list_entities",
        details={"entity_count": len(entities)},
        client_ip=request.client.host if request.client else None,
    )

    return EntityListResponse(total=len(entities), entities=entities)


@router.get(
    "/{entity_id:path}",
    response_model=EntityState,
    dependencies=[Depends(require_permission("entities.read"))],
    summary="Get a specific entity's state",
)
async def get_entity(entity_id: str, request: Request):
    """Get the current state of a specific device control entity."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    # Validate
    entity_id = _resolve_control_entity(entity_id, config)
    entity = await ha_client.get_entity_state(entity_id)

    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found in HA.")

    attrs = entity.get("attributes", {})
    domain = entity_id.split(".")[0] if "." in entity_id else ""

    audit_log.log_action(
        api_key_name=key_config.name,
        method="GET",
        path=f"/api/entities/{entity_id}",
        action="get_entity",
        details={"entity_id": entity_id},
        client_ip=request.client.host if request.client else None,
    )

    return EntityState(
        entity_id=entity_id,
        name=_entity_name(entity_id),
        domain=domain,
        state=entity.get("state", "unknown"),
        friendly_name=attrs.get("friendly_name"),
        last_changed=entity.get("last_changed"),
        last_updated=entity.get("last_updated"),
        attributes=attrs,
    )


@router.post(
    "/{entity_id:path}/set",
    response_model=EntitySetResponse,
    dependencies=[Depends(require_permission("entities.control"))],
    summary="Set an entity's value",
)
async def set_entity(entity_id: str, body: EntitySetRequest, request: Request):
    """Set the value of a device control entity.

    The service called depends on the entity domain:
      - switch/light: turn_on or turn_off (based on 'state')
      - number: set_value (based on 'value')
      - select: select_option (based on 'option')
      - text: set_value (based on 'value')
      - button: press (no body needed)
    """
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    entity_id = _resolve_control_entity(entity_id, config)
    domain = entity_id.split(".")[0] if "." in entity_id else ""

    # Fetch current state before changing it (for changelog old → new)
    old_state = await ha_client.get_entity_state(entity_id)
    old_val = old_state.get("state", "unknown") if old_state else "unknown"

    # Determine which HA service to call
    svc_domain, svc_name, extra_data = _get_set_service(domain, body)

    # Build service data
    service_data = {"entity_id": entity_id, **extra_data}

    success = await ha_client.call_service(svc_domain, svc_name, service_data)

    if not success:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to call {svc_domain}.{svc_name} for {entity_id}.",
        )

    action_desc = f"{svc_domain}.{svc_name}"
    if extra_data:
        action_desc += f" ({extra_data})"

    # Update stored base duration when a duration entity is set
    if domain == "number" and body.value is not None:
        try:
            from routes.moisture import (
                _load_data as _load_moisture_data,
                _save_data as _save_moisture_data,
                apply_adjusted_durations,
                _find_duration_entities,
            )
            dur_entities = _find_duration_entities(config.allowed_control_entities)
            if entity_id in dur_entities:
                from datetime import datetime, timezone
                mdata = _load_moisture_data()
                base_durations = mdata.get("base_durations", {})
                base_durations[entity_id] = base_durations.get(entity_id, {})
                base_durations[entity_id]["base_value"] = float(body.value)
                base_durations[entity_id]["captured_at"] = datetime.now(timezone.utc).isoformat()
                mdata["base_durations"] = base_durations
                _save_moisture_data(mdata)
                if mdata.get("apply_factors_to_schedule"):
                    await apply_adjusted_durations()
        except Exception as e:
            print(f"[ENTITIES] Base duration update after set failed: {e}")

    # Log configuration change with old → new
    actor = get_actor(request)
    fname = friendly_entity_name(entity_id)
    new_val = body.value if body.value is not None else body.state if body.state is not None else body.option
    log_change(actor, "Schedule", f"Set {fname}: {old_val} -> {new_val}",
               {"entity_id": entity_id, "old_value": old_val, "new_value": new_val})

    audit_log.log_action(
        api_key_name=key_config.name,
        method="POST",
        path=f"/api/entities/{entity_id}/set",
        action="set_entity",
        details={
            "entity_id": entity_id,
            "domain": domain,
            "service": f"{svc_domain}.{svc_name}",
            **extra_data,
        },
        client_ip=request.client.host if request.client else None,
    )

    return EntitySetResponse(
        success=True,
        entity_id=entity_id,
        action=f"{svc_domain}.{svc_name}",
        message=f"Called {svc_domain}.{svc_name} on {entity_id}",
    )
