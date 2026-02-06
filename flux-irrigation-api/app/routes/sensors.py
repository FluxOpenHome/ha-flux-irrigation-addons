"""
Sensor data endpoints.
Read soil moisture, flow rates, rain sensor status, and other irrigation sensors.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from auth import require_permission, ApiKeyConfig
from config import get_config
import ha_client
import audit_log


router = APIRouter(prefix="/sensors", tags=["Sensors"])


class SensorReading(BaseModel):
    entity_id: str
    name: str
    state: str
    unit_of_measurement: Optional[str] = None
    device_class: Optional[str] = None
    friendly_name: Optional[str] = None
    last_changed: Optional[str] = None
    last_updated: Optional[str] = None
    attributes: dict = {}


class SensorSummary(BaseModel):
    total_sensors: int
    sensors: list[SensorReading]
    system_status: str  # "ok", "warning", "error"
    warnings: list[str] = []


@router.get(
    "",
    response_model=SensorSummary,
    dependencies=[Depends(require_permission("sensors.read"))],
    summary="Get all irrigation sensor readings",
)
async def list_sensors(request: Request):
    """Get current readings from all irrigation-related sensors."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    entities = await ha_client.get_entities_by_prefix(config.sensor_entity_prefix)

    sensors = []
    warnings = []

    for entity in entities:
        attrs = entity.get("attributes", {})
        state = entity.get("state", "unknown")

        sensor = SensorReading(
            entity_id=entity["entity_id"],
            name=entity["entity_id"].replace(config.sensor_entity_prefix, ""),
            state=state,
            unit_of_measurement=attrs.get("unit_of_measurement"),
            device_class=attrs.get("device_class"),
            friendly_name=attrs.get("friendly_name"),
            last_changed=entity.get("last_changed"),
            last_updated=entity.get("last_updated"),
            attributes=attrs,
        )
        sensors.append(sensor)

        # Check for warning conditions
        if state in ("unavailable", "unknown"):
            warnings.append(f"Sensor '{sensor.friendly_name or sensor.name}' is {state}")

    # Determine system status
    if any(s.state in ("unavailable", "unknown") for s in sensors):
        system_status = "warning"
    elif len(sensors) == 0:
        system_status = "error"
        warnings.append("No irrigation sensors found")
    else:
        system_status = "ok"

    audit_log.log_action(
        api_key_name=key_config.name,
        method="GET",
        path="/api/sensors",
        action="list_sensors",
        details={"sensor_count": len(sensors), "system_status": system_status},
        client_ip=request.client.host if request.client else None,
    )

    return SensorSummary(
        total_sensors=len(sensors),
        sensors=sensors,
        system_status=system_status,
        warnings=warnings,
    )


@router.get(
    "/{sensor_id}",
    response_model=SensorReading,
    dependencies=[Depends(require_permission("sensors.read"))],
    summary="Get a specific sensor reading",
)
async def get_sensor(sensor_id: str, request: Request):
    """Get the current reading from a specific irrigation sensor."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    entity_id = f"{config.sensor_entity_prefix}{sensor_id}"
    entity = await ha_client.get_entity_state(entity_id)

    if entity is None:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found.")

    attrs = entity.get("attributes", {})

    audit_log.log_action(
        api_key_name=key_config.name,
        method="GET",
        path=f"/api/sensors/{sensor_id}",
        action="get_sensor",
        details={"entity_id": entity_id},
        client_ip=request.client.host if request.client else None,
    )

    return SensorReading(
        entity_id=entity["entity_id"],
        name=sensor_id,
        state=entity.get("state", "unknown"),
        unit_of_measurement=attrs.get("unit_of_measurement"),
        device_class=attrs.get("device_class"),
        friendly_name=attrs.get("friendly_name"),
        last_changed=entity.get("last_changed"),
        last_updated=entity.get("last_updated"),
        attributes=attrs,
    )
