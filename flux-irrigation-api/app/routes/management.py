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


@router.get("/api/customers/{customer_id}/schedule", summary="Get customer schedule")
async def get_customer_schedule(customer_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/api/schedule"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.put("/api/customers/{customer_id}/schedule", summary="Update customer schedule")
async def update_customer_schedule(customer_id: str, request: Request):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    status_code, data = await management_client.proxy_request(
        conn, "PUT", "/api/schedule", json_body=body
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.post(
    "/api/customers/{customer_id}/schedule/program",
    summary="Add a schedule program",
)
async def add_customer_program(customer_id: str, request: Request):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/api/schedule/program", json_body=body
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.delete(
    "/api/customers/{customer_id}/schedule/program/{program_id}",
    summary="Delete a schedule program",
)
async def delete_customer_program(customer_id: str, program_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "DELETE", f"/api/schedule/program/{program_id}"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.post(
    "/api/customers/{customer_id}/schedule/rain_delay",
    summary="Set rain delay",
)
async def set_customer_rain_delay(customer_id: str, request: Request):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/api/schedule/rain_delay", json_body=body
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.delete(
    "/api/customers/{customer_id}/schedule/rain_delay",
    summary="Cancel rain delay",
)
async def cancel_customer_rain_delay(customer_id: str):
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "DELETE", "/api/schedule/rain_delay"
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
