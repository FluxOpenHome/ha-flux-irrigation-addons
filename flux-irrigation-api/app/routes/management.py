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
