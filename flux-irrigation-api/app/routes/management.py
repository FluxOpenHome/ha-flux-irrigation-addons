"""
Flux Open Home - Management Mode API Routes
=============================================
Customer CRUD and proxy endpoints for management companies
to monitor and control remote homeowner irrigation systems.
"""

import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
import httpx

import customer_store
import management_client
import management_notification_store
import notification_config
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


class UpdateConnectionKeyRequest(BaseModel):
    connection_key: str = Field(
        min_length=10,
        description="New base64 connection key from homeowner",
    )


class UpdateZoneAliasesRequest(BaseModel):
    zone_aliases: dict = Field(
        default_factory=dict,
        description="Map of entity_id to display alias",
    )


# --- Helpers ---


def _require_management_mode():
    config = get_config()
    if config.mode != "management":
        print(f"[MGMT] Rejected request — config.mode='{config.mode}', expected 'management'")
        raise HTTPException(
            status_code=400,
            detail=f"This endpoint is only available in management mode (current mode: {config.mode}).",
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


async def _notify_homeowner(
    conn: ConnectionKeyData,
    event_type: str,
    title: str,
    message: str,
):
    """Best-effort notification recording on the homeowner instance.

    Failures are silently ignored — notification recording should never
    block or break the primary management operation.
    """
    try:
        status_code, resp_data = await management_client.proxy_request(
            conn, "POST", "/admin/api/homeowner/notifications/record",
            json_body={
                "event_type": event_type,
                "title": title,
                "message": message,
            },
        )
        print(f"[NOTIFY_HOMEOWNER] {event_type} → {title} | proxy status={status_code}, resp={resp_data}")
    except Exception as exc:
        print(f"[NOTIFY_HOMEOWNER] {event_type} → {title} | EXCEPTION: {exc}")


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
        "phone": customer.phone,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "zone_count": customer.zone_count,
        "last_seen_online": customer.last_seen_online,
        "last_status": customer.last_status,
        "zone_aliases": customer.zone_aliases,
        "issue_summary": customer.issue_summary,
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
    "/api/customers/{customer_id}/connection-key",
    summary="Update customer connection key",
)
async def update_connection_key(customer_id: str, body: UpdateConnectionKeyRequest):
    """Replace a customer's connection key. Preserves notes, aliases, and name."""
    _require_management_mode()
    try:
        customer = customer_store.update_customer_connection_key(
            customer_id, encoded_key=body.connection_key
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    print(f"[MGMT] Connection key updated for {customer.name}: url='{customer.url}', mode={customer.connection_mode}")

    # Test connectivity immediately with the new key
    conn = _customer_connection(customer)
    check_result = await management_client.check_homeowner_connection(conn)
    customer_store.update_customer_status(customer.id, check_result)

    return {
        "success": True,
        "customer": _customer_response(customer),
        "connectivity": check_result,
    }


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


@router.get(
    "/api/customers/{customer_id}/zone_heads/reference",
    summary="Get nozzle reference data via customer",
)
async def get_customer_nozzle_reference(customer_id: str):
    """Get nozzle type reference data via customer proxy."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/zone_heads/reference"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.get(
    "/api/customers/{customer_id}/zone_heads",
    summary="Get all customer zone head details",
)
async def get_customer_all_zone_heads(customer_id: str):
    """Get head/nozzle details for all zones of a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/zone_heads"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.get(
    "/api/customers/{customer_id}/zone_heads/{entity_id:path}",
    summary="Get customer zone head details",
)
async def get_customer_zone_heads(customer_id: str, entity_id: str):
    """Get head/nozzle details for a specific customer zone."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", f"/admin/api/homeowner/zone_heads/{entity_id}"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.put(
    "/api/customers/{customer_id}/zone_heads/{entity_id:path}",
    summary="Save customer zone head details",
)
async def save_customer_zone_heads(customer_id: str, entity_id: str, request: Request):
    """Save head/nozzle details for a specific customer zone."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "PUT", f"/admin/api/homeowner/zone_heads/{entity_id}",
        json_body=body,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.delete(
    "/api/customers/{customer_id}/zone_heads/{entity_id:path}",
    summary="Delete customer zone head details",
)
async def delete_customer_zone_heads(customer_id: str, entity_id: str):
    """Remove all head/nozzle details for a specific customer zone."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "DELETE", f"/admin/api/homeowner/zone_heads/{entity_id}",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


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
        conn, "POST", f"/api/zones/{zone_id}/start", json_body=body,
        extra_headers={"X-Actor": "Management"},
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
        conn, "POST", f"/api/zones/{zone_id}/stop",
        extra_headers={"X-Actor": "Management"},
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
        conn, "POST", "/api/zones/stop_all",
        extra_headers={"X-Actor": "Management"},
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
        conn, "POST", f"/api/entities/{entity_id}/set", json_body=body,
        extra_headers={"X-Actor": "Management"},
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
        conn, "POST", "/api/system/pause",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    await _notify_homeowner(conn, "system_changes", "System Paused",
                            "Your irrigation system was paused by management.")
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
        conn, "POST", "/api/system/resume",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    await _notify_homeowner(conn, "system_changes", "System Resumed",
                            "Your irrigation system was resumed by management.")
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
        conn, "GET", "/admin/api/homeowner/history/runs", params=params
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
        conn, "PUT", "/admin/api/weather/rules", json_body=body,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    await _notify_homeowner(conn, "weather_changes", "Weather Rules Updated",
                            "Management updated your weather adjustment rules.")
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
        conn, "POST", "/admin/api/weather/evaluate",
        extra_headers={"X-Actor": "Management"},
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
        conn, "GET", "/admin/api/homeowner/history/runs", params={"hours": str(hours)}
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)

    events = data.get("events", [])
    lines = ["timestamp,zone_name,entity_id,state,source,duration_minutes,weather_condition,temperature,humidity,wind_speed,watering_multiplier,weather_rules,moisture_multiplier,combined_multiplier"]
    for e in events:
        dur = ""
        if e.get("duration_seconds") is not None:
            dur = str(round(e["duration_seconds"] / 60, 1))
        wx = e.get("weather") or {}
        mo = e.get("moisture") or {}
        rules_str = ";".join(wx.get("active_adjustments", wx.get("rules_triggered", [])))
        # Moisture/combined multiplier only for schedule events
        moisture_mult = ""
        combined_mult = ""
        if e.get("source") == "schedule":
            if mo.get("moisture_multiplier") is not None:
                moisture_mult = str(mo["moisture_multiplier"])
            if mo.get("combined_multiplier") is not None:
                combined_mult = str(mo["combined_multiplier"])
        line = ",".join([
            e.get("timestamp", ""),
            _csv_escape(e.get("zone_name", "")),
            e.get("entity_id", ""),
            e.get("state", ""),
            e.get("source", ""),
            dur,
            _csv_escape(str(wx.get("condition", ""))),
            _csv_escape(str(wx.get("temperature", ""))),
            _csv_escape(str(wx.get("humidity", ""))),
            _csv_escape(str(wx.get("wind_speed", ""))),
            _csv_escape(str(wx.get("watering_multiplier", ""))),
            _csv_escape(rules_str),
            moisture_mult,
            combined_mult,
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


@router.delete(
    "/api/customers/{customer_id}/weather/log",
    summary="Clear customer weather log",
)
async def clear_customer_weather_log(customer_id: str):
    """Clear weather event log on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "DELETE", "/admin/api/homeowner/weather/log",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": "Failed to clear weather log"}
    return data


@router.delete(
    "/api/customers/{customer_id}/history/runs",
    summary="Clear customer run history",
)
async def clear_customer_history(customer_id: str):
    """Clear run history on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "DELETE", "/admin/api/homeowner/history/runs",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": "Failed to clear run history"}
    return data


# --- Moisture Probe Proxy Endpoints ---

@router.get(
    "/api/customers/{customer_id}/moisture/probes",
    summary="Get customer moisture probes",
)
async def get_customer_moisture_probes(customer_id: str):
    """Get moisture probe configuration and live readings from a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/moisture/probes"
    )
    if status_code != 200:
        return {"enabled": False, "probes": {}, "total": 0}
    return data


@router.get(
    "/api/customers/{customer_id}/moisture/settings",
    summary="Get customer moisture settings",
)
async def get_customer_moisture_settings(customer_id: str):
    """Get moisture probe settings from a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/moisture/settings"
    )
    if status_code != 200:
        return {"enabled": False}
    return data


@router.put(
    "/api/customers/{customer_id}/moisture/settings",
    summary="Update customer moisture settings",
)
async def update_customer_moisture_settings(customer_id: str, request: Request):
    """Update moisture settings on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "PUT", "/admin/api/homeowner/moisture/settings", json_body=body,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": "Failed to update moisture settings"}
    await _notify_homeowner(conn, "moisture_changes", "Moisture Settings Updated",
                            "Management updated your moisture probe settings.")
    return data


@router.get(
    "/api/customers/{customer_id}/moisture/multiplier",
    summary="Get customer overall moisture multiplier",
)
async def get_customer_moisture_multiplier(customer_id: str):
    """Get the overall moisture multiplier from a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/moisture/multiplier"
    )
    if status_code != 200:
        return {"moisture_multiplier": 1.0, "weather_multiplier": 1.0, "combined_multiplier": 1.0}
    return data


@router.get(
    "/api/customers/{customer_id}/moisture/probes/discover",
    summary="Discover moisture probes on customer system",
)
async def discover_customer_moisture_probes(customer_id: str):
    """Scan for moisture probe sensors on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/moisture/probes/discover"
    )
    if status_code != 200:
        return {"candidates": [], "total": 0}
    return data


@router.post(
    "/api/customers/{customer_id}/moisture/probes",
    summary="Add moisture probe to customer system",
)
async def add_customer_moisture_probe(customer_id: str, request: Request):
    """Add a moisture probe on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/admin/api/homeowner/moisture/probes", json_body=body,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": "Failed to add probe"}
    return data


@router.put(
    "/api/customers/{customer_id}/moisture/probes/{probe_id}",
    summary="Update moisture probe on customer system",
)
async def update_customer_moisture_probe(customer_id: str, probe_id: str, request: Request):
    """Update a moisture probe on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "PUT", f"/admin/api/homeowner/moisture/probes/{probe_id}", json_body=body,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": "Failed to update probe"}
    return data


@router.delete(
    "/api/customers/{customer_id}/moisture/probes/{probe_id}",
    summary="Remove moisture probe from customer system",
)
async def delete_customer_moisture_probe(customer_id: str, probe_id: str):
    """Remove a moisture probe on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "DELETE", f"/admin/api/homeowner/moisture/probes/{probe_id}",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": "Failed to remove probe"}
    return data


@router.post(
    "/api/customers/{customer_id}/moisture/probes/sync-schedules",
    summary="Sync irrigation schedules to customer moisture probes",
)
async def sync_customer_probe_schedules(customer_id: str):
    """Sync irrigation controller start times to Gophr probe schedule_time entities."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/admin/api/homeowner/moisture/probes/sync-schedules",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": "Failed to sync schedules", "synced": 0}
    return data


@router.get(
    "/api/customers/{customer_id}/moisture/schedule-timeline",
    summary="Get customer schedule timeline",
)
async def get_customer_schedule_timeline(customer_id: str):
    """Return the calculated irrigation schedule timeline for a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/moisture/schedule-timeline",
    )
    if status_code != 200:
        return {"success": False, "schedules": [], "probe_prep": {}}
    return data


@router.post(
    "/api/customers/{customer_id}/moisture/schedule-timeline/recalculate",
    summary="Force recalculate customer schedule timeline",
)
async def recalculate_customer_schedule_timeline(customer_id: str):
    """Force a recalculation of the irrigation schedule timeline for a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/admin/api/homeowner/moisture/schedule-timeline/recalculate",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": "Failed to recalculate timeline"}
    return data


@router.put(
    "/api/customers/{customer_id}/moisture/probes/{probe_id}/sleep-duration",
    summary="Set probe sleep duration",
)
async def set_customer_probe_sleep_duration(customer_id: str, probe_id: str, request: Request):
    """Set sleep duration for a customer's Gophr probe (applies immediately or queues for wake)."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    body = await request.body()
    status_code, data = await management_client.proxy_request(
        conn, "PUT",
        f"/admin/api/homeowner/moisture/probes/{probe_id}/sleep-duration",
        json_body=json.loads(body) if body else None,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": data.get("detail", "Failed to set sleep duration") if isinstance(data, dict) else "Failed to set sleep duration"}
    return data


@router.put(
    "/api/customers/{customer_id}/moisture/probes/{probe_id}/sleep-disabled",
    summary="Toggle probe sleep disabled",
)
async def set_customer_probe_sleep_disabled(customer_id: str, probe_id: str, request: Request):
    """Toggle sleep disabled for a customer's Gophr probe (applies immediately or queues for wake)."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    body = await request.body()
    status_code, data = await management_client.proxy_request(
        conn, "PUT",
        f"/admin/api/homeowner/moisture/probes/{probe_id}/sleep-disabled",
        json_body=json.loads(body) if body else None,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": data.get("detail", "Failed to toggle sleep") if isinstance(data, dict) else "Failed to toggle sleep"}
    return data


@router.post(
    "/api/customers/{customer_id}/moisture/probes/{probe_id}/sleep-now",
    summary="Force probe to sleep immediately",
)
async def press_customer_probe_sleep_now(customer_id: str, probe_id: str):
    """Press the sleep_now button on a customer's Gophr probe to force it to sleep immediately."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST",
        f"/admin/api/homeowner/moisture/probes/{probe_id}/sleep-now",
    )
    if status_code != 200:
        return {"success": False, "error": data.get("detail", "Failed to press sleep now") if isinstance(data, dict) else "Failed to press sleep now"}
    return data


@router.post(
    "/api/customers/{customer_id}/moisture/probes/{probe_id}/calibrate",
    summary="Press calibration buttons on customer probe",
)
async def calibrate_customer_probe(customer_id: str, probe_id: str, request: Request):
    """Press calibration buttons on a customer's Gophr probe."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "POST",
        f"/admin/api/homeowner/moisture/probes/{probe_id}/calibrate",
        json_body=body,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {
            "success": False,
            "error": data.get("detail", "Calibration failed")
            if isinstance(data, dict) else "Calibration failed"
        }
    return data


@router.post(
    "/api/customers/{customer_id}/moisture/zones/{zone_id}/multiplier",
    summary="Preview zone moisture multiplier",
)
async def get_customer_zone_multiplier(customer_id: str, zone_id: str):
    """Get the moisture multiplier for a zone on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST", f"/admin/api/homeowner/moisture/zones/{zone_id}/multiplier"
    )
    if status_code != 200:
        return {"combined_multiplier": 1.0, "moisture_multiplier": 1.0, "weather_multiplier": 1.0}
    return data


@router.get(
    "/api/customers/{customer_id}/moisture/durations",
    summary="Get customer duration adjustment status",
)
async def get_customer_moisture_durations(customer_id: str):
    """Get base vs. adjusted duration status from a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/moisture/durations"
    )
    if status_code != 200:
        return {"duration_adjustment_active": False, "base_durations": {}, "adjusted_durations": {}}
    return data


@router.post(
    "/api/customers/{customer_id}/moisture/durations/capture",
    summary="Capture base durations on customer system",
)
async def capture_customer_moisture_durations(customer_id: str):
    """Capture current run durations as base values on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/admin/api/homeowner/moisture/durations/capture",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": "Failed to capture durations"}
    return data


@router.post(
    "/api/customers/{customer_id}/moisture/durations/apply",
    summary="Apply adjusted durations on customer system",
)
async def apply_customer_moisture_durations(customer_id: str):
    """Apply adjusted durations on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/admin/api/homeowner/moisture/durations/apply",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": "Failed to apply durations"}
    await _notify_homeowner(conn, "duration_changes", "Adjusted Durations Applied",
                            "Management applied adjusted zone durations to your schedule.")
    return data


@router.post(
    "/api/customers/{customer_id}/moisture/durations/restore",
    summary="Restore base durations on customer system",
)
async def restore_customer_moisture_durations(customer_id: str):
    """Restore base durations on a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/admin/api/homeowner/moisture/durations/restore",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return {"success": False, "error": "Failed to restore durations"}
    await _notify_homeowner(conn, "duration_changes", "Base Durations Restored",
                            "Management restored your base zone durations.")
    return data


@router.get(
    "/api/customers/{customer_id}/changelog",
    summary="Get customer configuration change log",
)
async def get_customer_changelog(customer_id: str, limit: int = 200):
    """Get configuration change log from a customer system."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/changelog",
        params={"limit": str(limit)},
    )
    if status_code != 200:
        return {"entries": []}
    return data


@router.get(
    "/api/customers/{customer_id}/changelog/csv",
    summary="Export customer change log as CSV",
)
async def get_customer_changelog_csv(customer_id: str):
    """Export configuration change log as CSV from a customer system."""
    from fastapi.responses import Response
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/changelog",
        params={"limit": "1000"},
    )
    entries = data.get("entries", []) if status_code == 200 else []
    lines = ["timestamp,actor,category,description"]
    for e in entries:
        lines.append(",".join([
            _csv_escape(e.get("timestamp", "")),
            _csv_escape(e.get("actor", "")),
            _csv_escape(e.get("category", "")),
            _csv_escape(e.get("description", "")),
        ]))
    csv_content = "\n".join(lines) + "\n"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=config_changelog.csv"},
    )


def _csv_escape(value: str) -> str:
    """Escape a value for CSV output."""
    if not value or value == "None":
        return ""
    if "," in value or '"' in value or "\n" in value:
        return '"' + value.replace('"', '""') + '"'
    return value


# --- Issue Proxy Endpoints ---


@router.get(
    "/api/customers/{customer_id}/issues",
    summary="Get customer issues",
)
async def get_customer_issues(customer_id: str):
    """Get all issues reported by a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/issues"
    )
    if status_code != 200:
        return {"issues": [], "total": 0}
    return data


@router.get(
    "/api/customers/{customer_id}/issues/active",
    summary="Get customer active issues",
)
async def get_customer_active_issues(customer_id: str):
    """Get active (non-resolved) issues from a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/issues/active"
    )
    if status_code != 200:
        return {"issues": [], "total": 0}
    return data


@router.put(
    "/api/customers/{customer_id}/issues/{issue_id}/acknowledge",
    summary="Acknowledge a customer issue",
)
async def acknowledge_customer_issue(customer_id: str, issue_id: str, request: Request):
    """Management acknowledges an issue, optionally scheduling a service date."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "PUT", f"/admin/api/homeowner/issues/{issue_id}/acknowledge",
        json_body=body,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return _proxy_error(status_code, data)
    # Notify homeowner about service date if present
    if status_code == 200 and isinstance(data, dict):
        issue_data = data.get("issue", {})
        sd = issue_data.get("service_date")
        if sd:
            if issue_data.get("service_date_updated_at"):
                ntitle = "Service Date Updated"
                nmsg = f"Your service appointment has been rescheduled to {sd}."
            else:
                ntitle = "Service Scheduled"
                nmsg = f"A service appointment has been scheduled for {sd}."
            mnote = issue_data.get("management_note")
            if mnote:
                nmsg += f" Note: {mnote}"
            await _notify_homeowner(conn, "service_appointments", ntitle, nmsg)

        # Record to management notification store
        try:
            evt_type = "service_scheduled" if sd else "acknowledged"
            evt_title = f"{'Service Scheduled' if sd else 'Acknowledged'}: {customer.name}"
            evt_msg = issue_data.get("description", "")[:200]
            management_notification_store.record_event(
                event_type=evt_type,
                customer_id=customer_id,
                customer_name=customer.name,
                title=evt_title,
                message=evt_msg,
                severity=issue_data.get("severity", ""),
            )
        except Exception:
            pass  # Best-effort
    return data


@router.put(
    "/api/customers/{customer_id}/issues/{issue_id}/resolve",
    summary="Resolve a customer issue",
)
async def resolve_customer_issue(customer_id: str, issue_id: str, request: Request):
    """Management marks an issue as resolved."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "PUT", f"/admin/api/homeowner/issues/{issue_id}/resolve",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        return _proxy_error(status_code, data)

    # Record to management notification store
    try:
        issue_data = data.get("issue", {}) if isinstance(data, dict) else {}
        management_notification_store.record_event(
            event_type="resolved",
            customer_id=customer_id,
            customer_name=customer.name,
            title=f"Resolved: {customer.name}",
            message=issue_data.get("description", "")[:200],
            severity=issue_data.get("severity", ""),
        )
    except Exception:
        pass  # Best-effort

    return data


# --- HA Notification Settings ---


class UpdateNotificationSettingsRequest(BaseModel):
    enabled: Optional[bool] = None
    ha_notify_service: Optional[str] = Field(None, max_length=200)
    notify_severe: Optional[bool] = None
    notify_annoyance: Optional[bool] = None
    notify_clarification: Optional[bool] = None


@router.get("/api/notification-settings", summary="Get HA notification settings")
async def get_notification_settings():
    """Get the current HA notification configuration for issue alerts."""
    _require_management_mode()
    return notification_config.get_settings()


@router.put("/api/notification-settings", summary="Update HA notification settings")
async def update_notification_settings(body: UpdateNotificationSettingsRequest):
    """Update the HA notification configuration for issue alerts."""
    _require_management_mode()
    return notification_config.update_settings(
        enabled=body.enabled,
        ha_notify_service=body.ha_notify_service,
        notify_severe=body.notify_severe,
        notify_annoyance=body.notify_annoyance,
        notify_clarification=body.notify_clarification,
    )


@router.post("/api/notification-settings/test", summary="Send a test notification")
async def test_notification():
    """Send a test notification through the configured HA notify service."""
    _require_management_mode()
    settings = notification_config.get_settings()
    if not settings.get("ha_notify_service"):
        raise HTTPException(status_code=400, detail="No HA notify service configured")

    import ha_client
    service_name = settings["ha_notify_service"]
    success = await ha_client.call_service("notify", service_name, {
        "message": "🧪 Test notification from Flux Open Home — HA notifications are working!",
        "title": "Flux Open Home Test",
    })
    if not success:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to call notify.{service_name} — check that the service exists in Home Assistant",
        )
    return {"success": True, "message": f"Test notification sent via notify.{service_name}"}


@router.get("/api/notification-settings/services", summary="Discover available HA notify services")
async def discover_notify_services():
    """Query Home Assistant for all available notify.* services.

    Returns a list of service names (e.g. 'mobile_app_brandons_iphone')
    that can be used in the notification settings.
    """
    _require_management_mode()
    import ha_client

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ha_client.HA_BASE_URL}/services",
            headers=ha_client._get_headers(),
            timeout=10.0,
        )
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to query HA services")

    services = []
    for domain_entry in response.json():
        if domain_entry.get("domain") == "notify":
            for svc_name, svc_info in domain_entry.get("services", {}).items():
                if svc_name == "send_message":
                    continue
                label = svc_info.get("name") or svc_name.replace("_", " ").title()
                services.append({"id": svc_name, "name": label})
            break

    services.sort(key=lambda s: s["name"])
    return {"services": services}


# --- Management Notification Feed ---


class UpdateMgmtNotifPreferencesRequest(BaseModel):
    notify_new_issue: Optional[bool] = None
    notify_acknowledged: Optional[bool] = None
    notify_service_scheduled: Optional[bool] = None
    notify_resolved: Optional[bool] = None
    notify_returned: Optional[bool] = None


@router.get("/api/mgmt-notifications", summary="Get management notification feed")
async def get_mgmt_notifications(limit: int = 50):
    """Get recent management notification events and unread count."""
    _require_management_mode()
    events = management_notification_store.get_events(limit=limit)
    unread = management_notification_store.get_unread_count()
    return {"events": events, "unread_count": unread}


@router.put("/api/mgmt-notifications/{event_id}/read", summary="Mark notification read")
async def mark_mgmt_notification_read(event_id: str):
    """Mark a single management notification as read."""
    _require_management_mode()
    found = management_notification_store.mark_read(event_id)
    return {"success": found}


@router.put("/api/mgmt-notifications/read-all", summary="Mark all notifications read")
async def mark_all_mgmt_notifications_read():
    """Mark all management notifications as read."""
    _require_management_mode()
    count = management_notification_store.mark_all_read()
    return {"success": True, "marked": count}


@router.delete("/api/mgmt-notifications/clear", summary="Clear all notifications")
async def clear_all_mgmt_notifications():
    """Remove all management notification events."""
    _require_management_mode()
    count = management_notification_store.clear_all()
    return {"success": True, "cleared": count}


@router.get("/api/mgmt-notification-preferences", summary="Get management notification preferences")
async def get_mgmt_notification_preferences():
    """Get preferences for which event types should appear in the notification feed."""
    _require_management_mode()
    return management_notification_store.get_preferences()


@router.put("/api/mgmt-notification-preferences", summary="Update management notification preferences")
async def update_mgmt_notification_preferences(body: UpdateMgmtNotifPreferencesRequest):
    """Update management notification feed preferences."""
    _require_management_mode()
    updates = {}
    if body.notify_new_issue is not None:
        updates["notify_new_issue"] = body.notify_new_issue
    if body.notify_acknowledged is not None:
        updates["notify_acknowledged"] = body.notify_acknowledged
    if body.notify_service_scheduled is not None:
        updates["notify_service_scheduled"] = body.notify_service_scheduled
    if body.notify_resolved is not None:
        updates["notify_resolved"] = body.notify_resolved
    if body.notify_returned is not None:
        updates["notify_returned"] = body.notify_returned
    return management_notification_store.update_preferences(updates)


# --- PDF Report Proxy Endpoint ---


@router.get(
    "/api/customers/{customer_id}/report/pdf",
    summary="Generate customer system report PDF",
)
async def get_customer_report_pdf(
    customer_id: str,
    hours: int = Query(720, ge=1, le=8760),
):
    """Generate a comprehensive system report PDF for a customer.

    Gathers data from the customer's homeowner API via proxy,
    then builds the PDF locally using the shared report builder.
    """
    import traceback
    from fastapi.responses import Response as FastResponse, JSONResponse
    from datetime import datetime as dt
    from routes.report_pdf import build_report

    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)

    try:
        # Gather all data via proxy calls to the customer's homeowner API
        _, status_data = await management_client.proxy_request(
            conn, "GET", "/admin/api/homeowner/status"
        )
        if not isinstance(status_data, dict):
            status_data = {}

        _, zones_data = await management_client.proxy_request(
            conn, "GET", "/admin/api/homeowner/zones"
        )
        if not isinstance(zones_data, list):
            zones_data = []

        _, aliases_data = await management_client.proxy_request(
            conn, "GET", "/admin/api/homeowner/zone_aliases"
        )
        if not isinstance(aliases_data, dict):
            aliases_data = {}

        _, zone_heads_data = await management_client.proxy_request(
            conn, "GET", "/admin/api/homeowner/zone_heads"
        )
        if not isinstance(zone_heads_data, dict):
            zone_heads_data = {}

        _, sensors_resp = await management_client.proxy_request(
            conn, "GET", "/admin/api/homeowner/sensors"
        )
        sensors_data = sensors_resp.get("sensors", []) if isinstance(sensors_resp, dict) else []

        _, weather_data = await management_client.proxy_request(
            conn, "GET", "/admin/api/homeowner/weather"
        )
        if not isinstance(weather_data, dict):
            weather_data = {"weather_enabled": False}

        _, moisture_settings = await management_client.proxy_request(
            conn, "GET", "/admin/api/homeowner/moisture/settings"
        )
        moisture_data = moisture_settings if isinstance(moisture_settings, dict) else {"enabled": False}

        _, issues_resp = await management_client.proxy_request(
            conn, "GET", "/admin/api/homeowner/issues"
        )
        issues_data = issues_resp if isinstance(issues_resp, list) else issues_resp.get("issues", []) if isinstance(issues_resp, dict) else []

        _, history_data = await management_client.proxy_request(
            conn, "GET", "/admin/api/homeowner/history/runs",
            params={"hours": str(hours)},
        )
        if not isinstance(history_data, list):
            history_data = history_data.get("events", []) if isinstance(history_data, dict) else []

        # Fetch water source settings
        water_settings = {}
        try:
            _, ws_resp = await management_client.proxy_request(
                conn, "GET", "/admin/api/homeowner/water_settings"
            )
            if isinstance(ws_resp, dict):
                water_settings = ws_resp
        except Exception:
            pass

        # Fetch report branding settings
        report_settings = {}
        try:
            _, rs_resp = await management_client.proxy_request(
                conn, "GET", "/admin/api/homeowner/report_settings"
            )
            if isinstance(rs_resp, dict):
                report_settings = rs_resp
        except Exception:
            pass

        # Fetch custom logo bytes if one exists
        custom_logo_bytes = None
        if report_settings.get("has_custom_logo"):
            try:
                logo_status, logo_bytes = await management_client.proxy_request_raw(
                    conn, "GET", "/admin/api/homeowner/report_settings/logo"
                )
                if logo_status == 200 and logo_bytes:
                    custom_logo_bytes = logo_bytes
            except Exception:
                pass

        # Build PDF using shared builder
        pdf = build_report(
            status_data, zones_data, aliases_data, zone_heads_data,
            sensors_data, weather_data, moisture_data, issues_data,
            history_data, hours,
            water_settings=water_settings,
            report_settings=report_settings,
            custom_logo_bytes=custom_logo_bytes,
        )

        pdf_bytes = bytes(pdf.output())
        timestamp = dt.now().strftime("%Y%m%d_%H%M")
        return FastResponse(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="flux_report_{customer_id}_{timestamp}.pdf"',
            },
        )
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[MGMT REPORT PDF] Error generating report for {customer_id}: {e}\n{tb}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate PDF report: {str(e)}"},
        )


# ----------  Pump Settings & Stats  ----------

@router.get(
    "/api/customers/{customer_id}/pump_settings",
    summary="Get customer pump settings",
)
async def get_customer_pump_settings(customer_id: str):
    """Get pump configuration for a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/pump_settings"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.put(
    "/api/customers/{customer_id}/pump_settings",
    summary="Save customer pump settings",
)
async def save_customer_pump_settings(customer_id: str, request: Request):
    """Save pump configuration for a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "PUT", "/admin/api/homeowner/pump_settings",
        json_body=body,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    await _notify_homeowner(conn, "equipment_changes", "Pump Settings Updated",
                            "Management updated your pump configuration.")
    return data


@router.get(
    "/api/customers/{customer_id}/pump_stats",
    summary="Get customer pump usage statistics",
)
async def get_customer_pump_stats(
    customer_id: str,
    hours: int = Query(720, ge=1, le=8760),
):
    """Get pump usage statistics for a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/pump_stats",
        params={"hours": hours},
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


# --- Water Source Settings (proxy) ---


@router.get(
    "/api/customers/{customer_id}/water_settings",
    summary="Get customer water source settings",
)
async def get_customer_water_settings(customer_id: str):
    """Get water source configuration for a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/water_settings"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.put(
    "/api/customers/{customer_id}/water_settings",
    summary="Save customer water source settings",
)
async def save_customer_water_settings(customer_id: str, request: Request):
    """Save water source configuration for a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "PUT", "/admin/api/homeowner/water_settings",
        json_body=body,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    await _notify_homeowner(conn, "equipment_changes", "Water Settings Updated",
                            "Management updated your water source settings.")
    return data


# --- Report Settings (proxy) ---


@router.get(
    "/api/customers/{customer_id}/report_settings",
    summary="Get customer report settings",
)
async def get_customer_report_settings(customer_id: str):
    """Get PDF report branding settings for a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "GET", "/admin/api/homeowner/report_settings"
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.put(
    "/api/customers/{customer_id}/report_settings",
    summary="Save customer report settings",
)
async def save_customer_report_settings(customer_id: str, request: Request):
    """Save PDF report branding settings for a customer."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    try:
        body = await request.json()
    except Exception:
        body = None
    status_code, data = await management_client.proxy_request(
        conn, "PUT", "/admin/api/homeowner/report_settings",
        json_body=body,
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    await _notify_homeowner(conn, "report_changes", "Report Settings Updated",
                            "Management updated your PDF report branding settings.")
    return data


@router.post(
    "/api/customers/{customer_id}/report_settings/logo",
    summary="Upload customer report logo",
)
async def upload_customer_report_logo(customer_id: str, request: Request):
    """Upload a custom logo for a customer's PDF report.

    Accepts multipart form with 'logo' file field. Forwards to homeowner
    as base64 JSON for Nabu Casa compatibility.
    """
    import base64
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)

    form = await request.form()
    file = form.get("logo")
    if not file:
        raise HTTPException(400, "No logo file provided")
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(400, "Logo file too large (max 2MB)")

    # Forward as base64 JSON (works through Nabu Casa rest_command proxy)
    b64 = base64.b64encode(contents).decode("ascii")
    status_code, data = await management_client.proxy_request(
        conn, "POST", "/admin/api/homeowner/report_settings/logo_base64",
        json_body={"logo_base64": b64},
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.delete(
    "/api/customers/{customer_id}/report_settings/logo",
    summary="Remove customer report logo",
)
async def delete_customer_report_logo(customer_id: str):
    """Remove the custom logo for a customer's PDF report."""
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, data = await management_client.proxy_request(
        conn, "DELETE", "/admin/api/homeowner/report_settings/logo",
        extra_headers={"X-Actor": "Management"},
    )
    if status_code != 200:
        raise _proxy_error(status_code, data)
    return data


@router.get(
    "/api/customers/{customer_id}/report_settings/logo",
    summary="Get customer report logo",
)
async def get_customer_report_logo(customer_id: str):
    """Serve the custom logo image for a customer, or 404 if none."""
    from fastapi.responses import Response as FastResponse
    _require_management_mode()
    customer = _get_customer_or_404(customer_id)
    conn = _customer_connection(customer)
    status_code, raw_bytes = await management_client.proxy_request_raw(
        conn, "GET", "/admin/api/homeowner/report_settings/logo"
    )
    if status_code == 404:
        raise HTTPException(404, "No custom logo")
    if status_code != 200:
        raise HTTPException(status_code, "Failed to fetch logo")
    return FastResponse(content=raw_bytes, media_type="image/png")


# ----------  Portfolio Report  ----------


@router.get(
    "/api/portfolio_report/settings",
    summary="Get portfolio report settings",
)
async def get_portfolio_report_settings():
    """Get the portfolio report branding & section settings."""
    _require_management_mode()
    import portfolio_report_settings as prs
    return prs.get_settings()


@router.put(
    "/api/portfolio_report/settings",
    summary="Save portfolio report settings",
)
async def save_portfolio_report_settings(request: Request):
    """Save portfolio report branding & section settings."""
    _require_management_mode()
    import portfolio_report_settings as prs
    body = await request.json()
    return prs.save_settings(body)


@router.post(
    "/api/portfolio_report/settings/logo",
    summary="Upload portfolio report logo",
)
async def upload_portfolio_report_logo(request: Request):
    """Upload a custom company logo for the portfolio report cover page."""
    _require_management_mode()
    import portfolio_report_settings as prs
    form = await request.form()
    file = form.get("logo")
    if not file:
        raise HTTPException(400, "No logo file provided")
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(400, "Logo file too large (max 2MB)")
    prs.save_logo(contents)
    return {"success": True, "message": "Logo uploaded"}


@router.delete(
    "/api/portfolio_report/settings/logo",
    summary="Remove portfolio report logo",
)
async def delete_portfolio_report_logo():
    """Remove the custom logo for the portfolio report."""
    _require_management_mode()
    import portfolio_report_settings as prs
    prs.delete_logo()
    return {"success": True, "message": "Logo removed"}


@router.get(
    "/api/portfolio_report/settings/logo",
    summary="Get portfolio report logo",
)
async def get_portfolio_report_logo():
    """Serve the custom logo image for the portfolio report, or 404 if none."""
    from fastapi.responses import Response as FastResponse
    _require_management_mode()
    import portfolio_report_settings as prs
    path = prs.get_logo_path()
    if not path:
        raise HTTPException(404, "No custom logo")
    with open(path, "rb") as f:
        logo_bytes = f.read()
    return FastResponse(content=logo_bytes, media_type="image/png")


async def _gather_portfolio_data(customers: list, hours: int) -> list:
    """Fetch status, zones, issues, history, moisture, weather from each customer in parallel."""
    import asyncio

    async def _fetch_one(customer) -> dict:
        conn = _customer_connection(customer)
        result = {
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "address": getattr(customer, "address", ""),
                "city": getattr(customer, "city", ""),
                "state": getattr(customer, "state", ""),
            },
            "online": False,
            "status": {},
            "zones": [],
            "zone_aliases": {},
            "zone_heads": {},
            "issues": [],
            "history": [],
            "moisture": {},
            "weather": {},
            "water_settings": {},
            "sensors": [],
        }
        try:
            tasks = {
                "status": management_client.proxy_request(conn, "GET", "/admin/api/homeowner/status"),
                "zones": management_client.proxy_request(conn, "GET", "/admin/api/homeowner/zones"),
                "zone_aliases": management_client.proxy_request(conn, "GET", "/admin/api/homeowner/zone_aliases"),
                "zone_heads": management_client.proxy_request(conn, "GET", "/admin/api/homeowner/zone_heads"),
                "issues": management_client.proxy_request(conn, "GET", "/admin/api/homeowner/issues"),
                "history": management_client.proxy_request(
                    conn, "GET", "/admin/api/homeowner/history/runs",
                    params={"hours": str(hours)},
                ),
                "moisture": management_client.proxy_request(conn, "GET", "/admin/api/homeowner/moisture/settings"),
                "weather": management_client.proxy_request(conn, "GET", "/admin/api/homeowner/weather"),
                "water_settings": management_client.proxy_request(conn, "GET", "/admin/api/homeowner/water_settings"),
                "sensors": management_client.proxy_request(conn, "GET", "/admin/api/homeowner/sensors"),
            }
            keys = list(tasks.keys())
            responses = await asyncio.gather(*tasks.values(), return_exceptions=True)

            for key, resp in zip(keys, responses):
                if isinstance(resp, Exception):
                    continue
                sc, data = resp
                if sc == 200 and data:
                    if key == "sensors" and isinstance(data, dict):
                        result[key] = data.get("sensors", [])
                    elif key == "issues" and isinstance(data, dict):
                        result[key] = data.get("issues", []) if "issues" in data else []
                    elif key == "history" and isinstance(data, dict):
                        result[key] = data.get("events", []) if "events" in data else []
                    else:
                        result[key] = data

            result["online"] = True
        except Exception as e:
            print(f"[PORTFOLIO] Failed to fetch data for {customer.name}: {e}")

        return result

    sem = asyncio.Semaphore(10)

    async def _limited_fetch(c):
        async with sem:
            return await _fetch_one(c)

    results = await asyncio.gather(*[_limited_fetch(c) for c in customers])
    return list(results)


@router.get(
    "/api/portfolio_report/pdf",
    summary="Generate portfolio statistics PDF",
)
async def generate_portfolio_report_pdf(
    hours: int = Query(720, ge=1, le=8760),
):
    """Generate a cross-customer portfolio statistics PDF report.

    Gathers data from all connected customer instances in parallel,
    aggregates the results, and builds a multi-page PDF.
    """
    import traceback
    import io
    from datetime import datetime as dt
    from fastapi.responses import Response as FastResponse, JSONResponse

    _require_management_mode()

    import portfolio_report_settings as prs
    from portfolio_report import build_portfolio_report

    try:
        settings = prs.get_settings()
        logo_path = prs.get_logo_path()
        custom_logo_bytes = None
        if logo_path:
            with open(logo_path, "rb") as f:
                custom_logo_bytes = f.read()

        # Load all customers
        customers = customer_store.load_customers()
        if not customers:
            return JSONResponse(
                status_code=400,
                content={"error": "No customers configured"},
            )

        # Fetch data from all customers in parallel
        customer_data = await _gather_portfolio_data(customers, hours)

        pdf = build_portfolio_report(
            customer_data=customer_data,
            hours=hours,
            report_settings=settings,
            custom_logo_bytes=custom_logo_bytes,
        )

        pdf_bytes = bytes(pdf.output())
        timestamp = dt.now().strftime("%Y%m%d_%H%M")
        return FastResponse(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="portfolio_report_{timestamp}.pdf"',
            },
        )
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[PORTFOLIO REPORT PDF] Error generating report: {e}\n{tb}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate portfolio report: {str(e)}"},
        )
