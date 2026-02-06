"""
Admin settings endpoints and web UI.
Allows the homeowner to configure API keys, device selection,
and permissions through the add-on's ingress panel.
"""

import json
import os
import secrets
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
from config import get_config, reload_config


router = APIRouter(prefix="/admin", tags=["Admin"])

OPTIONS_FILE = "/data/options.json"


def _load_options() -> dict:
    """Load current options from persistent storage."""
    if os.path.exists(OPTIONS_FILE):
        with open(OPTIONS_FILE, "r") as f:
            return json.load(f)
    return {}


async def _save_options(options: dict):
    """Save options to persistent storage and reload config."""
    os.makedirs(os.path.dirname(OPTIONS_FILE), exist_ok=True)
    with open(OPTIONS_FILE, "w") as f:
        json.dump(options, f, indent=2)
    await reload_config()


# --- API Endpoints for Settings ---


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    permissions: list[str] = []


class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[list[str]] = None
    regenerate_key: bool = False


class DeviceSelect(BaseModel):
    device_id: str = Field(min_length=1)


class SettingsUpdate(BaseModel):
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=300)
    log_retention_days: Optional[int] = Field(None, ge=1, le=365)
    enable_audit_log: Optional[bool] = None


@router.get("/api/settings", summary="Get current settings")
async def get_settings():
    """Get all current add-on settings."""
    options = _load_options()
    config = get_config()

    # Mask API keys for display
    api_keys = []
    for key_entry in options.get("api_keys", []):
        masked = key_entry.copy()
        raw_key = masked.get("key", "")
        if len(raw_key) > 8:
            masked["key_preview"] = f"{raw_key[:4]}...{raw_key[-4:]}"
        else:
            masked["key_preview"] = "****"
        del masked["key"]
        api_keys.append(masked)

    return {
        "mode": config.mode,
        "api_keys": api_keys,
        "irrigation_device_id": options.get("irrigation_device_id", ""),
        "allowed_zone_entities": config.allowed_zone_entities,
        "allowed_sensor_entities": config.allowed_sensor_entities,
        "rate_limit_per_minute": options.get("rate_limit_per_minute", 60),
        "log_retention_days": options.get("log_retention_days", 30),
        "enable_audit_log": options.get("enable_audit_log", True),
        "homeowner_url": options.get("homeowner_url", ""),
        "homeowner_label": options.get("homeowner_label", ""),
        "homeowner_address": options.get("homeowner_address", ""),
        "homeowner_city": options.get("homeowner_city", ""),
        "homeowner_state": options.get("homeowner_state", ""),
        "homeowner_zip": options.get("homeowner_zip", ""),
    }


@router.post("/api/keys", summary="Create a new API key")
async def create_api_key(body: ApiKeyCreate):
    """Generate a new API key for a management company."""
    options = _load_options()
    if "api_keys" not in options:
        options["api_keys"] = []

    new_key = secrets.token_urlsafe(32)
    key_entry = {
        "key": new_key,
        "name": body.name,
        "permissions": body.permissions,
    }
    options["api_keys"].append(key_entry)
    await _save_options(options)

    return {
        "success": True,
        "name": body.name,
        "key": new_key,  # Show full key only on creation
        "permissions": body.permissions,
        "message": "Save this key now — it won't be shown again.",
    }


@router.put("/api/keys/{key_index}", summary="Update an API key")
async def update_api_key(key_index: int, body: ApiKeyUpdate):
    """Update an existing API key's name, permissions, or regenerate it."""
    options = _load_options()
    keys = options.get("api_keys", [])

    if key_index < 0 or key_index >= len(keys):
        raise HTTPException(status_code=404, detail="API key not found.")

    if body.name is not None:
        keys[key_index]["name"] = body.name
    if body.permissions is not None:
        keys[key_index]["permissions"] = body.permissions

    new_key_value = None
    if body.regenerate_key:
        new_key_value = secrets.token_urlsafe(32)
        keys[key_index]["key"] = new_key_value

    options["api_keys"] = keys
    await _save_options(options)

    result = {"success": True, "name": keys[key_index]["name"]}
    if new_key_value:
        result["key"] = new_key_value
        result["message"] = "New key generated. Save it now — it won't be shown again."
    return result


@router.delete("/api/keys/{key_index}", summary="Delete an API key")
async def delete_api_key(key_index: int):
    """Revoke and delete an API key."""
    options = _load_options()
    keys = options.get("api_keys", [])

    if key_index < 0 or key_index >= len(keys):
        raise HTTPException(status_code=404, detail="API key not found.")

    removed = keys.pop(key_index)
    options["api_keys"] = keys
    await _save_options(options)

    return {"success": True, "removed": removed["name"]}


@router.get("/api/devices", summary="List available HA devices")
async def list_devices():
    """List all Home Assistant devices for selection."""
    config = get_config()
    if config.mode != "homeowner":
        raise HTTPException(
            status_code=400, detail="Device management is only available in homeowner mode."
        )
    import ha_client

    try:
        devices = await ha_client.get_device_registry()
    except Exception as e:
        print(f"[ADMIN] Failed to fetch device registry: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch device registry: {type(e).__name__}: {e}",
        )

    # Return devices with useful display info
    result = []
    for device in devices:
        name = device.get("name_by_user") or device.get("name") or ""
        manufacturer = device.get("manufacturer") or ""
        model = device.get("model") or ""

        if not name:
            continue

        result.append({
            "id": device.get("id", ""),
            "name": name,
            "manufacturer": manufacturer,
            "model": model,
            "area_id": device.get("area_id", ""),
        })

    # Sort by name for display
    result.sort(key=lambda d: d["name"].lower())
    return result


@router.put("/api/device", summary="Select irrigation device")
async def select_device(body: DeviceSelect):
    """Select the irrigation controller device and resolve its entities."""
    config = get_config()
    if config.mode != "homeowner":
        raise HTTPException(
            status_code=400, detail="Device management is only available in homeowner mode."
        )
    import ha_client

    # Verify the device exists and get its entities
    try:
        entities = await ha_client.get_device_entities(body.device_id)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch device entities: {e}",
        )

    # Save device_id to options
    options = _load_options()
    options["irrigation_device_id"] = body.device_id
    await _save_options(options)

    config = get_config()

    return {
        "success": True,
        "device_id": body.device_id,
        "zones": entities.get("zones", []),
        "sensors": entities.get("sensors", []),
        "other": entities.get("other", []),
        "allowed_zone_entities": config.allowed_zone_entities,
        "allowed_sensor_entities": config.allowed_sensor_entities,
    }


@router.get("/api/device/entities", summary="Get selected device entities")
async def get_device_entities():
    """Get the entities resolved from the currently selected device."""
    config = get_config()

    if not config.irrigation_device_id:
        return {
            "device_id": "",
            "zones": [],
            "sensors": [],
            "other": [],
        }

    import ha_client

    try:
        entities = await ha_client.get_device_entities(config.irrigation_device_id)
    except Exception:
        entities = {"zones": [], "sensors": [], "other": []}

    return {
        "device_id": config.irrigation_device_id,
        "zones": entities.get("zones", []),
        "sensors": entities.get("sensors", []),
        "other": entities.get("other", []),
    }


@router.get("/api/device/debug", summary="Debug device entity resolution")
async def debug_device_entities():
    """Diagnostic endpoint: shows raw entity registry data for the selected device."""
    config = get_config()
    import ha_client

    result = {
        "device_id": config.irrigation_device_id or "(not set)",
        "supervisor_token_available": bool(config.supervisor_token),
        "supervisor_token_length": len(config.supervisor_token) if config.supervisor_token else 0,
        "mode": config.mode,
        "allowed_zone_entities": config.allowed_zone_entities,
        "allowed_sensor_entities": config.allowed_sensor_entities,
    }

    if not config.irrigation_device_id:
        result["error"] = "No device selected"
        return result

    # Try WebSocket first
    try:
        ws_entities = await ha_client._ws_command("config/entity_registry/list")
        ws_matched = [e for e in ws_entities if e.get("device_id") == config.irrigation_device_id]
        result["ws_total_entities"] = len(ws_entities)
        result["ws_matched_entities"] = len(ws_matched)
        result["ws_matched_sample"] = ws_matched[:10]
        result["ws_status"] = "ok"
    except Exception as e:
        result["ws_status"] = f"failed: {type(e).__name__}: {e}"

    # Try template fallback
    try:
        tpl_entities = await ha_client._get_entities_via_template()
        tpl_matched = [e for e in tpl_entities if e.get("device_id") == config.irrigation_device_id]
        result["template_total_entities"] = len(tpl_entities)
        result["template_matched_entities"] = len(tpl_matched)
        result["template_matched_sample"] = tpl_matched[:10]
        result["template_status"] = "ok"
    except Exception as e:
        result["template_status"] = f"failed: {type(e).__name__}: {e}"

    # Show what get_device_entities returns
    try:
        dev_entities = await ha_client.get_device_entities(config.irrigation_device_id)
        result["categorized"] = {
            "zones": len(dev_entities.get("zones", [])),
            "sensors": len(dev_entities.get("sensors", [])),
            "other": len(dev_entities.get("other", [])),
        }
        result["categorized_detail"] = dev_entities
    except Exception as e:
        result["categorized_error"] = str(e)

    return result


@router.put("/api/general", summary="Update general settings")
async def update_general_settings(body: SettingsUpdate):
    """Update rate limiting, logging, and other general settings."""
    options = _load_options()

    if body.rate_limit_per_minute is not None:
        options["rate_limit_per_minute"] = body.rate_limit_per_minute
    if body.log_retention_days is not None:
        options["log_retention_days"] = body.log_retention_days
    if body.enable_audit_log is not None:
        options["enable_audit_log"] = body.enable_audit_log

    await _save_options(options)
    return {"success": True}


# --- Mode Switch ---


class ModeSwitch(BaseModel):
    mode: str = Field(pattern=r"^(homeowner|management)$")


@router.put("/api/mode", summary="Switch operating mode")
async def switch_mode(body: ModeSwitch):
    """Switch between homeowner and management mode."""
    options = _load_options()
    options["mode"] = body.mode
    await _save_options(options)
    return {
        "success": True,
        "mode": body.mode,
        "message": f"Switched to {body.mode} mode. Reload the page.",
    }


# --- Connection Key (Homeowner Mode) ---


class ConnectionKeyRequest(BaseModel):
    url: str = Field(min_length=1, description="Externally reachable API URL")
    label: str = Field("", max_length=100, description="Property label")
    address: str = Field("", max_length=200, description="Street address")
    city: str = Field("", max_length=100, description="City")
    state: str = Field("", max_length=50, description="State")
    zip: str = Field("", max_length=20, description="ZIP code")
    ha_token: str = Field("", description="HA Long-Lived Access Token (for Nabu Casa mode)")
    connection_mode: str = Field("direct", description="Connection mode: 'nabu_casa' or 'direct'")


@router.post("/api/connection-key", summary="Generate a connection key")
async def generate_connection_key(body: ConnectionKeyRequest):
    """Generate a connection key for sharing with a management company."""
    from connection_key import ConnectionKeyData, encode_connection_key

    config = get_config()
    if config.mode != "homeowner":
        raise HTTPException(
            status_code=400,
            detail="Connection keys can only be generated in homeowner mode.",
        )

    options = _load_options()
    options["homeowner_url"] = body.url
    options["homeowner_label"] = body.label
    options["homeowner_address"] = body.address
    options["homeowner_city"] = body.city
    options["homeowner_state"] = body.state
    options["homeowner_zip"] = body.zip
    options["homeowner_ha_token"] = body.ha_token
    options["homeowner_connection_mode"] = body.connection_mode

    # Auto-detect zone count from selected device
    zone_count = len(config.allowed_zone_entities) if config.allowed_zone_entities else None

    # Find or create a dedicated management company key
    existing_keys = options.get("api_keys", [])
    mgmt_key_name = "Management Company (Connection Key)"
    mgmt_key = None

    for key_entry in existing_keys:
        if key_entry.get("name") == mgmt_key_name:
            mgmt_key = key_entry["key"]
            break

    if not mgmt_key:
        mgmt_key = secrets.token_urlsafe(32)
        existing_keys.append({
            "key": mgmt_key,
            "name": mgmt_key_name,
            "permissions": [
                "zones.read", "zones.control", "schedule.read",
                "schedule.write", "sensors.read", "history.read",
                "system.control",
            ],
        })
        options["api_keys"] = existing_keys

    await _save_options(options)

    key_data = ConnectionKeyData(
        url=body.url,
        key=mgmt_key,
        label=body.label,
        address=body.address or None,
        city=body.city or None,
        state=body.state or None,
        zip=body.zip or None,
        zone_count=zone_count,
        ha_token=body.ha_token or None,
        mode=body.connection_mode or "direct",
    )
    encoded = encode_connection_key(key_data)

    return {
        "success": True,
        "connection_key": encoded,
        "url": body.url,
        "label": body.label,
        "address": body.address,
        "city": body.city,
        "state": body.state,
        "zip": body.zip,
        "zone_count": zone_count,
        "api_key_name": mgmt_key_name,
    }


@router.post("/api/test-url", summary="Test if a URL is reachable from this add-on")
async def test_url(body: dict):
    """Test connectivity to a URL from the server side (inside the Docker container).
    This is what matters for management client connectivity."""
    import httpx

    url = body.get("url", "").rstrip("/")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Detect Nabu Casa URLs in direct mode testing — they won't reach port 8099
    if ".ui.nabu.casa" in url or ".nabucasa.com" in url:
        return {
            "success": False,
            "url_tested": url,
            "error": "Nabu Casa URLs cannot reach port 8099 directly.",
            "help": (
                "Use the 'Nabu Casa' connection mode instead (recommended). "
                "It routes through Home Assistant's REST API automatically."
            ),
        }

    test_url = f"{url}/api/system/health"
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False) as client:
            response = await client.get(test_url)
            return {
                "success": True,
                "url_tested": test_url,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text[:200],
                "message": "URL is reachable from this add-on",
            }
    except httpx.ConnectError as e:
        return {
            "success": False,
            "url_tested": test_url,
            "error": f"Connection failed: {e}",
            "help": "Make sure port 8099 is enabled in the add-on Network config and accessible from the network.",
        }
    except httpx.TimeoutException:
        return {
            "success": False,
            "url_tested": test_url,
            "error": "Connection timed out after 10 seconds",
            "help": "The server didn't respond. Check firewall and port forwarding settings.",
        }
    except Exception as e:
        return {
            "success": False,
            "url_tested": test_url,
            "error": f"{type(e).__name__}: {e}",
        }


@router.get("/api/connection-key", summary="Get current connection key info")
async def get_connection_key_info():
    """Get the current connection key configuration."""
    options = _load_options()
    url = options.get("homeowner_url", "")
    label = options.get("homeowner_label", "")
    address = options.get("homeowner_address", "")
    city = options.get("homeowner_city", "")
    state = options.get("homeowner_state", "")
    zip_code = options.get("homeowner_zip", "")
    ha_token = options.get("homeowner_ha_token", "")
    connection_mode = options.get("homeowner_connection_mode", "direct")

    config = get_config()
    zone_count = len(config.allowed_zone_entities) if config.allowed_zone_entities else None

    mgmt_key_name = "Management Company (Connection Key)"
    mgmt_key = None
    for key_entry in options.get("api_keys", []):
        if key_entry.get("name") == mgmt_key_name:
            mgmt_key = key_entry["key"]
            break

    connection_key = None
    if mgmt_key and url:
        from connection_key import ConnectionKeyData, encode_connection_key
        key_data = ConnectionKeyData(
            url=url, key=mgmt_key, label=label,
            address=address or None, city=city or None,
            state=state or None, zip=zip_code or None,
            zone_count=zone_count,
            ha_token=ha_token or None,
            mode=connection_mode,
        )
        connection_key = encode_connection_key(key_data)

    return {
        "configured": bool(url and mgmt_key),
        "url": url,
        "label": label,
        "address": address,
        "city": city,
        "state": state,
        "zip": zip_code,
        "zone_count": zone_count,
        "connection_key": connection_key,
        "ha_token_set": bool(ha_token),
        "connection_mode": connection_mode,
    }


# --- Web UI ---


@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def admin_ui(request: Request):
    """Serve the admin settings UI (mode-dependent)."""
    config = get_config()
    if config.mode == "management":
        from routes.management_ui import MANAGEMENT_HTML
        return HTMLResponse(content=MANAGEMENT_HTML)
    return HTMLResponse(content=ADMIN_HTML)


ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flux Irrigation API — Settings</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f6fa;
            color: #2c3e50;
            line-height: 1.6;
        }
        .header {
            background: linear-gradient(135deg, #1a7a4c, #2ecc71);
            color: white;
            padding: 24px 32px;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .header h1 { font-size: 22px; font-weight: 600; }
        .header .subtitle { opacity: 0.85; font-size: 14px; }
        .container { max-width: 900px; margin: 24px auto; padding: 0 16px; }

        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            overflow: hidden;
        }
        .card-header {
            padding: 16px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .card-header h2 { font-size: 16px; font-weight: 600; }
        .card-body { padding: 20px; }

        .form-group { margin-bottom: 16px; }
        .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #666;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.2s;
        }
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: #2ecc71;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary { background: #2ecc71; color: white; }
        .btn-primary:hover { background: #27ae60; }
        .btn-danger { background: #e74c3c; color: white; }
        .btn-danger:hover { background: #c0392b; }
        .btn-secondary { background: #ecf0f1; color: #2c3e50; }
        .btn-secondary:hover { background: #ddd; }
        .btn-sm { padding: 6px 12px; font-size: 12px; }

        .api-key-card {
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
        }
        .api-key-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .api-key-name { font-weight: 600; font-size: 15px; }
        .api-key-preview { font-family: monospace; color: #888; font-size: 13px; }

        .permissions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 8px;
            margin-top: 8px;
        }
        .perm-checkbox {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
        }
        .perm-checkbox input[type="checkbox"] { width: auto; }

        .toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 1000;
        }
        .toast.success { background: #2ecc71; }
        .toast.error { background: #e74c3c; }
        .toast.visible { opacity: 1; }

        .new-key-display {
            background: #fffde7;
            border: 2px solid #f9a825;
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            display: none;
        }
        .new-key-display code {
            font-size: 15px;
            word-break: break-all;
            display: block;
            margin: 8px 0;
            padding: 8px;
            background: #fff;
            border-radius: 4px;
        }
        .new-key-display .warning { color: #e65100; font-weight: 600; font-size: 13px; }

        .entity-list {
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
        }
        .entity-list h4 {
            font-size: 13px;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .entity-item {
            padding: 6px 0;
            border-bottom: 1px solid #f5f5f5;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
        }
        .entity-item:last-child { border-bottom: none; }
        .entity-id { font-family: monospace; }
        .entity-name { color: #888; }

        .toggle-switch {
            position: relative;
            width: 44px;
            height: 24px;
            display: inline-block;
        }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background: #ccc;
            border-radius: 24px;
            transition: 0.3s;
        }
        .toggle-slider:before {
            content: "";
            position: absolute;
            height: 18px; width: 18px;
            left: 3px; bottom: 3px;
            background: white;
            border-radius: 50%;
            transition: 0.3s;
        }
        .toggle-switch input:checked + .toggle-slider { background: #2ecc71; }
        .toggle-switch input:checked + .toggle-slider:before { transform: translateX(20px); }

        .status-bar {
            display: flex;
            gap: 12px;
            padding: 12px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #eee;
            font-size: 13px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 4px;
        }
        .status-dot.green { background: #2ecc71; }
        .status-dot.red { background: #e74c3c; }
        .status-dot.yellow { background: #f39c12; }

        .device-info {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 12px;
            font-size: 13px;
            color: #666;
        }
        .device-info.empty {
            text-align: center;
            color: #999;
            padding: 24px;
        }
    </style>
</head>
<body>

<div class="header">
    <div>
        <h1>Flux Irrigation Management API</h1>
        <div class="subtitle">Configure API access for irrigation management companies</div>
    </div>
    <div>
        <span style="background:rgba(255,255,255,0.2);padding:4px 12px;border-radius:12px;font-size:12px;">Homeowner Mode</span>
        <button class="btn btn-secondary btn-sm" style="margin-left:8px;" onclick="switchToManagement()">Switch to Management</button>
    </div>
</div>

<div class="container">

    <!-- System Status -->
    <div class="card">
        <div class="status-bar" id="statusBar">
            <span><span class="status-dot" id="statusDot"></span> <span id="statusText">Checking...</span></span>
            <span id="statusZones"></span>
            <span id="statusSensors"></span>
        </div>
    </div>

    <!-- Device Selection -->
    <div class="card">
        <div class="card-header">
            <h2>Irrigation Controller Device</h2>
            <button class="btn btn-secondary btn-sm" onclick="loadDevices()">Refresh Devices</button>
        </div>
        <div class="card-body">
            <div class="form-group">
                <label>Select Device</label>
                <select id="deviceSelect" onchange="onDeviceChange()">
                    <option value="">-- Select your irrigation controller --</option>
                </select>
            </div>

            <div id="deviceEntities">
                <div class="device-info empty" id="noDeviceMsg">
                    Select your irrigation controller device above to configure which entities are exposed through the API.
                </div>
            </div>
        </div>
    </div>

    <!-- API Keys -->
    <div class="card">
        <div class="card-header">
            <h2>API Keys</h2>
            <button class="btn btn-primary btn-sm" onclick="showCreateKey()">+ New API Key</button>
        </div>
        <div class="card-body">
            <div id="newKeyForm" style="display:none; margin-bottom:16px; padding:16px; border:1px solid #eee; border-radius:8px;">
                <div class="form-group">
                    <label>Company Name</label>
                    <input type="text" id="newKeyName" placeholder="e.g., ABC Irrigation Management">
                </div>
                <div class="form-group">
                    <label>Permissions</label>
                    <div class="permissions-grid" id="newKeyPermissions">
                        <label class="perm-checkbox"><input type="checkbox" value="zones.read" checked> Zones: Read</label>
                        <label class="perm-checkbox"><input type="checkbox" value="zones.control" checked> Zones: Control</label>
                        <label class="perm-checkbox"><input type="checkbox" value="schedule.read" checked> Schedule: Read</label>
                        <label class="perm-checkbox"><input type="checkbox" value="schedule.write" checked> Schedule: Write</label>
                        <label class="perm-checkbox"><input type="checkbox" value="sensors.read" checked> Sensors: Read</label>
                        <label class="perm-checkbox"><input type="checkbox" value="history.read" checked> History: Read</label>
                        <label class="perm-checkbox"><input type="checkbox" value="system.control"> System: Control</label>
                    </div>
                </div>
                <button class="btn btn-primary" onclick="createKey()">Generate API Key</button>
                <button class="btn btn-secondary" onclick="hideCreateKey()">Cancel</button>
            </div>

            <div id="newKeyDisplay" class="new-key-display">
                <strong>New API Key Created</strong>
                <code id="newKeyValue"></code>
                <p class="warning">Copy this key now — it will not be shown again!</p>
                <button class="btn btn-secondary btn-sm" onclick="copyKey()">Copy to Clipboard</button>
            </div>

            <div id="apiKeysList"></div>
        </div>
    </div>

    <!-- Connection Key -->
    <div class="card">
        <div class="card-header">
            <h2>Connection Key for Management Company</h2>
        </div>
        <div class="card-body">
            <p style="margin-bottom:16px; color:#666; font-size:14px;">
                Generate a connection key to share with your irrigation management company.
                They paste this key into their Flux Irrigation add-on to connect to your system.
            </p>

            <!-- Connection Mode Selection -->
            <div class="form-group">
                <label>Connection Method</label>
                <div style="display:flex;gap:12px;margin-bottom:8px;">
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:14px;padding:10px 16px;border:2px solid #ddd;border-radius:8px;flex:1;" id="modeNabuLabel">
                        <input type="radio" name="connMode" value="nabu_casa" checked onchange="toggleConnectionMode()">
                        <div>
                            <strong>Nabu Casa</strong> <span style="color:#27ae60;font-size:12px;">(Recommended)</span><br>
                            <span style="font-size:12px;color:#888;">Works with your existing Nabu Casa subscription. No extra setup needed.</span>
                        </div>
                    </label>
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:14px;padding:10px 16px;border:2px solid #ddd;border-radius:8px;flex:1;" id="modeDirectLabel">
                        <input type="radio" name="connMode" value="direct" onchange="toggleConnectionMode()">
                        <div>
                            <strong>Direct Connection</strong><br>
                            <span style="font-size:12px;color:#888;">Requires port forwarding, Cloudflare Tunnel, or VPN.</span>
                        </div>
                    </label>
                </div>
            </div>

            <!-- Nabu Casa Mode Fields -->
            <div id="nabuCasaFields">
                <div class="form-group">
                    <label>Your Nabu Casa URL</label>
                    <input type="text" id="homeownerUrl" placeholder="https://xxxxxxxx.ui.nabu.casa">
                    <p style="font-size:12px; color:#999; margin-top:4px;">
                        Find this in HA: <strong>Settings &rarr; Home Assistant Cloud &rarr; Remote Control</strong>. Copy the URL shown there.
                    </p>
                </div>
                <div class="form-group">
                    <label>Home Assistant Long-Lived Access Token</label>
                    <input type="password" id="haToken" placeholder="Paste your HA token here">
                    <p style="font-size:12px; color:#999; margin-top:4px;">
                        Create one in HA: Go to your <strong>Profile</strong> (click your name, bottom-left) &rarr; scroll to
                        <strong>Long-Lived Access Tokens</strong> &rarr; <strong>Create Token</strong>. Name it "Irrigation Management" and paste it above.
                    </p>
                </div>
                <div style="background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;padding:12px;margin-bottom:16px;font-size:13px;">
                    <strong style="color:#1a7a4c;">&#9989; One-time setup required</strong><br>
                    <span style="color:#555;">
                        After generating the connection key, add this to your HA <strong>configuration.yaml</strong>
                        (if not already present):<br>
                        <code style="background:#f0f0f0;padding:2px 6px;border-radius:3px;display:inline-block;margin-top:4px;">homeassistant:</code><br>
                        <code style="background:#f0f0f0;padding:2px 6px;border-radius:3px;display:inline-block;margin-left:16px;">packages: !include_dir_named packages</code><br>
                        <span style="font-size:11px;color:#888;margin-top:4px;display:block;">Then restart Home Assistant once. The add-on automatically creates the needed proxy configuration.</span>
                    </span>
                </div>
            </div>

            <!-- Direct Mode Fields -->
            <div id="directFields" style="display:none;">
                <div class="form-group">
                    <label>Your External API URL</label>
                    <div style="display:flex;gap:8px;align-items:flex-start;">
                        <input type="text" id="homeownerUrlDirect" placeholder="https://your-domain.duckdns.org:8099" style="flex:1;">
                        <button class="btn btn-secondary btn-sm" onclick="testExternalUrl()" style="white-space:nowrap;margin-top:2px;">Test URL</button>
                    </div>
                    <div id="urlTestResult" style="font-size:12px;margin-top:4px;display:none;"></div>
                    <p style="font-size:12px; color:#999; margin-top:4px;">
                        Port 8099 must be accessible externally. Options:<br>
                        &bull; <strong>Port forwarding</strong> on your router + DuckDNS for dynamic DNS<br>
                        &bull; <strong>Cloudflare Tunnel</strong> pointing to <code style="background:#f0f0f0;padding:1px 4px;border-radius:3px;">localhost:8099</code><br>
                        &bull; <strong>Tailscale / WireGuard</strong> VPN between both HA instances<br><br>
                        Make sure the port is enabled in the add-on Configuration tab under "Network".
                    </p>
                </div>
            </div>
            <div class="form-group">
                <label>Property Label (optional)</label>
                <input type="text" id="homeownerLabel" placeholder="e.g., Smith Residence">
            </div>
            <div class="form-group">
                <label>Street Address</label>
                <input type="text" id="homeownerAddress" placeholder="e.g., 123 Main Street">
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>City</label>
                    <input type="text" id="homeownerCity" placeholder="e.g., Springfield">
                </div>
                <div class="form-group">
                    <label>State</label>
                    <input type="text" id="homeownerState" placeholder="e.g., IL">
                </div>
            </div>
            <div class="form-group" style="max-width:200px;">
                <label>ZIP Code</label>
                <input type="text" id="homeownerZip" placeholder="e.g., 62704">
            </div>
            <div id="zoneCountInfo" class="device-info" style="margin-bottom:16px;display:none;">
                <strong>Enabled Zones:</strong> <span id="zoneCountValue">0</span>
                <span style="font-size:12px;color:#999;margin-left:8px;">(auto-detected from selected device)</span>
            </div>
            <button class="btn btn-primary" onclick="generateConnectionKey()">Generate Connection Key</button>

            <div id="connectionKeyDisplay" class="new-key-display" style="display:none;">
                <strong>Connection Key</strong>
                <code id="connectionKeyValue" style="font-size:13px;"></code>
                <p class="warning">Share this key with your management company. They paste it into their Flux Irrigation add-on.</p>
                <button class="btn btn-secondary btn-sm" onclick="copyConnectionKey()">Copy to Clipboard</button>
            </div>
        </div>
    </div>

    <!-- General Settings -->
    <div class="card">
        <div class="card-header">
            <h2>General Settings</h2>
        </div>
        <div class="card-body">
            <div class="form-row">
                <div class="form-group">
                    <label>Rate Limit (requests/min)</label>
                    <input type="number" id="rateLimit" min="1" max="300" value="60">
                </div>
                <div class="form-group">
                    <label>Log Retention (days)</label>
                    <input type="number" id="logRetention" min="1" max="365" value="30">
                </div>
            </div>
            <div class="form-group" style="display:flex; align-items:center; gap:12px;">
                <label style="margin:0;">Enable Audit Log</label>
                <label class="toggle-switch">
                    <input type="checkbox" id="auditLogEnabled" checked>
                    <span class="toggle-slider"></span>
                </label>
            </div>
            <button class="btn btn-primary" onclick="saveGeneralSettings()">Save Settings</button>
        </div>
    </div>

    <!-- API Docs Link -->
    <div class="card">
        <div class="card-body" style="text-align:center; padding: 24px;">
            <p style="margin-bottom:12px;">Interactive API documentation for management companies:</p>
            <a id="docsLink" href="/api/docs" target="_blank" class="btn btn-primary">Open API Docs (Swagger UI)</a>
        </div>
    </div>

</div>

<div class="toast" id="toast"></div>

<script>
    const BASE = (window.location.pathname.replace(/\\/+$/, '')) + '/api';

    // --- Toast ---
    function showToast(msg, type = 'success') {
        const t = document.getElementById('toast');
        t.textContent = msg;
        t.className = `toast ${type} visible`;
        setTimeout(() => t.classList.remove('visible'), 3000);
    }

    // --- Load Settings ---
    async function loadSettings() {
        try {
            const res = await fetch(`${BASE}/settings`);
            const data = await res.json();

            document.getElementById('rateLimit').value = data.rate_limit_per_minute || 60;
            document.getElementById('logRetention').value = data.log_retention_days || 30;
            document.getElementById('auditLogEnabled').checked = data.enable_audit_log !== false;

            renderApiKeys(data.api_keys || []);

            // Load devices and set current selection
            await loadDevices(data.irrigation_device_id || '');

            // Show resolved entities if device is selected
            if (data.irrigation_device_id) {
                await loadDeviceEntities();
            }
        } catch (e) {
            showToast('Failed to load settings', 'error');
        }
    }

    // --- Status ---
    // Derive the ingress base path (strip /admin from the end of current path)
    const INGRESS_BASE = window.location.pathname.replace(/\\/admin\\/?$/, '');

    async function loadStatus() {
        try {
            const res = await fetch(INGRESS_BASE + '/api/system/health');
            const data = await res.json();
            const dot = document.getElementById('statusDot');
            const text = document.getElementById('statusText');
            if (data.ha_connected) {
                dot.className = 'status-dot green';
                text.textContent = 'Connected to Home Assistant';
            } else {
                dot.className = 'status-dot red';
                text.textContent = 'Home Assistant disconnected';
            }
        } catch (e) {
            document.getElementById('statusDot').className = 'status-dot red';
            document.getElementById('statusText').textContent = 'API not responding';
        }
    }

    // --- Device Selection ---
    async function loadDevices(selectedId) {
        try {
            const res = await fetch(`${BASE}/devices`);
            const devices = await res.json();
            const select = document.getElementById('deviceSelect');

            // Preserve current selection if not passed
            if (selectedId === undefined) {
                selectedId = select.value;
            }

            select.innerHTML = '<option value="">-- Select your irrigation controller --</option>';
            for (const device of devices) {
                const label = device.manufacturer || device.model
                    ? `${device.name} (${[device.manufacturer, device.model].filter(Boolean).join(' ')})`
                    : device.name;
                const opt = document.createElement('option');
                opt.value = device.id;
                opt.textContent = label;
                if (device.id === selectedId) opt.selected = true;
                select.appendChild(opt);
            }
        } catch (e) {
            showToast('Failed to load devices', 'error');
        }
    }

    async function onDeviceChange() {
        const deviceId = document.getElementById('deviceSelect').value;
        if (!deviceId) {
            document.getElementById('deviceEntities').innerHTML =
                '<div class="device-info empty">Select your irrigation controller device above to configure which entities are exposed through the API.</div>';
            return;
        }

        try {
            const res = await fetch(`${BASE}/device`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ device_id: deviceId }),
            });
            const data = await res.json();

            if (data.success) {
                renderDeviceEntities(data.zones || [], data.sensors || [], data.other || []);
                showToast('Device selected — entities resolved');
            }
        } catch (e) {
            showToast('Failed to select device', 'error');
        }
    }

    async function loadDeviceEntities() {
        try {
            const res = await fetch(`${BASE}/device/entities`);
            const data = await res.json();
            if (data.device_id) {
                renderDeviceEntities(data.zones || [], data.sensors || [], data.other || []);
            }
        } catch (e) {
            // Silently fail — device might not be configured yet
        }
    }

    function renderDeviceEntities(zones, sensors, other) {
        const container = document.getElementById('deviceEntities');
        const total = zones.length + sensors.length + (other ? other.length : 0);

        if (total === 0) {
            container.innerHTML = '<div class="device-info empty">No entities found on this device. Make sure the device has switch, valve, or sensor entities.<br><a href="' + BASE + '/device/debug" target="_blank" style="color:#1a7a4c;font-size:12px;">View debug info</a></div>';
            return;
        }

        let html = '';

        if (zones.length > 0) {
            html += '<div class="entity-list"><h4>Zones — switches & valves (' + zones.length + ')</h4>';
            for (const z of zones) {
                html += `<div class="entity-item"><span class="entity-id">${escHtml(z.entity_id)}</span><span class="entity-name">${escHtml(z.name || z.original_name || '')}</span></div>`;
            }
            html += '</div>';
        }

        if (sensors.length > 0) {
            html += '<div class="entity-list" style="margin-top:8px;"><h4>Sensors (' + sensors.length + ')</h4>';
            for (const s of sensors) {
                html += `<div class="entity-item"><span class="entity-id">${escHtml(s.entity_id)}</span><span class="entity-name">${escHtml(s.name || s.original_name || '')}</span></div>`;
            }
            html += '</div>';
        }

        if (other && other.length > 0) {
            html += '<div class="entity-list" style="margin-top:8px;"><h4>Other Entities (' + other.length + ')</h4>';
            for (const o of other) {
                html += `<div class="entity-item"><span class="entity-id">${escHtml(o.entity_id)}</span><span class="entity-name">${escHtml(o.name || o.original_name || '')}</span></div>`;
            }
            html += '</div>';
        }

        container.innerHTML = html;
    }

    // --- API Keys ---
    function renderApiKeys(keys) {
        const container = document.getElementById('apiKeysList');
        if (keys.length === 0) {
            container.innerHTML = '<p style="color:#999; text-align:center; padding:20px;">No API keys configured. Create one to get started.</p>';
            return;
        }
        container.innerHTML = keys.map((key, i) => `
            <div class="api-key-card">
                <div class="api-key-header">
                    <div>
                        <span class="api-key-name">${escHtml(key.name)}</span>
                        <span class="api-key-preview">${escHtml(key.key_preview)}</span>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-secondary btn-sm" onclick="regenerateKey(${i})">Regenerate</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteKey(${i}, '${escHtml(key.name)}')">Delete</button>
                    </div>
                </div>
                <div class="permissions-grid">
                    ${['zones.read','zones.control','schedule.read','schedule.write','sensors.read','history.read','system.control'].map(p => `
                        <label class="perm-checkbox">
                            <input type="checkbox" ${(key.permissions||[]).includes(p) ? 'checked' : ''} onchange="updateKeyPermissions(${i})">
                            ${p.replace('.', ': ').replace(/\\b\\w/g, c => c.toUpperCase())}
                        </label>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }

    function showCreateKey() { document.getElementById('newKeyForm').style.display = 'block'; }
    function hideCreateKey() { document.getElementById('newKeyForm').style.display = 'none'; }

    async function createKey() {
        const name = document.getElementById('newKeyName').value.trim();
        if (!name) { showToast('Enter a company name', 'error'); return; }

        const perms = [...document.querySelectorAll('#newKeyPermissions input:checked')].map(c => c.value);

        try {
            const res = await fetch(`${BASE}/keys`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name, permissions: perms }),
            });
            const data = await res.json();
            if (data.success) {
                document.getElementById('newKeyValue').textContent = data.key;
                document.getElementById('newKeyDisplay').style.display = 'block';
                document.getElementById('newKeyName').value = '';
                hideCreateKey();
                loadSettings();
                showToast(`API key created for ${name}`);
            }
        } catch (e) {
            showToast('Failed to create key', 'error');
        }
    }

    function copyKey() {
        const key = document.getElementById('newKeyValue').textContent;
        navigator.clipboard.writeText(key).then(() => showToast('Key copied!'));
    }

    async function deleteKey(index, name) {
        if (!confirm(`Delete API key for "${name}"? This will immediately revoke their access.`)) return;
        try {
            await fetch(`${BASE}/keys/${index}`, { method: 'DELETE' });
            loadSettings();
            showToast(`API key for ${name} deleted`);
        } catch (e) {
            showToast('Failed to delete key', 'error');
        }
    }

    async function regenerateKey(index) {
        if (!confirm('Regenerate this API key? The old key will stop working immediately.')) return;
        try {
            const res = await fetch(`${BASE}/keys/${index}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ regenerate_key: true }),
            });
            const data = await res.json();
            if (data.key) {
                document.getElementById('newKeyValue').textContent = data.key;
                document.getElementById('newKeyDisplay').style.display = 'block';
                showToast('Key regenerated');
            }
        } catch (e) {
            showToast('Failed to regenerate key', 'error');
        }
    }

    async function updateKeyPermissions(index) {
        const card = document.querySelectorAll('.api-key-card')[index];
        const checked = [...card.querySelectorAll('input[type=checkbox]')];
        const allPerms = ['zones.read','zones.control','schedule.read','schedule.write','sensors.read','history.read','system.control'];
        const selectedPerms = allPerms.filter((_, i) => checked[i]?.checked);

        try {
            await fetch(`${BASE}/keys/${index}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ permissions: selectedPerms }),
            });
            showToast('Permissions updated');
        } catch (e) {
            showToast('Failed to update permissions', 'error');
        }
    }

    // --- General ---
    async function saveGeneralSettings() {
        try {
            await fetch(`${BASE}/general`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    rate_limit_per_minute: parseInt(document.getElementById('rateLimit').value),
                    log_retention_days: parseInt(document.getElementById('logRetention').value),
                    enable_audit_log: document.getElementById('auditLogEnabled').checked,
                }),
            });
            showToast('Settings saved');
        } catch (e) {
            showToast('Failed to save settings', 'error');
        }
    }

    function escHtml(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }

    // --- Connection Key ---
    function getConnectionMode() {
        const radios = document.querySelectorAll('input[name="connMode"]');
        for (const r of radios) { if (r.checked) return r.value; }
        return 'nabu_casa';
    }

    function toggleConnectionMode() {
        const mode = getConnectionMode();
        document.getElementById('nabuCasaFields').style.display = mode === 'nabu_casa' ? 'block' : 'none';
        document.getElementById('directFields').style.display = mode === 'direct' ? 'block' : 'none';
        // Highlight selected radio card
        document.getElementById('modeNabuLabel').style.borderColor = mode === 'nabu_casa' ? '#2ecc71' : '#ddd';
        document.getElementById('modeDirectLabel').style.borderColor = mode === 'direct' ? '#2ecc71' : '#ddd';
    }

    function getEffectiveUrl() {
        const mode = getConnectionMode();
        if (mode === 'nabu_casa') return document.getElementById('homeownerUrl').value.trim();
        return document.getElementById('homeownerUrlDirect').value.trim();
    }

    async function loadConnectionKey() {
        try {
            const res = await fetch(`${BASE}/connection-key`);
            const data = await res.json();
            // Set connection mode
            if (data.connection_mode === 'direct') {
                const directRadio = document.querySelector('input[name="connMode"][value="direct"]');
                if (directRadio) directRadio.checked = true;
                if (data.url) document.getElementById('homeownerUrlDirect').value = data.url;
            } else {
                const nabuRadio = document.querySelector('input[name="connMode"][value="nabu_casa"]');
                if (nabuRadio) nabuRadio.checked = true;
                if (data.url) document.getElementById('homeownerUrl').value = data.url;
            }
            toggleConnectionMode();
            if (data.ha_token_set) document.getElementById('haToken').value = '********';
            if (data.label) document.getElementById('homeownerLabel').value = data.label;
            if (data.address) document.getElementById('homeownerAddress').value = data.address;
            if (data.city) document.getElementById('homeownerCity').value = data.city;
            if (data.state) document.getElementById('homeownerState').value = data.state;
            if (data.zip) document.getElementById('homeownerZip').value = data.zip;
            if (data.zone_count !== null && data.zone_count !== undefined) {
                document.getElementById('zoneCountValue').textContent = data.zone_count;
                document.getElementById('zoneCountInfo').style.display = 'block';
            }
            if (data.connection_key) {
                document.getElementById('connectionKeyValue').textContent = data.connection_key;
                document.getElementById('connectionKeyDisplay').style.display = 'block';
            }
        } catch(e) { /* first time, no key yet */ }
    }

    async function testExternalUrl() {
        const url = document.getElementById('homeownerUrlDirect').value.trim();
        const resultEl = document.getElementById('urlTestResult');
        if (!url) { showToast('Enter a URL first', 'error'); return; }

        resultEl.style.display = 'block';
        resultEl.innerHTML = '<span style="color:#666;">Testing: ' + escHtml(url) + '/api/system/health ...</span>';
        try {
            const res = await fetch(`${BASE}/test-url`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url }),
            });
            const data = await res.json();
            if (data.success) {
                resultEl.innerHTML = '<span style="color:#27ae60;">&#10004; ' + escHtml(data.message) + ' (HTTP ' + data.status_code + ')</span>';
            } else {
                resultEl.innerHTML = '<span style="color:#e74c3c;">&#10008; ' + escHtml(data.error) + '</span>' +
                    (data.help ? '<br><span style="color:#999;font-size:11px;">' + escHtml(data.help) + '</span>' : '');
            }
        } catch(e) {
            resultEl.innerHTML = '<span style="color:#e74c3c;">&#10008; Test failed: ' + escHtml(e.message) + '</span>';
        }
    }

    async function generateConnectionKey() {
        const mode = getConnectionMode();
        const url = getEffectiveUrl();
        if (!url) { showToast('Enter your URL', 'error'); return; }

        const ha_token = mode === 'nabu_casa' ? document.getElementById('haToken').value.trim() : '';
        if (mode === 'nabu_casa' && (!ha_token || ha_token === '********')) {
            if (!ha_token) { showToast('Enter your HA Long-Lived Access Token', 'error'); return; }
        }

        const label = document.getElementById('homeownerLabel').value.trim();
        const address = document.getElementById('homeownerAddress').value.trim();
        const city = document.getElementById('homeownerCity').value.trim();
        const state = document.getElementById('homeownerState').value.trim();
        const zip = document.getElementById('homeownerZip').value.trim();

        const body = { url, label, address, city, state, zip, connection_mode: mode };
        if (mode === 'nabu_casa' && ha_token && ha_token !== '********') {
            body.ha_token = ha_token;
        }

        try {
            const res = await fetch(`${BASE}/connection-key`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (data.connection_key) {
                document.getElementById('connectionKeyValue').textContent = data.connection_key;
                document.getElementById('connectionKeyDisplay').style.display = 'block';
                if (data.zone_count !== null && data.zone_count !== undefined) {
                    document.getElementById('zoneCountValue').textContent = data.zone_count;
                    document.getElementById('zoneCountInfo').style.display = 'block';
                }
                showToast('Connection key generated' + (mode === 'nabu_casa' ? ' (Nabu Casa mode)' : ''));
                loadSettings();
            }
        } catch(e) { showToast('Failed to generate key', 'error'); }
    }

    function copyConnectionKey() {
        const key = document.getElementById('connectionKeyValue').textContent;
        navigator.clipboard.writeText(key).then(() => showToast('Connection key copied!'));
    }

    // --- Mode Switch ---
    async function switchToManagement() {
        if (!confirm('Switch to Management mode? The homeowner settings will no longer be available until you switch back.')) return;
        try {
            await fetch(`${BASE}/mode`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ mode: 'management' }),
            });
            showToast('Switching to management mode...');
            setTimeout(() => window.location.reload(), 1000);
        } catch(e) { showToast(e.message, 'error'); }
    }

    // --- Init ---
    // Fix docs link for ingress
    document.getElementById('docsLink').href = INGRESS_BASE + '/api/docs';
    loadSettings();
    loadConnectionKey();
    loadStatus();
    setInterval(loadStatus, 30000);
</script>
</body>
</html>
"""
