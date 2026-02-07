"""
Flux Open Home - Management Mode API Routes
=============================================
Customer CRUD and proxy endpoints for management companies
to monitor and control remote homeowner irrigation systems.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

import customer_store
import management_client
from config import get_config
from connection_key import ConnectionKeyData

router = APIRouter(prefix="/admin", tags=["Management"])


# --- Request/Response Models ---


class AddCustomerRequest(BaseModel):
    connection_key: str = Field(
        min_length=10,
        description="Base64 connection key from homeowner",
    )
    name: Optional[str] = Field(
        None, max_length=100, description="Display name (overrides key label)"
    )
    notes: str = Field("", max_length=500)


class UpdateCustomerRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class UpdateZoneAliasesRequest(BaseModel):
    zone_aliases: dict = Field(
        default_factory=dict,
        description="Map of entity_id to display alias",
    )


# --- Helpers ---


def _require_management_mode():
    config = get_config()
    if config.mode != "management":
        raise HTTPException(
            status_code=400,
            detail="This endpoint is only available in management mode.",
        )


def _proxy_error(status_code: int, data: dict) -> HTTPException:
    """Create an HTTPException from a proxy response, ensuring detail is a string."""
    if isinstance(data, dict):
        detail = (
            data.get("detail")
            or data.get("error")
            or data.get("message")
            or data.get("raw")
            or str(data)
        )
    else:
        detail = str(data)
    return HTTPException(status_code=status_code, detail=detail)


def _get_customer_or_404(customer_id: str) -> customer_store.Customer:
    customer = customer_store.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


def _customer_connection(customer: customer_store.Customer) -> ConnectionKeyData:
    print(f"[MGMT] Building connection for {customer.name}: url='{customer.url}', mode='{customer.connection_mode}', ha_token={'SET' if customer.ha_token else 'EMPTY'}")
    return ConnectionKeyData(
        url=customer.url,
        key=customer.api_key,
        ha_token=customer.ha_token or None,
        mode=customer.connection_mode or "direct",
    )


def _customer_response(customer: customer_store.Customer) -> dict:
    """Build a safe response (no API key exposed)."""
    return {
        "id": customer.id,
        "name": customer.name,
        "url": customer.url,
        "added_at": customer.added_at,
        "notes": customer.notes,
        "address": customer.address,
        "city": customer.city,
        "state": customer.state,
        "zip": customer.zip,
        "zone_count": customer.zone_count,
        "last_seen_online": customer.last_seen_online,
        "last_status": customer.last_status,
        "zone_aliases": customer.zone_aliases,
    }


# --- Customer CRUD ---


@router.get("/api/customers", summary="List all customers")
async def list_customers():
    _require_management_mode()
    customers = customer_store.load_customers()
    return {"customers": [_customer_response(c) for c in customers]}


@router.post("/api/customers", summary="Add a customer via connection key")
async def add_customer(body: AddCustomerRequest):
    _require_management_mode()
    try:
        customer = customer_store.add_customer(
            encoded_key=body.connection_key,
            name=body.name,
            notes=body.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    print(f"[MGMT] Customer added: name={customer.name}, url='{customer.url}', mode={customer.connection_mode}, ha_token={'SET('+str(len(customer.ha_token))+'chars)' if customer.ha_token else 'EMPTY'}")

    # Test connectivity immediately
    conn = _customer_connection(customer)
    check_result = await management_client.check_homeowner_connection(conn)
    customer_store.update_customer_status(customer.id, check_result)

    return {
        "success": True,
        "customer": _customer_response(customer),
        "connectivity": check_result,
    }


@router.get("/api/customers/{customer_id}", summary="Get customer details")
async def get_customer(customer_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    return _customer_response(customer)


@router.put("/api/customers/{customer_id}", summary="Update customer name/notes")
async def update_customer(customer_id: str, body: UpdateCustomerRequest):
    _require_management_mode()
    customer = customer_store.update_customer(
        customer_id, name=body.name, notes=body.notes
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"success": True, "customer": _customer_response(customer)}


@router.put(
    "/api/customers/{customer_id}/zone_aliases",
    summary="Update zone display aliases",
)
async def update_zone_aliases(customer_id: str, body: UpdateZoneAliasesRequest):
    _require_management_mode()
    customer = customer_store.update_customer_zone_aliases(
        customer_id, zone_aliases=body.zone_aliases
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"success": True, "zone_aliases": customer.zone_aliases}


@router.delete("/api/customers/{customer_id}", summary="Remove a customer")
async def delete_customer(customer_id: str):
    _require_management_mode()
    if not customer_store.remove_customer(customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"success": True, "message": "Customer removed"}


@router.post(
    "/api/customers/{customer_id}/check", summary="Test customer connectivity"
)
async def check_customer(customer_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    result = await management_client.check_homeowner_connection(conn)
    customer_store.update_customer_status(customer_id, result)
    return {"customer_id": customer_id, "customer_name": customer.name, **result}


# --- Proxy Endpoints ---


@router.get("/api/customers/{customer_id}/status", summary="Get customer system status")
async def get_customer_status(customer_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/api/system/status"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.get("/api/customers/{customer_id}/zones", summary="Get customer zones")
async def get_customer_zones(customer_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/api/zones"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.post(
    "/api/customers/{customer_id}/zones/{zone_id}/start",
    summary="Start a customer zone",
)
async def start_customer_zone(customer_id: str, zone_id: str, request: Request):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    # Forward request body if present (may contain duration_minutes)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "POST", f"/api/zones/{zone_id}/start", json_body=body
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.post(
    "/api/customers/{customer_id}/zones/{zone_id}/stop",
    summary="Stop a customer zone",
)
async def stop_customer_zone(customer_id: str, zone_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST", f"/api/zones/{zone_id}/stop"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.post(
    "/api/customers/{customer_id}/zones/stop_all",
    summary="Emergency stop all customer zones",
)
async def stop_all_customer_zones(customer_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/api/zones/stop_all"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.get("/api/customers/{customer_id}/sensors", summary="Get customer sensors")
async def get_customer_sensors(customer_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/api/sensors"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.get(
    "/api/customers/{customer_id}/entities",
    summary="Get customer device control entities",
)
async def get_customer_entities(customer_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/api/entities"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.post(
    "/api/customers/{customer_id}/entities/{entity_id:path}/set",
    summary="Set a customer entity value",
)
async def set_customer_entity(customer_id: str, entity_id: str, request: Request):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "POST", f"/api/entities/{entity_id}/set", json_body=body
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.post(
    "/api/customers/{customer_id}/system/pause",
    summary="Pause customer system",
)
async def pause_customer_system(customer_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/api/system/pause"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.post(
    "/api/customers/{customer_id}/system/resume",
    summary="Resume customer system",
)
async def resume_customer_system(customer_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/api/system/resume"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.get(
    "/api/customers/{customer_id}/history/runs",
    summary="Get customer run history",
)
async def get_customer_history(
    customer_id: str, zone_id: Optional[str] = None, hours: int = 24
):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    params = {"hours": str(hours)}
    if zone_id:
        params["zone_id"] = zone_id
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/api/history/runs", params=params
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.get(
    "/api/customers/{customer_id}/weather",
    summary="Get customer weather data",
)
async def get_customer_weather(customer_id: str):
    """Get weather conditions and adjustments for a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/weather"
    )
    if status_code != 200:
        # Weather may not be configured on the homeowner side — return safe default
        return {
            "weather_enabled": False,
            "weather": {"error": "Not available"},
        }
    return data


@router.get(
    "/api/customers/{customer_id}/weather/rules",
    summary="Get customer weather rules",
)
async def get_customer_weather_rules(customer_id: str):
    """Get weather rules configuration from a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/weather/rules"
    )
    if status_code != 200:
        return {"rules": {}, "error": "Weather rules not available"}
    return data


@router.put(
    "/api/customers/{customer_id}/weather/rules",
    summary="Update customer weather rules",
)
async def update_customer_weather_rules(customer_id: str, request: Request):
    """Update weather rules configuration on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "PUT", "/admin/api/weather/rules", json_body=body
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.post(
    "/api/customers/{customer_id}/weather/evaluate",
    summary="Trigger customer weather evaluation",
)
async def evaluate_customer_weather(customer_id: str):
    """Manually trigger weather rules evaluation on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/admin/api/weather/evaluate"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.get(
    "/api/customers/{customer_id}/weather/log",
    summary="Get customer weather event log",
)
async def get_customer_weather_log(
    customer_id: str,
    limit: int = 200,
    hours: int = 0,
):
    """Get weather event log from a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    params = {"limit": str(limit)}
    if hours > 0:
        params["hours"] = str(hours)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/weather/log", params=params
    )
    if status_code != 200:
        return {"events": []}
    return data


@router.get(
    "/api/customers/{customer_id}/history/runs/csv",
    summary="Export customer run history as CSV",
)
async def get_customer_history_csv(customer_id: str, hours: int = 24):
    """Fetch customer run history JSON and convert to CSV for download."""
    from fastapi.responses import Response

    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/api/history/runs", params={"hours": str(hours)}
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)

    events = data.get("events", [])
    lines = ["timestamp,zone_name,entity_id,state,duration_minutes"]
    for e in events:
        dur = ""
        if e.get("duration_seconds") is not None:
            dur = str(round(e["duration_seconds"] / 60, 1))
        line = ",".join([
            e.get("timestamp", ""),
            _csv_escape(e.get("zone_name", "")),
            e.get("entity_id", ""),
            e.get("state", ""),
            dur,
        ])
        lines.append(line)

    csv_content = "\n".join(lines) + "\n"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=irrigation_history_{hours}h.csv"},
    )


@router.get(
    "/api/customers/{customer_id}/weather/log/csv",
    summary="Export customer weather log as CSV",
)
async def get_customer_weather_log_csv(customer_id: str, hours: int = 0):
    """Fetch customer weather log JSON and convert to CSV for download."""
    from fastapi.responses import Response

    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    params = {"limit": "10000"}
    if hours > 0:
        params["hours"] = str(hours)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/weather/log", params=params
    )
    if status_code != 200:
        return Response(
            content="timestamp,event,condition,temperature,humidity,wind_speed,watering_multiplier,rules_triggered,reason\n",
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=weather_log.csv"},
        )

    events = data.get("events", [])
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
