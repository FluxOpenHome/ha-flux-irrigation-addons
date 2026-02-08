"""
Admin settings endpoints and web UI.
Allows the homeowner to configure API keys, device selection,
and permissions through the add-on's ingress panel.
"""

import json
import os
import secrets
import httpx
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
from config import get_config, reload_config
from config_changelog import log_change


router = APIRouter(prefix="/admin", tags=["Admin"])

OPTIONS_FILE = "/data/options.json"


def _load_options() -> dict:
    """Load current options from persistent storage."""
    if os.path.exists(OPTIONS_FILE):
        with open(OPTIONS_FILE, "r") as f:
            return json.load(f)
    return {}


async def _save_options(options: dict):
    """Save options to persistent storage, persist to Supervisor, and reload config.

    We write to both:
      1. /data/options.json — for immediate runtime use
      2. Supervisor API (POST /addons/self/options) — so settings survive add-on rebuilds

    The HA Supervisor controls /data/options.json on add-on start. If we only write
    to the local file, a rebuild/restart wipes our changes back to the Supervisor's
    stored values. By pushing to the Supervisor API, we ensure persistence.
    """
    # 1. Write to local file for immediate use
    os.makedirs(os.path.dirname(OPTIONS_FILE), exist_ok=True)
    with open(OPTIONS_FILE, "w") as f:
        json.dump(options, f, indent=2)

    # 2. Push to Supervisor API so settings survive rebuilds
    #    The Supervisor validates options against config.yaml schema and rejects
    #    unknown fields. Filter to only known schema fields to prevent one unknown
    #    field from torpedoing the entire save (which would lose API keys etc.).
    _KNOWN_SCHEMA_KEYS = {
        "mode", "homeowner_url", "homeowner_label", "homeowner_address",
        "homeowner_city", "homeowner_state", "homeowner_zip", "homeowner_phone",
        "homeowner_first_name", "homeowner_last_name", "homeowner_ha_token",
        "homeowner_connection_mode", "api_keys", "irrigation_device_id",
        "rate_limit_per_minute", "log_retention_days", "enable_audit_log",
        "connection_revoked", "weather_entity_id", "weather_enabled",
        "weather_check_interval_minutes",
    }
    supervisor_token = os.environ.get("SUPERVISOR_TOKEN")
    if supervisor_token:
        try:
            # Only send fields the Supervisor schema knows about
            safe_options = {k: v for k, v in options.items() if k in _KNOWN_SCHEMA_KEYS}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "http://supervisor/addons/self/options",
                    headers={
                        "Authorization": f"Bearer {supervisor_token}",
                        "Content-Type": "application/json",
                    },
                    json={"options": safe_options},
                )
                if resp.status_code == 200:
                    print(f"[ADMIN] ✓ Options persisted to Supervisor API")
                else:
                    print(f"[ADMIN] ✗ Supervisor API returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[ADMIN] ✗ Failed to persist options to Supervisor: {type(e).__name__}: {e}")
    else:
        print(f"[ADMIN] ⚠ No SUPERVISOR_TOKEN — options saved locally only (may not survive rebuild)")

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
    log_retention_days: Optional[int] = Field(None, ge=1, le=730)
    enable_audit_log: Optional[bool] = None
    weather_entity_id: Optional[str] = None
    weather_enabled: Optional[bool] = None
    weather_check_interval_minutes: Optional[int] = Field(None, ge=5, le=60)


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
        "allowed_control_entities": config.allowed_control_entities,
        "rate_limit_per_minute": options.get("rate_limit_per_minute", 60),
        "log_retention_days": options.get("log_retention_days", 365),
        "enable_audit_log": options.get("enable_audit_log", True),
        "homeowner_url": options.get("homeowner_url", ""),
        "homeowner_label": options.get("homeowner_label", ""),
        "homeowner_address": options.get("homeowner_address", ""),
        "homeowner_city": options.get("homeowner_city", ""),
        "homeowner_state": options.get("homeowner_state", ""),
        "homeowner_zip": options.get("homeowner_zip", ""),
        "homeowner_phone": options.get("homeowner_phone", ""),
        "homeowner_first_name": options.get("homeowner_first_name", ""),
        "homeowner_last_name": options.get("homeowner_last_name", ""),
        "weather_entity_id": options.get("weather_entity_id", ""),
        "weather_enabled": options.get("weather_enabled", False),
        "weather_check_interval_minutes": options.get("weather_check_interval_minutes", 15),
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
async def list_devices(show_all: bool = False):
    """List Home Assistant devices for selection.

    By default, filters to likely irrigation controllers (matching keywords
    like 'flux', 'open home', 'irrigation', 'sprinkler', or 'esphome').
    Pass ?show_all=true to return every device.
    """
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

    # Keywords that indicate an irrigation controller
    IRRIGATION_KEYWORDS = [
        "flux", "open home", "irrigation", "sprinkler", "esphome",
        "rain", "valve", "watering", "lawn", "garden",
    ]

    def _is_irrigation_device(name: str, manufacturer: str, model: str) -> bool:
        """Check if any device field contains an irrigation-related keyword."""
        searchable = f"{name} {manufacturer} {model}".lower()
        return any(kw in searchable for kw in IRRIGATION_KEYWORDS)

    # Build full device list
    all_devices = []
    for device in devices:
        name = device.get("name_by_user") or device.get("name") or ""
        manufacturer = device.get("manufacturer") or ""
        model = device.get("model") or ""

        if not name:
            continue

        all_devices.append({
            "id": device.get("id", ""),
            "name": name,
            "manufacturer": manufacturer,
            "model": model,
            "area_id": device.get("area_id", ""),
        })

    if show_all:
        result = all_devices
    else:
        # Filter to irrigation-related devices
        result = [d for d in all_devices if _is_irrigation_device(
            d["name"], d["manufacturer"], d["model"]
        )]
        # If the currently selected device isn't in the filtered list, include it
        # so the dropdown doesn't lose its selection
        if config.irrigation_device_id:
            selected_ids = {d["id"] for d in result}
            if config.irrigation_device_id not in selected_ids:
                for d in all_devices:
                    if d["id"] == config.irrigation_device_id:
                        result.append(d)
                        break

    # Sort by name for display
    result.sort(key=lambda d: d["name"].lower())
    return {"devices": result, "total_count": len(all_devices), "filtered": not show_all}


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

    log_change("Homeowner", "Device Config", f"Selected device: {body.device_id}")

    return {
        "success": True,
        "device_id": body.device_id,
        "zones": entities.get("zones", []),
        "sensors": entities.get("sensors", []),
        "other": entities.get("other", []),
        "allowed_zone_entities": config.allowed_zone_entities,
        "allowed_sensor_entities": config.allowed_sensor_entities,
        "allowed_control_entities": config.allowed_control_entities,
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
        "allowed_control_entities": config.allowed_control_entities,
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

    changes = []
    if body.rate_limit_per_minute is not None:
        old = options.get("rate_limit_per_minute", 60)
        if old != body.rate_limit_per_minute:
            changes.append(f"Rate limit: {old} -> {body.rate_limit_per_minute}/min")
        options["rate_limit_per_minute"] = body.rate_limit_per_minute
    if body.log_retention_days is not None:
        old = options.get("log_retention_days", 365)
        if old != body.log_retention_days:
            changes.append(f"Log retention: {old} -> {body.log_retention_days} days")
        options["log_retention_days"] = body.log_retention_days
    if body.enable_audit_log is not None:
        old = options.get("enable_audit_log", True)
        if old != body.enable_audit_log:
            changes.append(f"Audit log: {'Enabled' if body.enable_audit_log else 'Disabled'}")
        options["enable_audit_log"] = body.enable_audit_log
    if body.weather_entity_id is not None:
        old = options.get("weather_entity_id", "")
        if old != body.weather_entity_id:
            changes.append(f"Weather entity: {old or '(none)'} -> {body.weather_entity_id or '(none)'}")
        options["weather_entity_id"] = body.weather_entity_id
    if body.weather_enabled is not None:
        old = options.get("weather_enabled", False)
        if old != body.weather_enabled:
            changes.append(f"Weather: {'Enabled' if body.weather_enabled else 'Disabled'}")
        options["weather_enabled"] = body.weather_enabled
    if body.weather_check_interval_minutes is not None:
        old = options.get("weather_check_interval_minutes", 15)
        if old != body.weather_check_interval_minutes:
            changes.append(f"Weather check interval: {old} -> {body.weather_check_interval_minutes} min")
        options["weather_check_interval_minutes"] = body.weather_check_interval_minutes

    await _save_options(options)

    if changes:
        for change in changes:
            log_change("Homeowner", "Device Config", change)

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
    phone: str = Field("", max_length=20, description="Homeowner phone number")
    first_name: str = Field("", max_length=50, description="Homeowner first name")
    last_name: str = Field("", max_length=50, description="Homeowner last name")
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

    # Validate URL before saving
    url = body.url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        raise HTTPException(
            status_code=400,
            detail=f"URL must start with http:// or https:// — got: '{url[:50]}'. "
                   f"Please enter your full Nabu Casa URL (e.g., https://xxxxxxxx.ui.nabu.casa) "
                   f"or direct URL (e.g., http://your-ip:8099).",
        )

    options = _load_options()

    # Track contact/address changes for changelog
    contact_changes = []
    contact_fields = {
        "homeowner_url": ("URL", url),
        "homeowner_label": ("Property label", body.label),
        "homeowner_address": ("Address", body.address),
        "homeowner_city": ("City", body.city),
        "homeowner_state": ("State", body.state),
        "homeowner_zip": ("ZIP", body.zip),
        "homeowner_phone": ("Phone", body.phone),
        "homeowner_first_name": ("First name", body.first_name),
        "homeowner_last_name": ("Last name", body.last_name),
        "homeowner_connection_mode": ("Connection mode", body.connection_mode),
    }
    for opt_key, (label, new_val) in contact_fields.items():
        old_val = options.get(opt_key, "")
        if old_val != new_val:
            contact_changes.append(f"{label}: {old_val or '(empty)'} -> {new_val or '(empty)'}")

    options["homeowner_url"] = url
    options["homeowner_label"] = body.label
    options["homeowner_address"] = body.address
    options["homeowner_city"] = body.city
    options["homeowner_state"] = body.state
    options["homeowner_zip"] = body.zip
    options["homeowner_phone"] = body.phone
    options["homeowner_first_name"] = body.first_name
    options["homeowner_last_name"] = body.last_name
    options["homeowner_connection_mode"] = body.connection_mode

    # Clear revoked flag — generating a new key means access is being restored
    options["connection_revoked"] = False

    # Preserve existing HA token if not provided (UI sends empty when unchanged)
    effective_ha_token = body.ha_token.strip() if body.ha_token else ""
    if effective_ha_token:
        options["homeowner_ha_token"] = effective_ha_token
    else:
        # Keep whatever was already saved
        effective_ha_token = options.get("homeowner_ha_token", "")

    print(f"[ADMIN] generate_connection_key: mode={body.connection_mode}, url={url}, ha_token={'SET('+str(len(effective_ha_token))+'chars)' if effective_ha_token else 'EMPTY'}")

    # Validate HA token for Nabu Casa mode — a real HA Long-Lived Access Token
    # is typically 180+ characters. If it's too short, it's corrupted or missing.
    if body.connection_mode == "nabu_casa":
        if not effective_ha_token:
            raise HTTPException(
                status_code=400,
                detail="Nabu Casa mode requires a Home Assistant Long-Lived Access Token. "
                       "Go to your HA Profile → Long-Lived Access Tokens → Create Token, "
                       "then paste it in the HA Token field.",
            )
        if len(effective_ha_token) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"The saved HA token is only {len(effective_ha_token)} characters — "
                       f"a valid Long-Lived Access Token is typically 180+ characters. "
                       f"Please re-enter your full HA token. Go to your HA Profile → "
                       f"Long-Lived Access Tokens → Create Token, then paste it in the HA Token field.",
            )

    # Auto-detect zone count from selected device
    zone_count = len(config.allowed_zone_entities) if config.allowed_zone_entities else None

    # Find or create a dedicated management company key.
    # Always generate a fresh random key — this ensures that after a revoke
    # (which deletes the old key), the new connection key works even if the
    # Supervisor restored stale options on rebuild.
    existing_keys = options.get("api_keys", [])
    mgmt_key_name = "Management Company (Connection Key)"

    # Full permission set for management company keys
    full_mgmt_permissions = [
        "zones.read", "zones.control", "schedule.read",
        "schedule.write", "sensors.read", "entities.read",
        "entities.control", "history.read", "system.control",
    ]

    # Remove any existing management key — we'll create a fresh one
    existing_keys = [k for k in existing_keys if k.get("name") != mgmt_key_name]

    mgmt_key = secrets.token_urlsafe(32)
    existing_keys.append({
        "key": mgmt_key,
        "name": mgmt_key_name,
        "permissions": full_mgmt_permissions,
    })
    options["api_keys"] = existing_keys
    print(f"[ADMIN] Generated fresh management API key")

    await _save_options(options)

    key_data = ConnectionKeyData(
        url=url,
        key=mgmt_key,
        label=body.label,
        address=body.address or None,
        city=body.city or None,
        state=body.state or None,
        zip=body.zip or None,
        phone=body.phone or None,
        first_name=body.first_name or None,
        last_name=body.last_name or None,
        zone_count=zone_count,
        ha_token=effective_ha_token or None,
        mode=body.connection_mode or "direct",
    )
    encoded = encode_connection_key(key_data)

    log_change("Homeowner", "Connection Key", "Generated new connection key")
    for change in contact_changes:
        log_change("Homeowner", "Connection Key", change)

    return {
        "success": True,
        "connection_key": encoded,
        "url": url,
        "label": body.label,
        "address": body.address,
        "city": body.city,
        "state": body.state,
        "zip": body.zip,
        "phone": body.phone,
        "first_name": body.first_name,
        "last_name": body.last_name,
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


@router.post("/api/revoke-access", summary="Revoke management company access")
async def revoke_management_access():
    """Revoke management company access by deleting the management API key.

    This immediately prevents the management company from accessing this
    homeowner's irrigation system. The connection key becomes invalid.
    The homeowner can re-generate a new connection key later if needed.
    """
    config = get_config()
    if config.mode != "homeowner":
        raise HTTPException(
            status_code=400,
            detail="This endpoint is only available in homeowner mode.",
        )

    options = _load_options()
    existing_keys = options.get("api_keys", [])

    mgmt_key_name = "Management Company (Connection Key)"
    original_count = len(existing_keys)
    options["api_keys"] = [k for k in existing_keys if k.get("name") != mgmt_key_name]
    removed_count = original_count - len(options["api_keys"])

    if removed_count == 0:
        raise HTTPException(
            status_code=404,
            detail="No management company access to revoke.",
        )

    # Clear the stored connection key URL so the old key is fully invalidated
    # and the homeowner must generate a fresh one. Keep HA token and other
    # settings (name, address, etc.) so they don't have to re-enter them.
    options["homeowner_url"] = ""

    # Set explicit revoked flag so the /api/system/health endpoint signals
    # the management company immediately (no auth required to read this)
    options["connection_revoked"] = True

    await _save_options(options)

    print(f"[ADMIN] Management company access REVOKED — removed {removed_count} API key(s), cleared connection key URL")

    log_change("Homeowner", "Connection Key", "Revoked management access")

    return {
        "success": True,
        "message": "Management company access has been revoked. They can no longer access your irrigation system. Generate a new connection key to re-enable access.",
        "keys_removed": removed_count,
    }


@router.get("/api/geocode", summary="Geocode an address")
async def admin_geocode(q: str = Query(..., min_length=3, description="Address to geocode")):
    """Proxy geocoding via Nominatim so the browser doesn't need cross-origin access."""
    import httpx as _httpx
    try:
        async with _httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"format": "json", "limit": "1", "q": q},
                headers={"User-Agent": "FluxIrrigationAPI/1.1.8"},
            )
            resp.raise_for_status()
            results = resp.json()
            if results and len(results) > 0:
                return {"lat": float(results[0]["lat"]), "lon": float(results[0]["lon"])}
            return {"lat": None, "lon": None}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Geocoding failed: {e}")


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
    phone = options.get("homeowner_phone", "")
    first_name = options.get("homeowner_first_name", "")
    last_name = options.get("homeowner_last_name", "")
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
            phone=phone or None,
            first_name=first_name or None,
            last_name=last_name or None,
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
        "phone": phone,
        "first_name": first_name,
        "last_name": last_name,
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
    # Homeowner mode: check view param
    view = request.query_params.get("view", "")
    if view == "config":
        return HTMLResponse(content=ADMIN_HTML)
    from routes.homeowner_ui import HOMEOWNER_HTML
    return HTMLResponse(content=HOMEOWNER_HTML)


ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flux Open Home — Settings</title>
    <style>
        :root {
            --bg-body: #f5f6fa;
            --bg-card: #ffffff;
            --bg-tile: #f8f9fa;
            --bg-input: #ffffff;
            --bg-weather: #f0f8ff;
            --bg-secondary-btn: #ecf0f1;
            --bg-secondary-btn-hover: #ddd;
            --bg-active-tile: #e8f5e9;
            --bg-inactive-tile: #fbe9e7;
            --bg-toast: #2c3e50;
            --bg-modal-overlay: rgba(0,0,0,0.5);
            --bg-warning: #fff3cd;
            --bg-success-light: #d4edda;
            --bg-danger-light: #f8d7da;
            --bg-new-key: #fffde7;
            --text-primary: #2c3e50;
            --text-secondary: #666;
            --text-muted: #7f8c8d;
            --text-hint: #888;
            --text-disabled: #95a5a6;
            --text-placeholder: #999;
            --text-warning: #856404;
            --text-success-dark: #155724;
            --text-danger-dark: #721c24;
            --text-warning-dark: #e65100;
            --border-light: #eee;
            --border-input: #ddd;
            --border-card: #bdc3c7;
            --border-active: #a5d6a7;
            --border-hover: #bbb;
            --border-row: #f5f5f5;
            --border-new-key: #f9a825;
            --color-primary: #2ecc71;
            --color-primary-hover: #27ae60;
            --color-accent: #2ecc71;
            --color-success: #2ecc71;
            --color-danger: #e74c3c;
            --color-danger-hover: #c0392b;
            --color-warning: #f39c12;
            --color-link: #3498db;
            --header-gradient: linear-gradient(135deg, #1a7a4c, #2ecc71);
            --shadow-card: 0 1px 3px rgba(0,0,0,0.08);
            --shadow-header: 0 2px 8px rgba(0,0,0,0.15);
            --toggle-bg: #ccc;
        }
        body.dark-mode {
            --bg-body: #1a1a2e;
            --bg-card: #16213e;
            --bg-tile: #1a1a2e;
            --bg-input: #1a1a2e;
            --bg-weather: #16213e;
            --bg-secondary-btn: #253555;
            --bg-secondary-btn-hover: #2d4068;
            --bg-active-tile: #1b3a2a;
            --bg-inactive-tile: #3a2020;
            --bg-toast: #0f3460;
            --bg-modal-overlay: rgba(0,0,0,0.7);
            --bg-warning: #3a3020;
            --bg-success-light: #1b3a2a;
            --bg-danger-light: #3a2020;
            --bg-new-key: #2a2820;
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --text-muted: #8a9bb0;
            --text-hint: #7a8a9a;
            --text-disabled: #607080;
            --text-placeholder: #607080;
            --text-warning: #d4a843;
            --text-success-dark: #6fcf97;
            --text-danger-dark: #e07a7a;
            --text-warning-dark: #f0a050;
            --border-light: #253555;
            --border-input: #304060;
            --border-card: #304060;
            --border-active: #2d7a4a;
            --border-hover: #405575;
            --border-row: #253555;
            --border-new-key: #8a7020;
            --color-primary: #2ecc71;
            --color-primary-hover: #27ae60;
            --color-accent: #2ecc71;
            --color-success: #2ecc71;
            --color-danger: #e74c3c;
            --color-danger-hover: #c0392b;
            --color-warning: #f39c12;
            --color-link: #5dade2;
            --header-gradient: linear-gradient(135deg, #0f3460, #16213e);
            --shadow-card: 0 1px 3px rgba(0,0,0,0.3);
            --shadow-header: 0 2px 8px rgba(0,0,0,0.4);
            --toggle-bg: #405575;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-body);
            color: var(--text-primary);
            line-height: 1.6;
        }
        .header {
            background: var(--header-gradient);
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
            background: var(--bg-card);
            border-radius: 12px;
            box-shadow: var(--shadow-card);
            margin-bottom: 20px;
            overflow: hidden;
        }
        .card-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-light);
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
            color: var(--text-secondary);
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border-input);
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.2s;
            background: var(--bg-input);
            color: var(--text-primary);
        }
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: var(--color-accent);
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
        .btn-primary { background: var(--color-primary); color: white; }
        .btn-primary:hover { background: var(--color-primary-hover); }
        .btn-danger { background: var(--color-danger); color: white; }
        .btn-danger:hover { background: var(--color-danger-hover); }
        .btn-secondary { background: var(--bg-secondary-btn); color: var(--text-primary); }
        .btn-secondary:hover { background: var(--bg-secondary-btn-hover); }
        .btn-sm { padding: 6px 12px; font-size: 12px; }

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
        .toast.success { background: var(--color-success); }
        .toast.error { background: var(--color-danger); }
        .toast.visible { opacity: 1; }

        .new-key-display {
            background: var(--bg-new-key);
            border: 2px solid var(--border-new-key);
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
            background: var(--bg-card);
            border-radius: 4px;
        }
        .new-key-display .warning { color: var(--text-warning-dark); font-weight: 600; font-size: 13px; }

        .entity-list {
            border: 1px solid var(--border-light);
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
        }
        .entity-list h4 {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .entity-item {
            padding: 6px 0;
            border-bottom: 1px solid var(--border-row);
            font-size: 13px;
            display: flex;
            justify-content: space-between;
        }
        .entity-item:last-child { border-bottom: none; }
        .entity-id { font-family: monospace; }
        .entity-name { color: var(--text-hint); }

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
            background: var(--toggle-bg);
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
        .toggle-switch input:checked + .toggle-slider { background: var(--color-accent); }
        .toggle-switch input:checked + .toggle-slider:before { transform: translateX(20px); }

        .status-bar {
            display: flex;
            gap: 12px;
            padding: 12px 20px;
            background: var(--bg-tile);
            border-bottom: 1px solid var(--border-light);
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
            background: var(--bg-tile);
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 12px;
            font-size: 13px;
            color: var(--text-secondary);
        }
        .device-info.empty {
            text-align: center;
            color: var(--text-placeholder);
            padding: 24px;
        }

        .dark-toggle { background: rgba(255,255,255,0.15); border: none; border-radius: 8px; cursor: pointer; font-size: 16px; padding: 4px 8px; transition: background 0.15s; line-height: 1; }
        .dark-toggle:hover { background: rgba(255,255,255,0.25); }

        /* Dark mode form inputs */
        body.dark-mode input, body.dark-mode select, body.dark-mode textarea {
            background: var(--bg-input); color: var(--text-primary); border-color: var(--border-input);
        }

        /* Responsive */
        @media (max-width: 600px) {
            .header { flex-wrap: wrap; gap: 10px; padding: 14px 16px !important; }
            .header h1 { font-size: 16px; }
            .header .subtitle { font-size: 11px; }
            .header-left { gap: 10px !important; }
            .header-left img { height: 32px !important; }
            .header-nav { width: 100%; justify-content: flex-start; flex-wrap: wrap; gap: 6px !important; }
            .header-nav a, .header-nav span, .header-nav button { font-size: 11px !important; padding: 4px 8px !important; }
            .container { padding: 12px; }
            .conn-mode-grid { grid-template-columns: 1fr !important; }
            .form-group input[type="text"], .form-group input[type="password"] { font-size: 13px; }
            .dark-toggle { font-size: 14px; padding: 3px 6px; }
        }
    </style>
    <script src="https://unpkg.com/qrcode-generator@1.4.4/qrcode.js"></script>
</head>
<body>
<script>(function(){if(localStorage.getItem('flux_dark_mode_homeowner')==='true')document.body.classList.add('dark-mode');})()</script>

<div class="header" style="display:flex;align-items:center;justify-content:space-between;">
    <div class="header-left" style="display:flex;align-items:center;gap:14px;">
        <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAARYAAABaCAYAAAB9oHnsAAAACXBIWXMAAC4jAAAuIwF4pT92AAAQnklEQVR4nO2d0XHjOBKGf1xdqaQnOwNrI7AuAnMjsDYCcyIYTQSjiWA8EZiOYDURDB3ByhGcnIH9JJVe+h7QvKEpgARIAgRlfFUslymKhEjgJ9BodAsiQiQSifTJv4cuwEdgMp1dAkgBXALIjof9btACKeAyrvjf/HjY5wMWJ6JACLEAsOR/dwA2RPQ6XIn0CFWPhStZBuDWc3l+AlgfD/tt3UGT6SwFsMbvhrqqO35oJtPZFsA1//sGIGn6jT7h570FcFXa/dfxsN+0PN8cUkhz3rULUUzHghBC1x7fAKyIKPNdpib+pdmfwb+ogK9ZW5kn09kCwANkI7gA8HkynQUrLJPpLMFvUQFkmZfqowdjgfeiAkhhaMscwFcAv3jb8nMLnsl0lk6mMypt+ZDlYVHJoW6PFwAehBCh1SetsAwhKgXVCl7l0nBfpBt93tMLAHno4jKZzpaQL62QuMf7F5OKjIdJwaATliF5GboAEScELS5crmzocpQRQmQA7gwOvQCQhyQuoQnLM8IbJkTs2UI+yyoXADK26QQDi0oOWb4qgxhHLUSl4AKy5xLEvbWZFXoEsDoe9kFaoSPhcDzsX9nAnuO0sV5D9lySEOpSg6g8o5utqRUNovIGvc3lGrLnkgw9W2TaY3k7HvZpCBUhMg541iuBbAhVCnEZ9O1qICrexc9AVBIiWgJ40hxzjQCGdKbCEszUaGQ8hCwuIxaVoi0uoR5uAsAtn2swQrOxRM6MEMUlUFFZo96mkpZEBTzUSaC+rwBwJ4QYzA0jCkvEOQbikvkqC4tYjrBEJYX0+9HxiYhO/LsMxOU7n9s7UVgiXmBxSTUf306ms8x1GRpE5Q2AdzsiN/w635lPdZ613ItJar7/IISo+9wJUVgi3uAlAp80H9+5FJeSqKiczQZZZtFVVApYXHT3FQA2vn1corBEvHI87DN4FpdzFpUCPvaL5uPCgc6bLSsKS8Q7PsXlI4hKARHdQ/qbqfAqLlFYIoNgIC7rrtcYqah86bJamYhS6MXlGr9XnDslCktkMFhcvmk+/sreu60IVFQWkIsKdTxyr6MrK+h9XK59+LhEYYkMyvGwX0P/hn3oIC51q4KXA4lKDvWMFCBFJe3jWqVpaJ243Akh+hAwLVFYIoNzPOxT9CgubKPROZt98h0dz6eoFLC4LKH3cfns0sclCkskCPoSFwNRyWzL1oUhRKWAiHaod6B7cCUuUVgiwWAgLrUhNaKonMI+LnXXuHfh4xKFJRIULC4/NR9nukBRUVT08HIA3QyckyBRUVgiIZJCHyjqJApdgKJSt3QAAJ59iUoBT2HrZuAuIL1ze/NxicISCQ5er5NALy7/lANeY2Sigvq1Pc4gojX0Q80r9OhAF4UlEiQN4mLCjwFFRTfN/QwZU2WwgGncU3IeJMo0NOXCcRqEzHcliIQPh7hMUN9YVTz6zjU1BlEpsYS+rLdCiKzrUM1UWC4A3HS5UAM3k+lsG1ISr0gYlMSlmlBNxyMbgL0xMlEBEb1yKAXdPb0TQux46NSKkIZCMTp/RAkPi3aGh2fuSnLK2ESlwMCB7msXH5eQhKVVOs9IZCgMROUFAYpKgcsgUSEIywuk9T4OgyJjo2490huAZaiiUuAqSJSpjeXpeNgntiePRPqAbSymNr57HzmLLCPqBw0RZUIIQB3O4f8OdLxEwIgQeiyRiBZ2hrMZJjsPzn1OolLADnR1QaKsHOiisESCpSFNRx3OgnOfo6gU9BkkKgpLJEgaROUF0smr2FT0Hj/3nEWlgMWlc5CoKCyR4DBIKLY4HvZJscFD/NyPIColEtQHicqaThCFJRIUbbIUug7ObZulcOwY+LjcNfm4RGFxj2p2wmuOFwMSxT7vDaVL6lMDcWkVipGnWq2zFI6drkGiorA4RuOfM/ddjgZU1n6v/hcc/HoDfZbCxilkFhddbp3PLePn1nmEt0rTMRa4F1b3+x90Pi6mfiyRbrzg/ZqM68l0duk7nWcNiWKftx5LKaK+at2KkagUHA/7e+75qIYuD5PpDJYLXnea/UaiMkR6Uwc8Qj8U3EDxoozC4gfVYq8lPK9rUTGZzuZQe496ERYXaTqOh306mc6AHsSFncdWlfI1iooQoni+tlPlY+NKCDGvOs/FoZAfVGPw1HchNKSKfc/Hw37n+sIuc//0GfmfiBYA/oKMwPaHoaj8jfMXlYKToXQUFj+ohOWGXdUHgxu2Km5J5unaORwmFOtZXDZEtDZ0a3easycw3lQzYlFYPMD2AVUFX3suSpUV1G/VzOVFfWYpbBCXwh7TG2zMNIkbcy6sVTujsPhjrdh3M5nOvEY6K+AGpbr2owejcg6/qU91KUeVwbk70ltA6sB5g8wzreydReOtJ46H/W4ynams698n01nuM2wE9xgynPZW3qAWmz6vnUEfaiB1cR8aQlwW4uIjl/MT5DAplNnAtrw2OQRGYfHLCnI2qNqgfVXssr+IqnGvXfZWDNJ0OHM0C0BcnogocXTu4IhDIY9wo00VH7nokp9Qsm2oYps8HQ97Z0bHEHL/GKQVcfkMPpJBNwqLb/it/EPxUZEvx8lQhBvMFnrbhrOYwyGISoGBuGxYgPtm7MMfK6KwDACnptDNVHyfTGd5X1PRk+nscjKdrQH8gx48W1tcP0MgolLAv1W3yO4KsufyUYywTjgXYUmGLoAtDdOgNwB+scC06klMprM5C8oO+kV0rmZhijJkCExUCtgBMIFaXK7xgcRFCLEUQrwKIUgIsesjj/O5GG9vJtNZOrakZ+x6/grgs+aQG8jf9gJpG9kA2Oq8YrmXs4B8GzfFiHUtKmvoReWL7bPi35Z0KpSaHMCtYn8hLs7j5w6JEGIO6SVccAXN+h+r8xLRyU7Oh1smmGDaXMF+aT5+gXn+mb54hZxNad1AuVeSwd4F/BnSb8LWIesJwNLh8CeFOjAz0CKhWEPPxzU/j4e9ca+x5M5f5T8hxmzhRZKq9vQnEeVtz3suPZaCKwzj9ThHhxgrx8N+w8bVe6jfnjps0o4C7KfioWeXava3ERXdSmVf2A6HlPUgRFFxybnYWIbGtoGfcDzsd/xm/BP6OK5teYNcQDcfcLjYNvXph7BznBs6YalW7JDGmCGVpeClrxMdD/uch51/QE5Ldzn3T8ioavPjYe/U+a2B1vmUj4d9Dn38VR+EWN+CRzcUWkF2y28gRSb1VaAmjof9djKdfYIsXwjL0l/gwAeEDbQrACseDiSQ3ew5b9UhX/EyyCH9VfIBhaRwBptD2p+yjudLIOug795LzsIWsURpvI1EIu3gwNsn0/tEJPyXphlXxttoY4lEIr0ThSUSifROa2Fhx5rIByM+94gJRsIihLgUQqyEEFt2+yUA/y25AGem0ciFEElxDoNtJ4TIhRD3Jgmp+VjTc+u2pHLOdeXzzOR3lr7/7vw231Wcq1qW3PB7J/fc4poJP9/XynMnvt+pxbmqz8f4u5XzGN+HHuqD9twRPY3Cwg1tB+A71P4aV5AOTL9MBcCCK8iZqc8AdlyhhvZruDuTlA618MtkA2nYu4N6Bu4GMrdM2/Ul65bFS1t+L+KJWmHhN8ovmE/rfgaQO2r8F5DWdlfntyEb+PpO4fubw9wL+AryuaSWl7qyFWl2mf9IMWVHiVZY+AHq1nvUcQ23De8a6qj3PrniacVzJYe9N/EFgPsWPRfb+DODxAiO2KF0kOM3Vqb46I33byGHRwmkc1i1Et4KIVKL9JN/1ny2hOz6lntNN0KIxGCe/RH2Ime6puOrECIzTAcxGlgwVaLyBF5dDen4luB0Dc8FpHNcYnHJW6FIeKUp2xzNq7ab+AK7ZGzR87YNRHSyQb4VqLJtASw0x2eK43eaY5PqsarjKt9ZQD7g8vc2iuPyyjHrpnMbXHut+G3Flht83+q3Wpal8fq291xxnwnAyuK5EICl5vjq8ym2e8PfcW/7HBTHJl3rRJv64vKaHct7Ujf6uE+6oZDKRX1JmhWaRJTidH3RVUuDnur8W5zGDE36OHdHbnjIeBbwb6na036QJsUD6ZOG296T1KBslybHRcJAJyzV7uYjNXdV14p9fQYmziv/h7BOCACyAIzJfaF6XrVBoEkOR6sLJeeW170wMPyqRC8SKKYOco3GUq5g1VWoc8vy1BFKPIvqb7zA8BkNXfFk8EIBTsWnzQulySgbjbYjwlRYTBu1S0OX09QYFmwgwxGU+dzXsG9gksr/ueH3qvWjTc/iWjf1zPs7x7zxhKoeDBn2YRBOhEXVQAzfWq6pvrF6i4HSghVOgzBnA5Tj3Egt94eIalj84WaWVNPNXewFTm4gj7+rzlomviyJhb9JZiqgRLTj834v7b4WQqx0hk5HzA1/39xxOdryhPf2vDshxLr8HNh+VZ3W/gm7EJ5lUlOnPCJat7zGmNhp9neyG/Yd83aLFg+8oXGo/GQAs8xyNzD3e8hhEYibiO5Z8MplWwshNh57eFfQp/YYAzlOg1aleG+zqvZUn9CynjE28XPXjUeMHH5Jqj5aoIMjaijBtG0bx7eAhmflIDmFg9jZTEF7YI33Ht4rvG/QaeX4DOH2wCLMGOOxPIbSReWZsGq61NuPsEixRzZ4b6/6/9Qz/y33Zl7I3Js7MiB991jmPZ+vzBukJ62NDeMJ5jMbO9sCMWucLjnIhBALInJttHuBmdF4jmFTaGgholcORVFO2raC/F1p5fCsh0s+wn/uqQ9HKMKiS3ex421LRG3Ge7nr3g03jBXed+evcNqld8HO5PdxDypIYWHu8V5Yrrm3UrWPZT1cK6MOsVwjZpwICxHlVWOO6SKxthBR4urcPiCiTNEQvtoGhfqosAGxOkNUXVlv4v0dCQRTG8vc8LhzcW1vQ6rYl3kuQ1eqjm6J4ffmPVy7aYib9XCNiCdMhSVtOoAd66rTwjvL8owWfpt+q+zuusTfN1Wb0MJwHVRa+d86kyMPdXVOj88jH77Mhy6ADlce46aZEO8MKphqLcfOukTj5h7DegR3ReWaX7tGh+03VQFta7TW9Vp8Oh264KptfF8PrDX7d11OqjPebnBaWTZCiKVqpoNvWtU4+Dbyt4w1bMhNoU4ANQZyyNm38gzXSgihNJ5z4CVVo2/rWJXhvTczIOtR1vJ8Q5BD3VN94PuVeyxLHXPInqauV513OblOWDJIJXsXtQ3AVghxj99eqgkXTuUFue5SsLHCxu8uLueDwcK4wfuXxAWAv4UQPyCfew7plZlA9maqCw5b+5rw9R8r1291rgHJoHf4/FrzWUiYrmrXUxNZShVFznTb2kSs6jEaVt6hzMrIWTiNCLY2KMcc6shqnX6roiy54feM7zmkAV5Z9jb3r+H5nNxLvn5S2i673Ice6oPRPa5cM+vhukNu2mdoummNtyQd0R51n9fwjDCiuw0Gq/164GK0guRQN8Hp6m0TPlHH4S8RvRJRXtrGuDJ4hfGGSvjW9RkCDbNCJENOfoJ5JXuCVLsxVoZeYWEeZeUiGXJyAfPyvwH4i8ZlC3FGSZzH9vy/UE8OpY3TzVxZFpC9F53APEO+raKovGe0Uc+IaEdEC8gXi66BvECulZpTO8/os4V7XsX9C3mm8A2ybf9BPYb8EDwmNP+CnPcuTz1vo5icP+xuUPZ52FH0hDWGZ4Tmw5bihFfSBMjvirWwRCKRSBP/A3Jkqd9jS9KSAAAAAElFTkSuQmCC" alt="Flux Open Home" style="height:44px;filter:brightness(0) invert(1);">
        <div>
            <h1>Irrigation</h1>
            <div class="subtitle">Device setup, management access, and system settings</div>
        </div>
    </div>
    <div class="header-nav" style="display:flex;gap:8px;align-items:center;">
        <a href="?" style="color:white;text-decoration:none;padding:6px 14px;background:rgba(255,255,255,0.15);border-radius:8px;font-size:13px;">&#8592; Homeowner</a>
        <span style="background:rgba(255,255,255,0.25);padding:4px 12px;border-radius:12px;font-size:12px;font-weight:500;">Configuration</span>
        <button class="dark-toggle" onclick="toggleDarkMode()" title="Toggle dark mode">🌙</button>
        <button class="dark-toggle" onclick="showHelp()" title="Help">❓</button>
        <button class="btn btn-secondary btn-sm" onclick="switchToManagement()">Management</button>
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
                <p id="deviceFilterToggle" style="display:none;font-size:12px;color:var(--text-muted);margin-top:6px;"></p>
            </div>

            <div id="deviceEntities">
                <div class="device-info empty" id="noDeviceMsg">
                    Select your irrigation controller device above to configure which entities are exposed through the API.
                </div>
            </div>
        </div>
    </div>

    <!-- Gophr Moisture Probes -->
    <div class="card">
        <div class="card-header" style="cursor:pointer;" onclick="document.getElementById('moistureCardBody').style.display = document.getElementById('moistureCardBody').style.display === 'none' ? 'block' : 'none'; document.getElementById('moistureChevron').textContent = document.getElementById('moistureCardBody').style.display === 'none' ? '▶' : '▼';">
            <h2 style="display:flex;align-items:center;gap:8px;"><svg xmlns="http://www.w3.org/2000/svg" viewBox="155 170 745 295" style="height:28px;width:auto;"><path fill="var(--text-primary)" fill-rule="evenodd" d="M322.416931,281.625397 C323.073517,288.667053 324.062378,295.290680 324.095001,301.918976 C324.240021,331.407532 324.573761,360.907135 323.953278,390.384125 C323.315430,420.685608 305.951965,442.817230 276.750000,451.004150 C252.045670,457.930115 227.631088,457.462616 204.859512,444.061829 C193.733704,437.514404 185.529037,427.904022 179.913101,416.206268 C179.426056,415.191742 179.182327,414.060425 178.732849,412.703430 C192.772842,404.558502 206.657608,396.503632 221.095810,388.127686 C222.548920,398.588440 227.417007,406.291168 236.306213,411.228241 C242.295563,414.554749 248.872574,415.283630 255.195541,413.607391 C269.094299,409.922882 279.602142,400.331543 276.985321,375.408997 C268.292480,376.997406 259.625824,379.362396 250.827682,380.053528 C212.511551,383.063599 177.112976,355.681854 170.128632,318.134705 C162.288498,275.986908 187.834488,236.765533 229.805115,227.777832 C248.650925,223.742157 267.514679,224.860764 285.481567,232.988800 C306.417999,242.460220 318.099121,258.975830 322.416931,281.625397 M216.907806,286.065979 C225.295822,272.331604 237.176926,265.403442 252.929047,267.162231 C267.323669,268.769440 277.405518,277.037170 282.681366,290.504517 C288.739105,305.967712 282.622986,322.699615 267.827820,332.537079 C254.597519,341.334045 236.860046,339.821564 225.031052,328.887756 C212.268768,317.091309 209.342514,302.099945 216.907806,286.065979z"/><path fill="var(--text-primary)" fill-rule="evenodd" d="M440.778076,230.141632 C466.800079,239.483002 484.434601,256.637787 491.839233,283.105133 C500.007050,312.300537 489.084961,342.278625 464.074921,361.493744 C431.640076,386.413300 382.445770,383.545990 353.656403,355.057953 C318.682434,320.450043 324.759583,264.850739 366.581024,238.762604 C389.708984,224.335434 414.506042,222.091354 440.778076,230.141632 M419.079773,266.764740 C437.440765,270.748535 450.546936,286.287720 449.715515,302.670624 C448.781708,321.070160 434.135437,336.279297 415.803497,337.885803 C397.935547,339.451660 380.905334,327.358856 376.509705,309.984161 C370.390747,285.797394 393.025116,262.545013 419.079773,266.764740z"/><path fill="var(--text-primary)" fill-rule="evenodd" d="M505.651459,275.706696 C519.676758,244.101715 544.491516,227.960754 577.827881,226.121109 C611.160156,224.281693 638.083069,237.473114 655.040100,266.968140 C676.296448,303.941376 659.723389,352.082367 620.168030,369.955170 C596.583435,380.611755 572.628662,381.200958 548.535156,371.444641 C547.794678,371.144745 546.983826,371.018707 545.645447,370.662506 C545.645447,390.059296 545.645447,409.111145 545.645447,428.497070 C530.607544,428.497070 516.074341,428.497070 500.996918,428.497070 C500.996918,426.395355 500.996918,424.628113 500.996918,422.860901 C500.996948,382.885895 500.731262,342.907776 501.200592,302.938263 C501.306030,293.961548 503.980682,285.014954 505.651459,275.706696 M598.115479,334.281433 C575.892517,344.478851 553.161804,330.843811 547.077026,312.404572 C542.453613,298.393616 547.708435,283.178833 560.344666,273.573029 C572.626587,264.236572 589.550232,263.566986 602.341309,271.911499 C626.866516,287.910980 624.857971,320.051117 598.115479,334.281433z"/><path fill="var(--text-primary)" d="M670.825439,182.155045 C670.825439,180.187927 670.825439,178.699997 670.825439,176.849915 C685.635620,176.849915 700.198181,176.849915 715.259155,176.849915 C715.259155,197.175491 715.259155,217.587784 715.259155,238.510025 C716.406799,238.089737 717.045288,238.015717 717.473022,237.676285 C735.466553,223.398956 755.376953,222.532013 775.856384,230.443253 C790.949036,236.273605 798.483093,249.035553 801.756714,264.225281 C803.287109,271.326416 804.004150,278.725677 804.067200,285.998688 C804.319702,315.143738 804.171570,344.292236 804.171570,373.721710 C789.407043,373.721710 774.836182,373.721710 759.827942,373.721710 C759.827942,371.711731 759.835571,369.768616 759.826843,367.825562 C759.706604,341.165588 760.090210,314.490112 759.275696,287.851318 C758.772949,271.407867 746.863953,263.163330 731.353210,266.883484 C722.925842,268.904694 717.127258,275.714691 716.057434,285.099060 C715.681213,288.399445 715.542114,291.742798 715.536499,295.066956 C715.495117,319.566559 715.514954,344.066254 715.515503,368.565918 C715.515503,370.204803 715.515503,371.843689 715.515503,373.824829 C700.566040,373.824829 685.988281,373.824829 670.825439,373.824829 C670.825439,310.162415 670.825439,246.398331 670.825439,182.155045z"/><path fill="var(--text-primary)" d="M855.839355,323.000092 C855.839355,340.127289 855.839355,356.754486 855.839355,373.695129 C840.823486,373.695129 826.114746,373.695129 810.997253,373.695129 C810.997253,371.683563 810.994263,369.731567 810.997681,367.779572 C811.046997,339.965515 810.786316,312.145172 811.345886,284.341370 C811.503601,276.506470 813.144958,268.402985 815.701904,260.971832 C822.865173,240.153290 839.259949,230.438156 859.952881,227.148788 C867.723389,225.913574 875.715454,226.072052 883.918213,225.576279 C883.918213,240.530334 883.918213,254.247711 883.918213,268.202820 C883.009399,267.944122 882.380005,267.791504 881.768005,267.586914 C867.262085,262.736725 856.693237,269.680603 856.083313,285.032410 C855.587708,297.505157 855.890564,310.009644 855.839355,323.000092z"/><path fill="#6DAC39" d="M397.000000,391.998138 C428.473236,391.998138 459.446503,391.998138 490.792969,391.998138 C490.792969,404.699890 490.792969,417.072754 490.792969,429.726562 C438.290070,429.726562 385.895660,429.726562 333.244019,429.726562 C333.244019,417.257721 333.244019,404.991150 333.244019,391.998138 C354.328308,391.998138 375.414154,391.998138 397.000000,391.998138z"/></svg> Moisture Probes</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <span id="moistureStatusBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-tile);color:var(--text-muted);">—</span>
                <span id="moistureChevron" style="font-size:12px;color:var(--text-muted);">▶</span>
            </div>
        </div>
        <div class="card-body" id="moistureCardBody" style="display:none;">
            <div id="moistureConfigContent">
                <div class="loading">Loading moisture configuration...</div>
            </div>
        </div>
    </div>

    <!-- Management Access Control -->
    <div class="card">
        <div class="card-header">
            <h2>Management Access Control</h2>
        </div>
        <div class="card-body">
            <p style="margin-bottom:16px; color:var(--text-secondary); font-size:14px;">
                Generate a connection key to grant your management company access to all your devices — irrigation zones, moisture probes, weather settings, schedules, and sensors.
                They paste this key into their Flux Open Home Irrigation Control add-on to connect.
            </p>

            <!-- Connection Mode Selection -->
            <div class="form-group">
                <label>Connection Method</label>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:8px;" class="conn-mode-grid">
                    <label style="display:block;cursor:pointer;padding:12px;border:2px solid var(--border-input);border-radius:8px;" id="modeNabuLabel">
                        <input type="radio" name="connMode" value="nabu_casa" checked onchange="toggleConnectionMode()">
                        <strong style="font-size:14px;">Nabu Casa</strong>
                        <span style="color:var(--color-success);font-size:11px;"> (Recommended)</span>
                        <div style="font-size:12px;color:var(--text-hint);margin-top:4px;">Works with your existing Nabu Casa subscription. No extra setup needed.</div>
                    </label>
                    <label style="display:block;cursor:pointer;padding:12px;border:2px solid var(--border-input);border-radius:8px;" id="modeDirectLabel">
                        <input type="radio" name="connMode" value="direct" onchange="toggleConnectionMode()">
                        <strong style="font-size:14px;">Direct Connection</strong>
                        <div style="font-size:12px;color:var(--text-hint);margin-top:4px;">Requires port forwarding, Cloudflare Tunnel, or VPN.</div>
                    </label>
                </div>
            </div>

            <!-- Nabu Casa Mode Fields -->
            <div id="nabuCasaFields">
                <div class="form-group">
                    <label>Your Nabu Casa URL</label>
                    <input type="text" id="homeownerUrl" placeholder="https://xxxxxxxx.ui.nabu.casa">
                    <p style="font-size:12px; color:var(--text-placeholder); margin-top:4px;">
                        Find this in HA: <strong>Settings &rarr; Home Assistant Cloud &rarr; Remote Control</strong>. Copy the URL shown there.
                    </p>
                </div>
                <div class="form-group">
                    <label>Home Assistant Long-Lived Access Token</label>
                    <input type="password" id="haToken" placeholder="Paste your HA token here">
                    <p style="font-size:12px; color:var(--text-placeholder); margin-top:4px;">
                        Create one in HA: Go to your <strong>Profile</strong> (click your name, bottom-left) &rarr; scroll to
                        <strong>Long-Lived Access Tokens</strong> &rarr; <strong>Create Token</strong>. Name it "Irrigation Management" and paste it above.
                    </p>
                </div>
                <div style="background:var(--bg-active-tile);border:1px solid var(--border-active);border-radius:8px;padding:12px;margin-bottom:16px;font-size:13px;">
                    <strong style="color:var(--color-primary);">&#9989; One-time setup required</strong><br>
                    <span style="color:var(--text-secondary);">
                        After generating the connection key, add this to your HA <strong>configuration.yaml</strong>
                        (if not already present):<br>
                        <code style="background:var(--bg-tile);padding:2px 6px;border-radius:3px;display:inline-block;margin-top:4px;">homeassistant:</code><br>
                        <code style="background:var(--bg-tile);padding:2px 6px;border-radius:3px;display:inline-block;margin-left:16px;">packages: !include_dir_named packages</code><br>
                        <span style="font-size:11px;color:var(--text-hint);margin-top:4px;display:block;">Then restart Home Assistant once. The add-on automatically creates the needed proxy configuration.</span>
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
                    <p style="font-size:12px; color:var(--text-placeholder); margin-top:4px;">
                        Port 8099 must be accessible externally. Options:<br>
                        &bull; <strong>Port forwarding</strong> on your router + DuckDNS for dynamic DNS<br>
                        &bull; <strong>Cloudflare Tunnel</strong> pointing to <code style="background:var(--bg-tile);padding:1px 4px;border-radius:3px;">localhost:8099</code><br>
                        &bull; <strong>Tailscale / WireGuard</strong> VPN between both HA instances<br><br>
                        Make sure the port is enabled in the add-on Configuration tab under "Network".
                    </p>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>First Name</label>
                    <input type="text" id="homeownerFirstName" placeholder="e.g., John">
                </div>
                <div class="form-group">
                    <label>Last Name</label>
                    <input type="text" id="homeownerLastName" placeholder="e.g., Smith">
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
            <div class="form-row">
                <div class="form-group" style="max-width:200px;">
                    <label>ZIP Code</label>
                    <input type="text" id="homeownerZip" placeholder="e.g., 62704">
                </div>
                <div class="form-group">
                    <label>Phone Number</label>
                    <input type="tel" id="homeownerPhone" placeholder="e.g., (555) 123-4567">
                    <p style="font-size:12px; color:var(--text-placeholder); margin-top:4px;">
                        Shared with your management company so they can contact you if needed.
                    </p>
                </div>
            </div>
            <div id="generateKeyArea">
                <div id="generateKeyUnlocked" style="display:block;">
                    <button class="btn btn-primary" onclick="generateConnectionKey()">Generate Connection Key</button>
                </div>
                <div id="generateKeyLocked" style="display:none;">
                    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                        <button class="btn btn-primary" disabled style="opacity:0.5;cursor:not-allowed;" id="generateBtnLocked">
                            &#128274; Generate Connection Key
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="unlockGenerateKey()" style="font-size:12px;">
                            &#128275; Unlock to Regenerate
                        </button>
                    </div>
                    <p style="font-size:12px;color:var(--text-placeholder);margin-top:6px;">
                        Regenerating will invalidate the current connection key. Your management company will need the new key.
                    </p>
                </div>
                <div id="generateKeyConfirm" style="display:none;">
                    <div style="background:var(--bg-warning);border:1px solid var(--border-new-key);border-radius:8px;padding:12px 16px;margin-bottom:12px;">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                            <span style="font-size:18px;">&#9888;</span>
                            <strong style="color:var(--text-warning);font-size:13px;">This will replace your current connection key</strong>
                        </div>
                        <p style="font-size:12px;color:var(--text-warning);margin:0;">
                            The old key will stop working immediately. Your management company will need the new key to reconnect.
                        </p>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <button class="btn btn-primary" onclick="generateConnectionKey()">Regenerate Connection Key</button>
                        <button class="btn btn-secondary" onclick="lockGenerateKey()">Cancel</button>
                    </div>
                </div>
            </div>

            <div id="connectionKeyDisplay" class="new-key-display" style="display:none;">
                <strong>Connection Key</strong>
                <code id="connectionKeyValue" style="font-size:13px;"></code>
                <p class="warning">Share this key with your management company. They paste it into their Flux Open Home Irrigation Control add-on.</p>
                <div style="display:flex;gap:8px;flex-wrap:wrap;">
                    <button class="btn btn-secondary btn-sm" onclick="copyConnectionKey()">&#128203; Copy to Clipboard</button>
                    <button class="btn btn-secondary btn-sm" onclick="emailConnectionKey()">&#9993; Email Key</button>
                    <button class="btn btn-secondary btn-sm" onclick="showQRCode()">&#9783; QR Code</button>
                </div>
            </div>

            <!-- QR Code Modal -->
            <div id="qrModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10000;align-items:center;justify-content:center;">
                <div style="background:var(--bg-card);border-radius:16px;padding:24px;max-width:400px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                        <h3 style="font-size:16px;font-weight:600;margin:0;color:var(--text-primary);">Connection Key QR Code</h3>
                        <button onclick="closeQRModal()" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text-placeholder);padding:0 4px;">&times;</button>
                    </div>
                    <div id="qrCodeContainer" style="display:flex;justify-content:center;padding:16px;background:var(--bg-card);border-radius:8px;"></div>
                    <p style="font-size:12px;color:var(--text-hint);text-align:center;margin-top:12px;">
                        Your management company can scan this QR code to import the connection key.
                    </p>
                    <div style="display:flex;gap:8px;justify-content:center;margin-top:16px;">
                        <button class="btn btn-secondary btn-sm" onclick="downloadQRCode()">&#128190; Download QR</button>
                        <button class="btn btn-secondary btn-sm" onclick="closeQRModal()">Close</button>
                    </div>
                </div>
            </div>

            <!-- Revoke Access Section -->
            <div id="revokeSection" style="display:none;margin-top:20px;padding-top:20px;border-top:1px solid var(--border-light);">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-size:14px;font-weight:600;color:var(--text-primary);">Management Access</div>
                        <div id="revokeStatusText" style="font-size:13px;color:var(--color-success);margin-top:2px;">Active — your management company can access this system</div>
                    </div>
                    <button class="btn btn-danger btn-sm" onclick="confirmRevokeAccess()">Revoke Access</button>
                </div>
            </div>

            <!-- Revoke Confirmation Modal -->
            <div id="revokeModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:10000;align-items:center;justify-content:center;">
                <div style="background:var(--bg-card);border-radius:16px;padding:24px;max-width:440px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
                        <span style="font-size:28px;">&#9888;</span>
                        <h3 style="font-size:16px;font-weight:600;margin:0;color:var(--color-danger);">Revoke Management Access?</h3>
                    </div>
                    <p style="font-size:14px;color:var(--text-secondary);margin-bottom:12px;">
                        This will <strong>immediately</strong> prevent your irrigation management company from accessing your system. They will:
                    </p>
                    <ul style="font-size:13px;color:var(--text-secondary);margin-bottom:16px;padding-left:20px;line-height:1.8;">
                        <li>Lose access to view your zones, sensors, and schedules</li>
                        <li>Be unable to start, stop, or pause your irrigation</li>
                        <li>See your property as <strong style="color:var(--color-danger);">Access Revoked</strong> on their dashboard</li>
                    </ul>
                    <p style="font-size:13px;color:var(--text-hint);margin-bottom:20px;">
                        You can re-generate a new connection key later if you want to restore access.
                    </p>
                    <div style="display:flex;gap:8px;justify-content:flex-end;">
                        <button class="btn btn-secondary" onclick="closeRevokeModal()">Cancel</button>
                        <button class="btn btn-danger" onclick="executeRevokeAccess()">Yes, Revoke Access</button>
                    </div>
                </div>
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
                    <input type="number" id="logRetention" min="1" max="730" value="365">
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

    <!-- Weather-Based Control -->
    <div class="card">
        <div class="card-header">
            <h2>Weather-Based Control</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <span id="weatherStatusBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--border-light);color:var(--text-secondary);">Not Configured</span>
                <label class="toggle-switch">
                    <input type="checkbox" id="weatherEnabled" onchange="saveWeatherSettings()">
                    <span class="toggle-slider"></span>
                </label>
            </div>
        </div>
        <div class="card-body">
            <div class="form-group">
                <label>Weather Entity</label>
                <select id="weatherEntitySelect" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);">
                    <option value="">-- Select a weather entity --</option>
                </select>
                <p style="font-size:12px;color:var(--text-placeholder);margin-top:4px;">Uses your existing HA weather integration (NWS, Weather Underground, etc.). No API key needed.</p>
            </div>

            <div id="weatherPreview" style="display:none;background:var(--bg-weather);border-radius:8px;padding:14px;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <strong>Current Conditions</strong>
                    <button class="btn btn-secondary btn-sm" onclick="testWeatherEntity()">Refresh</button>
                </div>
                <div id="weatherPreviewContent" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;font-size:13px;"></div>
            </div>

            <div class="form-group" style="max-width:200px;">
                <label>Check Interval (minutes)</label>
                <input type="number" id="weatherInterval" min="5" max="60" value="15" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);">
            </div>

            <p style="font-size:13px;color:var(--text-secondary);margin-top:8px;">Weather rules and thresholds can be configured from the <a href="?" style="color:var(--color-primary);font-weight:500;">Homeowner Dashboard</a>.</p>

            <div style="margin-top:16px;">
                <button class="btn btn-primary" onclick="saveWeatherSettings()">Save Weather Settings</button>
            </div>
        </div>
    </div>


</div>

<!-- Help Modal -->
<div id="helpModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:640px;max-height:80vh;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">Configuration Help</h3>
            <button onclick="closeHelpModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div id="helpContent" style="padding:16px 24px 24px 24px;overflow-y:auto;font-size:14px;color:var(--text-secondary);line-height:1.6;"></div>
    </div>
</div>

<div class="toast" id="toast"></div>

<script>
    const BASE = (window.location.pathname.replace(/\\/+$/, '')) + '/api';

    // --- Dark Mode ---
    function toggleDarkMode() {
        const isDark = document.body.classList.toggle('dark-mode');
        localStorage.setItem('flux_dark_mode_homeowner', isDark);
        document.querySelector('.dark-toggle').textContent = isDark ? '☀️' : '🌙';
    }
    (function initDarkToggleIcon() {
        const btn = document.querySelector('.dark-toggle');
        if (btn && document.body.classList.contains('dark-mode')) btn.textContent = '☀️';
    })();

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
            document.getElementById('logRetention').value = data.log_retention_days || 365;
            document.getElementById('auditLogEnabled').checked = data.enable_audit_log !== false;

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
    let showingAllDevices = false;

    async function loadDevices(selectedId, showAll) {
        try {
            const all = showAll !== undefined ? showAll : showingAllDevices;
            const res = await fetch(`${BASE}/devices${all ? '?show_all=true' : ''}`);
            const data = await res.json();
            const devices = data.devices || data;
            const totalCount = data.total_count || devices.length;
            const filtered = data.filtered !== false;
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

            // Show/hide the "show all" link
            const toggleEl = document.getElementById('deviceFilterToggle');
            if (filtered && devices.length < totalCount) {
                toggleEl.innerHTML = 'Showing ' + devices.length + ' irrigation device' + (devices.length !== 1 ? 's' : '') +
                    ' of ' + totalCount + ' total. <a href="#" onclick="loadAllDevices(event)">Show all devices</a>';
                toggleEl.style.display = '';
            } else if (!filtered && totalCount > 0) {
                toggleEl.innerHTML = 'Showing all ' + totalCount + ' devices. <a href="#" onclick="loadFilteredDevices(event)">Show only irrigation devices</a>';
                toggleEl.style.display = '';
            } else {
                toggleEl.style.display = 'none';
            }
        } catch (e) {
            showToast('Failed to load devices', 'error');
        }
    }

    function loadAllDevices(e) {
        e.preventDefault();
        showingAllDevices = true;
        loadDevices(undefined, true);
    }

    function loadFilteredDevices(e) {
        e.preventDefault();
        showingAllDevices = false;
        loadDevices(undefined, false);
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

    let _deviceEntitiesExpanded = false;

    function toggleDeviceEntities() {
        _deviceEntitiesExpanded = !_deviceEntitiesExpanded;
        const body = document.getElementById('deviceEntitiesBody');
        const chevron = document.getElementById('deviceEntitiesChevron');
        if (body) body.style.display = _deviceEntitiesExpanded ? 'block' : 'none';
        if (chevron) chevron.textContent = _deviceEntitiesExpanded ? '▼' : '▶';
    }

    function renderDeviceEntities(zones, sensors, other) {
        const container = document.getElementById('deviceEntities');
        const total = zones.length + sensors.length + (other ? other.length : 0);

        if (total === 0) {
            container.innerHTML = '<div class="device-info empty">No entities found on this device. Make sure the device has switch, valve, or sensor entities.<br><a href="' + BASE + '/device/debug" target="_blank" style="color:var(--color-primary);font-size:12px;">View debug info</a></div>';
            return;
        }

        let html = '';

        // Collapsible header
        html += '<div style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;padding:8px 0;margin-top:8px;border-top:1px solid var(--border-light);" onclick="toggleDeviceEntities()">';
        html += '<span style="font-size:13px;font-weight:600;color:var(--text-secondary);">Device Entities (' + total + ')</span>';
        html += '<span id="deviceEntitiesChevron" style="font-size:12px;color:var(--text-muted);">' + (_deviceEntitiesExpanded ? '▼' : '▶') + '</span>';
        html += '</div>';

        // Collapsible body (hidden by default)
        html += '<div id="deviceEntitiesBody" style="display:' + (_deviceEntitiesExpanded ? 'block' : 'none') + ';">';

        if (zones.length > 0) {
            html += '<div class="entity-list"><h4>Zones (' + zones.length + ')</h4>';
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

        html += '</div>';

        container.innerHTML = html;
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
        document.getElementById('modeNabuLabel').style.borderColor = mode === 'nabu_casa' ? 'var(--color-accent)' : 'var(--border-input)';
        document.getElementById('modeDirectLabel').style.borderColor = mode === 'direct' ? 'var(--color-accent)' : 'var(--border-input)';
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
            if (data.phone) document.getElementById('homeownerPhone').value = data.phone;
            if (data.first_name) document.getElementById('homeownerFirstName').value = data.first_name;
            if (data.last_name) document.getElementById('homeownerLastName').value = data.last_name;
            if (data.connection_key) {
                document.getElementById('connectionKeyValue').textContent = data.connection_key;
                document.getElementById('connectionKeyDisplay').style.display = 'block';
                document.getElementById('revokeSection').style.display = 'block';
                // Lock the generate button since a key already exists
                lockGenerateKey();
            } else {
                document.getElementById('connectionKeyDisplay').style.display = 'none';
                document.getElementById('revokeSection').style.display = 'none';
                // No key yet — show unlocked generate button
                showUnlockedGenerate();
            }
        } catch(e) { /* first time, no key yet */ }
    }

    async function testExternalUrl() {
        const url = document.getElementById('homeownerUrlDirect').value.trim();
        const resultEl = document.getElementById('urlTestResult');
        if (!url) { showToast('Enter a URL first', 'error'); return; }

        resultEl.style.display = 'block';
        resultEl.innerHTML = '<span style="color:var(--text-secondary);">Testing: ' + escHtml(url) + '/api/system/health ...</span>';
        try {
            const res = await fetch(`${BASE}/test-url`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ url }),
            });
            const data = await res.json();
            if (data.success) {
                resultEl.innerHTML = '<span style="color:var(--color-success);">&#10004; ' + escHtml(data.message) + ' (HTTP ' + data.status_code + ')</span>';
            } else {
                resultEl.innerHTML = '<span style="color:var(--color-danger);">&#10008; ' + escHtml(data.error) + '</span>' +
                    (data.help ? '<br><span style="color:var(--text-placeholder);font-size:11px;">' + escHtml(data.help) + '</span>' : '');
            }
        } catch(e) {
            resultEl.innerHTML = '<span style="color:var(--color-danger);">&#10008; Test failed: ' + escHtml(e.message) + '</span>';
        }
    }

    async function generateConnectionKey() {
        const mode = getConnectionMode();
        const url = getEffectiveUrl();
        if (!url) { showToast('Enter your URL', 'error'); return; }

        // Validate URL format
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            showToast('URL must start with http:// or https://', 'error');
            return;
        }
        if (mode === 'nabu_casa' && !url.includes('.ui.nabu.casa') && !url.includes('.nabucasa.com') && !url.startsWith('https://')) {
            showToast('Nabu Casa URL should start with https://', 'error');
            return;
        }

        const ha_token = mode === 'nabu_casa' ? document.getElementById('haToken').value.trim() : '';
        if (mode === 'nabu_casa' && (!ha_token || ha_token === '********')) {
            if (!ha_token) { showToast('Enter your HA Long-Lived Access Token', 'error'); return; }
        }

        const label = document.getElementById('homeownerLabel').value.trim();
        const address = document.getElementById('homeownerAddress').value.trim();
        const city = document.getElementById('homeownerCity').value.trim();
        const state = document.getElementById('homeownerState').value.trim();
        const zip = document.getElementById('homeownerZip').value.trim();
        const phone = document.getElementById('homeownerPhone').value.trim();
        const first_name = document.getElementById('homeownerFirstName').value.trim();
        const last_name = document.getElementById('homeownerLastName').value.trim();

        const body = { url, label, address, city, state, zip, phone, first_name, last_name, connection_mode: mode };
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
                showToast('Connection key generated' + (mode === 'nabu_casa' ? ' (Nabu Casa mode)' : ''));
                // Re-lock the generate button now that a key exists
                lockGenerateKey();
                document.getElementById('revokeSection').style.display = 'block';
                loadSettings();
            }
        } catch(e) { showToast('Failed to generate key', 'error'); }
    }

    function lockGenerateKey() {
        document.getElementById('generateKeyUnlocked').style.display = 'none';
        document.getElementById('generateKeyLocked').style.display = 'block';
        document.getElementById('generateKeyConfirm').style.display = 'none';
    }
    function unlockGenerateKey() {
        document.getElementById('generateKeyUnlocked').style.display = 'none';
        document.getElementById('generateKeyLocked').style.display = 'none';
        document.getElementById('generateKeyConfirm').style.display = 'block';
    }
    function showUnlockedGenerate() {
        document.getElementById('generateKeyUnlocked').style.display = 'block';
        document.getElementById('generateKeyLocked').style.display = 'none';
        document.getElementById('generateKeyConfirm').style.display = 'none';
    }

    function copyConnectionKey() {
        const key = document.getElementById('connectionKeyValue').textContent;
        navigator.clipboard.writeText(key).then(() => showToast('Connection key copied!'));
    }

    function emailConnectionKey() {
        const key = document.getElementById('connectionKeyValue').textContent;
        if (!key) { showToast('No connection key to email', 'error'); return; }
        const label = document.getElementById('homeownerLabel').value.trim() || 'My Property';
        const subject = encodeURIComponent(label + ' — Flux Open Home Connection Key');
        const body = encodeURIComponent(
            'Hello,\\n\\n' +
            'Here is the connection key for "' + label + '":\\n\\n' +
            key + '\\n\\n' +
            'To connect:\\n' +
            '1. Open your Flux Open Home Irrigation Control add-on\\n' +
            '2. Click "+ Add Property"\\n' +
            '3. Paste this connection key\\n\\n' +
            'Thanks!'
        );
        window.open('mailto:?subject=' + subject + '&body=' + body, '_self');
    }

    function showQRCode() {
        const key = document.getElementById('connectionKeyValue').textContent;
        if (!key) { showToast('No connection key to generate QR code', 'error'); return; }
        const container = document.getElementById('qrCodeContainer');
        container.innerHTML = '';

        if (typeof qrcode === 'undefined') {
            container.innerHTML = '<p style="color:var(--color-danger);font-size:13px;">QR code library failed to load. Please check your internet connection.</p>';
            document.getElementById('qrModal').style.display = 'flex';
            return;
        }

        // Use error correction level L and auto-detect type number
        const qr = qrcode(0, 'L');
        qr.addData(key);
        qr.make();

        // Render QR code to canvas for high-quality output
        const cellSize = 6;
        const margin = 4;
        const moduleCount = qr.getModuleCount();
        const size = moduleCount * cellSize + margin * 2 * cellSize;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        canvas.id = 'qrCodeCanvas';
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, size, size);
        ctx.fillStyle = '#000000';
        for (let row = 0; row < moduleCount; row++) {
            for (let col = 0; col < moduleCount; col++) {
                if (qr.isDark(row, col)) {
                    ctx.fillRect(
                        (col + margin) * cellSize,
                        (row + margin) * cellSize,
                        cellSize, cellSize
                    );
                }
            }
        }
        canvas.style.cssText = 'max-width:100%;border-radius:4px;image-rendering:pixelated;';
        container.appendChild(canvas);

        // Add label below QR
        const label = document.getElementById('homeownerLabel').value.trim();
        if (label) {
            const labelEl = document.createElement('div');
            labelEl.style.cssText = 'text-align:center;font-size:13px;font-weight:600;color:var(--text-primary);margin-top:8px;';
            labelEl.textContent = label;
            container.appendChild(labelEl);
        }

        document.getElementById('qrModal').style.display = 'flex';
    }

    function closeQRModal() {
        document.getElementById('qrModal').style.display = 'none';
    }

    function downloadQRCode() {
        const qrCanvas = document.getElementById('qrCodeCanvas');
        if (!qrCanvas) return;
        const label = document.getElementById('homeownerLabel').value.trim() || 'connection-key';
        const filename = label.replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase() + '_qr.png';

        // Create a new canvas with padding and label
        const padding = 32;
        const labelText = document.getElementById('homeownerLabel').value.trim() || '';
        const labelHeight = labelText ? 30 : 0;

        const dlCanvas = document.createElement('canvas');
        const ctx = dlCanvas.getContext('2d');
        dlCanvas.width = qrCanvas.width + padding * 2;
        dlCanvas.height = qrCanvas.height + padding * 2 + labelHeight;

        // White background
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, dlCanvas.width, dlCanvas.height);

        // Draw QR code
        ctx.drawImage(qrCanvas, padding, padding);

        // Draw label
        if (labelText) {
            ctx.fillStyle = '#333333';
            ctx.font = 'bold 14px -apple-system, BlinkMacSystemFont, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(labelText, dlCanvas.width / 2, qrCanvas.height + padding + labelHeight - 4);
        }

        // Trigger download
        const link = document.createElement('a');
        link.download = filename;
        link.href = dlCanvas.toDataURL('image/png');
        link.click();
        showToast('QR code downloaded');
    }

    // Close QR modal on Escape key or backdrop click
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && document.getElementById('qrModal').style.display === 'flex') {
            closeQRModal();
        }
    });
    document.getElementById('qrModal').addEventListener('click', function(e) {
        if (e.target === this) closeQRModal();
    });

    // --- Revoke Access ---
    function confirmRevokeAccess() {
        document.getElementById('revokeModal').style.display = 'flex';
    }

    function closeRevokeModal() {
        document.getElementById('revokeModal').style.display = 'none';
    }

    async function executeRevokeAccess() {
        closeRevokeModal();
        try {
            const res = await fetch(`${BASE}/revoke-access`, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                showToast('Management company access has been revoked. Generate a new key to re-enable.');
                document.getElementById('connectionKeyDisplay').style.display = 'none';
                document.getElementById('revokeSection').style.display = 'none';
                // Clear URL fields since the old connection is invalidated
                // Keep HA token and other settings so they don't have to re-enter them
                document.getElementById('homeownerUrl').value = '';
                document.getElementById('homeownerUrlDirect').value = '';
                // Unlock generate button — no active key to protect
                showUnlockedGenerate();
                loadSettings();
                loadConnectionKey();
            } else {
                showToast(data.detail || 'Failed to revoke access', 'error');
            }
        } catch (e) { showToast('Failed to revoke access: ' + e.message, 'error'); }
    }

    // Close revoke modal on Escape key or backdrop click
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && document.getElementById('revokeModal').style.display === 'flex') {
            closeRevokeModal();
        }
    });
    document.getElementById('revokeModal').addEventListener('click', function(e) {
        if (e.target === this) closeRevokeModal();
    });

    // --- Weather Settings ---
    async function loadWeatherEntities() {
        try {
            const res = await fetch(`${BASE}/weather/entities`);
            const data = await res.json();
            const select = document.getElementById('weatherEntitySelect');
            const currentVal = select.value;
            select.innerHTML = '<option value="">-- Select a weather entity --</option>';
            for (const entity of (data.entities || [])) {
                const opt = document.createElement('option');
                opt.value = entity.entity_id;
                opt.textContent = entity.friendly_name + ' (' + entity.condition + ')';
                if (entity.entity_id === currentVal) opt.selected = true;
                select.appendChild(opt);
            }
        } catch (e) {
            console.log('Failed to load weather entities:', e);
        }
    }

    async function loadWeatherSettings() {
        try {
            const settingsRes = await fetch(`${BASE}/settings`);
            const settings = await settingsRes.json();
            document.getElementById('weatherEnabled').checked = settings.weather_enabled || false;
            document.getElementById('weatherInterval').value = settings.weather_check_interval_minutes || 15;

            await loadWeatherEntities();
            if (settings.weather_entity_id) {
                document.getElementById('weatherEntitySelect').value = settings.weather_entity_id;
            }

            updateWeatherBadge(settings.weather_enabled, settings.weather_entity_id);

            if (settings.weather_enabled && settings.weather_entity_id) {
                testWeatherEntity();
            }
        } catch (e) {
            console.log('Failed to load weather settings:', e);
        }
    }

    function updateWeatherBadge(enabled, entityId) {
        const badge = document.getElementById('weatherStatusBadge');
        if (!entityId) {
            badge.textContent = 'Not Configured';
            badge.style.background = 'var(--border-light)';
            badge.style.color = 'var(--text-secondary)';
        } else if (!enabled) {
            badge.textContent = 'Disabled';
            badge.style.background = 'var(--bg-warning)';
            badge.style.color = 'var(--text-warning)';
        } else {
            badge.textContent = 'Active';
            badge.style.background = 'var(--bg-success-light)';
            badge.style.color = 'var(--text-success-dark)';
        }
    }

    async function saveWeatherSettings() {
        try {
            const entityId = document.getElementById('weatherEntitySelect').value;
            const enabled = document.getElementById('weatherEnabled').checked;
            const interval = parseInt(document.getElementById('weatherInterval').value) || 15;

            await fetch(`${BASE}/general`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    weather_entity_id: entityId,
                    weather_enabled: enabled,
                    weather_check_interval_minutes: interval,
                }),
            });

            updateWeatherBadge(enabled, entityId);
            showToast('Weather settings saved');
        } catch (e) {
            showToast('Failed to save weather settings', 'error');
        }
    }

    async function testWeatherEntity() {
        const entityId = document.getElementById('weatherEntitySelect').value;
        if (!entityId) return;

        const preview = document.getElementById('weatherPreview');
        const content = document.getElementById('weatherPreviewContent');
        preview.style.display = 'block';
        content.innerHTML = '<span style="color:var(--text-placeholder);">Loading...</span>';

        try {
            const res = await fetch(`${BASE}/weather/current`);
            const data = await res.json();
            const w = data.weather || {};
            if (w.error) {
                content.innerHTML = '<span style="color:var(--color-danger);">' + escHtml(w.error) + '</span>';
                return;
            }

            const conditionIcons = {
                'sunny': '☀️', 'clear-night': '🌙', 'partlycloudy': '⛅',
                'cloudy': '☁️', 'rainy': '🌧️', 'pouring': '🌧️',
                'snowy': '❄️', 'windy': '💨', 'fog': '🌫️',
                'lightning': '⚡', 'lightning-rainy': '⛈️', 'hail': '🧊',
            };
            const icon = conditionIcons[w.condition] || '🌡️';

            content.innerHTML = `
                <div style="padding:6px 10px;background:var(--bg-card);border-radius:6px;text-align:center;">
                    <div style="font-size:20px;">${icon}</div>
                    <div style="font-weight:600;text-transform:capitalize;color:var(--text-primary);">${escHtml(w.condition || 'unknown')}</div>
                </div>
                <div style="padding:6px 10px;background:var(--bg-card);border-radius:6px;">
                    <div style="color:var(--text-placeholder);font-size:11px;">Temperature</div>
                    <div style="font-weight:600;color:var(--text-primary);">${w.temperature != null ? w.temperature + (w.temperature_unit || '°F') : 'N/A'}</div>
                </div>
                <div style="padding:6px 10px;background:var(--bg-card);border-radius:6px;">
                    <div style="color:var(--text-placeholder);font-size:11px;">Humidity</div>
                    <div style="font-weight:600;color:var(--text-primary);">${w.humidity != null ? w.humidity + '%' : 'N/A'}</div>
                </div>
                <div style="padding:6px 10px;background:var(--bg-card);border-radius:6px;">
                    <div style="color:var(--text-placeholder);font-size:11px;">Wind</div>
                    <div style="font-weight:600;color:var(--text-primary);">${w.wind_speed != null ? w.wind_speed + ' ' + (w.wind_speed_unit || 'mph') : 'N/A'}</div>
                </div>
            `;
        } catch (e) {
            content.innerHTML = '<span style="color:var(--color-danger);">Failed to load weather data</span>';
        }
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

    // --- Moisture Probes ---
    const MBASE = BASE + '/homeowner/moisture';

    async function mcfg(path, method = 'GET', bodyData = null) {
        const opts = { method, headers: {} };
        if (bodyData) {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(bodyData);
        }
        const res = await fetch(MBASE + path, opts);
        const data = await res.json();
        if (!res.ok) {
            const detail = data.detail || data.error || JSON.stringify(data);
            throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
        }
        return data;
    }

    async function loadMoistureConfig() {
        const content = document.getElementById('moistureConfigContent');
        const badge = document.getElementById('moistureStatusBadge');
        try {
            const data = await mcfg('/probes');
            const settings = await mcfg('/settings');
            const probes = data.probes || {};
            const probeCount = Object.keys(probes).length;

            if (settings.enabled) {
                badge.textContent = probeCount + ' probe(s)';
                badge.style.background = 'var(--bg-success-light)';
                badge.style.color = 'var(--text-success-dark)';
            } else {
                badge.textContent = probeCount > 0 ? 'Disabled' : 'Not Configured';
                badge.style.background = 'var(--bg-tile)';
                badge.style.color = 'var(--text-muted)';
            }

            let html = '';

            // Enable toggle
            html += '<div style="margin-bottom:16px;">';
            html += '<label style="display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer;"><input type="checkbox" id="cfgMoistureEnabled" ' + (settings.enabled ? 'checked' : '') + '> Enable Moisture Probe Integration</label>';
            html += '<p style="font-size:12px;color:var(--text-muted);margin-top:4px;">When enabled, soil moisture data from Gophr probes adjusts irrigation durations automatically.</p>';
            html += '</div>';

            // Stale threshold
            html += '<div style="margin-bottom:16px;">';
            html += '<label style="font-size:12px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Stale Reading Threshold</label>';
            html += '<div style="display:grid;grid-template-columns:120px 1fr;gap:10px;align-items:center;">';
            html += '<input type="number" id="cfgMoistureStale" value="' + (settings.stale_reading_threshold_minutes || 120) + '" min="5" max="1440" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;">';
            html += '<span style="font-size:12px;color:var(--text-muted);">minutes — readings older than this are ignored</span>';
            html += '</div></div>';

            // Root Zone Thresholds (gradient-based algorithm)
            const dt = settings.default_thresholds || {};
            html += '<div style="margin-bottom:16px;">';
            html += '<label style="font-size:12px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Root Zone Thresholds (%)</label>';
            html += '<div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">The mid sensor (root zone) drives watering decisions. Shallow detects rain; deep guards against over-irrigation.</div>';
            html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">';
            for (const [key, label, hint] of [
                ['root_zone_skip','Skip (saturated)','Skip watering entirely'],
                ['root_zone_wet','Wet','Reduce watering'],
                ['root_zone_optimal','Optimal','Normal watering (1.0x)'],
                ['root_zone_dry','Dry','Increase watering']
            ]) {
                html += '<div><label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:2px;">' + label + '</label>';
                html += '<input type="number" id="cfgMoistureThresh_' + key + '" value="' + (dt[key] != null ? dt[key] : '') + '" min="0" max="100" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;" title="' + hint + '"></div>';
            }
            html += '</div>';
            html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:8px;">';
            for (const [key, label] of [['max_increase_percent','Max Increase %'], ['max_decrease_percent','Max Decrease %'], ['rain_boost_threshold','Rain Delta']]) {
                html += '<div><label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:2px;">' + label + '</label>';
                html += '<input type="number" id="cfgMoistureThresh_' + key + '" value="' + (dt[key] != null ? dt[key] : '') + '" min="0" max="100" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;"></div>';
            }
            html += '</div></div>';

            html += '<button class="btn btn-primary" onclick="saveMoistureConfig()">Save Moisture Settings</button>';
            html += '<hr style="margin:20px 0;border:none;border-top:1px solid var(--border-light);">';

            // Probe management
            html += '<h3 style="font-size:15px;font-weight:600;margin-bottom:12px;">Gophr Moisture Probes</h3>';

            // Existing probes
            if (probeCount > 0) {
                html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;margin-bottom:16px;">';
                for (const [pid, probe] of Object.entries(probes)) {
                    const ss = probe.sensors || {};
                    const zones = probe.zone_mappings || [];
                    html += '<div style="background:var(--bg-tile);border-radius:10px;padding:12px;border:1px solid var(--border-light);">';
                    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">';
                    html += '<strong style="font-size:14px;">' + esc(probe.display_name || pid) + '</strong>';
                    html += '<button class="btn btn-danger btn-sm" onclick="removeMoistureProbe(\\'' + esc(pid) + '\\')">Remove</button>';
                    html += '</div>';
                    html += '<div style="font-size:12px;color:var(--text-muted);">ID: ' + esc(pid) + '</div>';
                    html += '<div style="font-size:12px;margin-top:4px;"><strong>Sensors:</strong> ' + Object.entries(ss).map(function(e){return e[0] + ' = ' + e[1];}).join(', ') + '</div>';
                    html += '<div style="font-size:12px;margin-top:2px;"><strong>Zones:</strong> ' + (zones.length > 0 ? zones.map(function(z){return z.split(".").pop();}).join(', ') : '<em>None mapped</em>') + '</div>';
                    html += '</div>';
                }
                html += '</div>';
            } else {
                html += '<p style="color:var(--text-muted);margin-bottom:16px;">No probes configured yet. Select a Gophr device below to add a probe.</p>';
            }

            // Device picker for adding probes
            html += '<div style="margin-top:8px;">';
            html += '<label style="font-size:13px;font-weight:600;display:block;margin-bottom:6px;">Add Probe from Device</label>';
            html += '<div style="display:flex;gap:8px;align-items:start;">';
            html += '<div style="flex:1;">';
            html += '<select id="cfgMoistureDeviceSelect" onchange="onMoistureDeviceChange()" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);">';
            html += '<option value="">-- Select a Gophr device --</option>';
            html += '</select>';
            html += '<p id="moistureDeviceFilterToggle" style="display:none;font-size:12px;color:var(--text-muted);margin-top:4px;"></p>';
            html += '</div>';
            html += '<button class="btn btn-secondary btn-sm" onclick="refreshMoistureDevices()" style="white-space:nowrap;">Refresh</button>';
            html += '</div>';
            html += '</div>';
            html += '<div id="cfgMoistureDeviceSensors" style="margin-top:12px;"></div>';

            content.innerHTML = html;
            // Populate device dropdown after rendering
            loadMoistureDevices();
        } catch (e) {
            content.innerHTML = '<div style="color:var(--color-danger);">Failed to load moisture configuration: ' + esc(e.message) + '</div>';
        }
    }

    async function saveMoistureConfig() {
        try {
            const settings = {
                enabled: document.getElementById('cfgMoistureEnabled').checked,
                stale_reading_threshold_minutes: parseInt(document.getElementById('cfgMoistureStale').value) || 120,
                default_thresholds: {
                    root_zone_skip: parseInt(document.getElementById('cfgMoistureThresh_root_zone_skip').value) || 80,
                    root_zone_wet: parseInt(document.getElementById('cfgMoistureThresh_root_zone_wet').value) || 65,
                    root_zone_optimal: parseInt(document.getElementById('cfgMoistureThresh_root_zone_optimal').value) || 45,
                    root_zone_dry: parseInt(document.getElementById('cfgMoistureThresh_root_zone_dry').value) || 30,
                    max_increase_percent: parseInt(document.getElementById('cfgMoistureThresh_max_increase_percent').value) || 50,
                    max_decrease_percent: parseInt(document.getElementById('cfgMoistureThresh_max_decrease_percent').value) || 50,
                    rain_boost_threshold: parseInt(document.getElementById('cfgMoistureThresh_rain_boost_threshold').value) || 15,
                },
            };
            await mcfg('/settings', 'PUT', settings);
            showToast('Moisture settings saved');
            loadMoistureConfig();
        } catch (e) { showToast(e.message, 'error'); }
    }

    let moistureShowingAllDevices = false;

    async function loadMoistureDevices(showAll) {
        const select = document.getElementById('cfgMoistureDeviceSelect');
        if (!select) return;
        try {
            const all = showAll !== undefined ? showAll : moistureShowingAllDevices;
            const data = await mcfg('/devices' + (all ? '?show_all=true' : ''));
            const devices = data.devices || [];
            const totalCount = data.total_count || devices.length;
            const filtered = data.filtered !== false;

            select.innerHTML = '<option value="">-- Select a Gophr device --</option>';
            for (const device of devices) {
                const label = device.manufacturer || device.model
                    ? device.name + ' (' + [device.manufacturer, device.model].filter(Boolean).join(' ') + ')'
                    : device.name;
                const opt = document.createElement('option');
                opt.value = device.id;
                opt.textContent = label;
                select.appendChild(opt);
            }

            const toggleEl = document.getElementById('moistureDeviceFilterToggle');
            if (filtered && devices.length < totalCount) {
                toggleEl.innerHTML = 'Showing ' + devices.length + ' moisture device' + (devices.length !== 1 ? 's' : '') +
                    ' of ' + totalCount + ' total. <a href="#" onclick="showAllMoistureDevices(event)">Show all devices</a>';
                toggleEl.style.display = '';
            } else if (!filtered && totalCount > 0) {
                toggleEl.innerHTML = 'Showing all ' + totalCount + ' devices. <a href="#" onclick="showFilteredMoistureDevices(event)">Show only moisture devices</a>';
                toggleEl.style.display = '';
            } else {
                toggleEl.style.display = 'none';
            }
        } catch (e) {
            select.innerHTML = '<option value="">Failed to load devices</option>';
        }
    }

    function showAllMoistureDevices(e) {
        e.preventDefault();
        moistureShowingAllDevices = true;
        loadMoistureDevices(true);
    }

    function showFilteredMoistureDevices(e) {
        e.preventDefault();
        moistureShowingAllDevices = false;
        loadMoistureDevices(false);
    }

    function refreshMoistureDevices() {
        loadMoistureDevices();
        showToast('Device list refreshed');
    }

    async function onMoistureDeviceChange() {
        const deviceId = document.getElementById('cfgMoistureDeviceSelect').value;
        const el = document.getElementById('cfgMoistureDeviceSensors');
        if (!deviceId) {
            el.innerHTML = '';
            return;
        }
        el.innerHTML = '<div class="loading">Loading sensors for this device...</div>';
        try {
            const data = await mcfg('/devices/' + encodeURIComponent(deviceId) + '/sensors');
            const sensors = data.sensors || [];
            if (sensors.length === 0) {
                el.innerHTML = '<p style="color:var(--text-muted);">No sensor entities found on this device.</p>';
                return;
            }
            let html = '<div style="background:var(--bg-tile);border-radius:8px;padding:12px;border:1px solid var(--border-light);">';
            html += '<div style="font-weight:600;margin-bottom:6px;">' + sensors.length + ' sensor(s) found on this device</div>';
            html += '<div style="font-size:12px;margin-bottom:10px;color:var(--text-muted);">';
            for (const s of sensors) {
                const state = s.state != null ? s.state : '—';
                const unit = s.unit_of_measurement || '';
                html += '<div>' + esc(s.entity_id) + ' = <strong>' + esc(String(state)) + '</strong> ' + esc(unit) + '</div>';
            }
            html += '</div>';

            // Depth mapping dropdowns
            html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:8px;">';
            for (const depth of ['shallow', 'mid', 'deep']) {
                html += '<div><label style="font-size:11px;color:var(--text-muted);">' + depth.charAt(0).toUpperCase() + depth.slice(1) + ' sensor</label>';
                html += '<select id="cfgProbeDevice_' + depth + '" style="width:100%;padding:4px;border:1px solid var(--border-input);border-radius:4px;background:var(--bg-input);color:var(--text-primary);font-size:12px;">';
                html += '<option value="">None</option>';
                for (const s of sensors) {
                    const eidShort = s.entity_id.replace('sensor.', '');
                    const nameLabel = s.friendly_name || eidShort;
                    const auto = s.entity_id.toLowerCase().includes(depth) || (s.friendly_name || '').toLowerCase().includes(depth) ? ' (auto)' : '';
                    const selected = (s.entity_id.toLowerCase().includes(depth) || (s.friendly_name || '').toLowerCase().includes(depth)) ? ' selected' : '';
                    html += '<option value="' + esc(s.entity_id) + '"' + selected + '>' + esc(nameLabel) + auto + '</option>';
                }
                html += '</select></div>';
            }
            html += '</div>';

            // Display name
            html += '<div style="margin-bottom:8px;"><label style="font-size:11px;color:var(--text-muted);">Display Name</label>';
            // Derive a default name from the device
            const select = document.getElementById('cfgMoistureDeviceSelect');
            const deviceName = select.options[select.selectedIndex] ? select.options[select.selectedIndex].textContent : 'Probe';
            html += '<input type="text" id="cfgProbeDevice_name" value="' + esc(deviceName) + '" style="width:100%;padding:4px;border:1px solid var(--border-input);border-radius:4px;background:var(--bg-input);color:var(--text-primary);font-size:12px;"></div>';

            html += '<button class="btn btn-primary btn-sm" onclick="addProbeFromDevice()">Add Probe</button>';
            html += '</div>';
            el.innerHTML = html;
        } catch (e) {
            el.innerHTML = '<div style="color:var(--color-danger);">Failed to load device sensors: ' + esc(e.message) + '</div>';
        }
    }

    async function addProbeFromDevice() {
        try {
            const sensors = {};
            for (const depth of ['shallow', 'mid', 'deep']) {
                const sel = document.getElementById('cfgProbeDevice_' + depth);
                if (sel && sel.value) sensors[depth] = sel.value;
            }
            if (Object.keys(sensors).length === 0) {
                showToast('Select at least one sensor for this probe', 'error');
                return;
            }
            const nameInput = document.getElementById('cfgProbeDevice_name');
            const displayName = nameInput ? nameInput.value.trim() : 'Gophr Probe';

            // Build a probe ID from the display name
            const probeId = 'probe_' + displayName.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');

            // Get all zone entities to map by default
            const zonesRes = await fetch(BASE + '/homeowner/zones');
            const zonesData = await zonesRes.json();
            const allZones = (Array.isArray(zonesData) ? zonesData : zonesData.zones || []).map(function(z) { return z.entity_id; });

            await mcfg('/probes', 'POST', {
                probe_id: probeId,
                display_name: displayName,
                sensors: sensors,
                zone_mappings: allZones,
            });
            showToast('Probe "' + displayName + '" added and mapped to all zones');
            loadMoistureConfig();
        } catch (e) { showToast(e.message, 'error'); }
    }

    async function removeMoistureProbe(probeId) {
        if (!confirm('Remove this moisture probe?')) return;
        try {
            await mcfg('/probes/' + encodeURIComponent(probeId), 'DELETE');
            showToast('Probe removed');
            loadMoistureConfig();
        } catch (e) { showToast(e.message, 'error'); }
    }

    // Load moisture config on page load
    loadMoistureConfig();

    // --- Help Modal ---
    const HELP_CONTENT = `
<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:0 0 8px 0;">Configuration Overview</h4>
<p style="margin-bottom:10px;">This page lets you configure your irrigation system for remote management. You can select your controller device, create API keys, generate connection keys to share with your management company, and configure weather integration.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Irrigation Controller Device</h4>
<p style="margin-bottom:10px;">Select the ESPHome or other irrigation controller device connected to Home Assistant. This tells the add-on which switches, valves, and sensors to expose through the API.</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Select Device</strong> — Choose your controller from the dropdown. The list is filtered to show only irrigation-related devices (matching names like "Flux", "irrigation", "sprinkler", or "ESPHome").</li>
<li style="margin-bottom:4px;"><strong>Show all devices</strong> — If your controller doesn't appear in the filtered list, click "Show all devices" below the dropdown to see every device in Home Assistant.</li>
<li style="margin-bottom:4px;"><strong>Refresh Devices</strong> — Re-scan Home Assistant if your device isn't listed (e.g., after adding a new ESPHome device).</li>
<li style="margin-bottom:4px;"><strong>Entity List</strong> — After selecting a device, you'll see all zones, sensors, and other entities that will be accessible through the API.</li>
</ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 If you change your irrigation controller hardware, re-select the new device here to update the exposed entities.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Management Access Control</h4>
<p style="margin-bottom:10px;">Control your management company's access to your irrigation system. Generate a connection key to grant access, or revoke it instantly. The connection key gives your management company access to all devices — irrigation controller zones, schedules, sensors, moisture probes, weather settings, and run history.</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Connection Method</strong> — Choose how your management company connects:</li>
<li style="margin-bottom:4px;margin-left:16px;"><strong>Nabu Casa (Cloud)</strong> — Uses your Home Assistant Cloud URL. Works from anywhere without port forwarding. Recommended for most users.</li>
<li style="margin-bottom:4px;margin-left:16px;"><strong>Direct (Local/VPN)</strong> — Uses a direct URL you provide. Best for local network or VPN setups.</li>
<li style="margin-bottom:4px;"><strong>Generate Key</strong> — Creates a connection key that contains your URL, credentials, and property details in one encoded string. Share this with your management company.</li>
<li style="margin-bottom:4px;"><strong>🔒 Lock / Unlock</strong> — The generate button locks after a key is created to prevent accidentally overwriting it. Click 🔓 to unlock if you need to regenerate.</li>
<li style="margin-bottom:4px;"><strong>Revoke Access</strong> — Instantly cuts off management company access. They see "Access Revoked" on their dashboard. You can re-generate a new key later to restore access.</li>
</ul>
<p style="margin-bottom:10px;">Share the connection key by:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Copy</strong> — Copy to clipboard and paste into an email or message</li>
<li style="margin-bottom:4px;"><strong>Email</strong> — Opens your email client with the key pre-filled</li>
<li style="margin-bottom:4px;"><strong>QR Code</strong> — Generate a scannable QR code. Your management company can scan this directly from their dashboard using the 📷 Scan QR Code button when adding a property.</li>
</ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 The connection key grants access to all your devices — irrigation zones, Gophr moisture probes, weather settings, schedules, and sensors. If you regenerate a key, the old one stops working immediately. Any changes to your contact info (name, phone, address) are recorded in the configuration change log with old and new values.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Weather Settings</h4>
<p style="margin-bottom:10px;">Enable weather-aware irrigation by connecting a Home Assistant weather entity. When enabled, weather data is used for smart watering adjustments on the Homeowner Dashboard.</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Weather Entity</strong> — Select a weather integration from Home Assistant (e.g., OpenWeatherMap, Met.no, or your local weather station).</li>
<li style="margin-bottom:4px;"><strong>Check Interval</strong> — How often to refresh weather data (5–60 minutes). Lower values give more responsive adjustments but use more API calls.</li>
</ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Weather rules and thresholds (rain skip, wind delay, temperature adjustments, etc.) are configured from the Homeowner Dashboard's weather section.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Gophr Moisture Probes</h4>
<p style="margin-bottom:10px;">Integrate Gophr moisture probes with your irrigation system for data-driven watering adjustments. Expand the Moisture Probes card to configure:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Enable/Disable</strong> — Toggle moisture-aware irrigation on or off</li>
<li style="margin-bottom:4px;"><strong>Select Device</strong> — Choose your Gophr device from the dropdown. The list is filtered to show devices matching "gophr", "moisture", "soil", or "probe". Click "Show all devices" if your device doesn't appear.</li>
<li style="margin-bottom:4px;"><strong>Map Sensors</strong> — After selecting a device, map its sensor entities to shallow, mid, and deep depth readings. Sensors with matching depth names are auto-selected.</li>
<li style="margin-bottom:4px;"><strong>Add Probe</strong> — Creates a probe from the selected device sensors. New probes are mapped to all irrigation zones by default.</li>
<li style="margin-bottom:4px;"><strong>Settings</strong> — Configure stale data threshold, root zone thresholds (Skip, Wet, Optimal, Dry), max increase/decrease percentages, and rain detection sensitivity</li>
<li style="margin-bottom:4px;">Once probes are added and enabled, the Moisture Probes card appears on the Homeowner Dashboard with live readings and zone multipliers</li>
</ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 The combined weather &times; moisture multiplier adjusts both API/dashboard timed runs and ESPHome scheduled durations automatically.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Revoking Access</h4>
<p style="margin-bottom:10px;">If you need to disconnect a management company, use the <strong>Revoke Access</strong> button. This immediately invalidates the current API key and connection key, preventing any further remote access.</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;">All remote API calls will be rejected immediately</li>
<li style="margin-bottom:4px;">Your local irrigation system continues to operate normally</li>
<li style="margin-bottom:4px;">To re-enable access, generate a new connection key and share it with your management company</li>
</ul>
`;

    function showHelp() {
        document.getElementById('helpContent').innerHTML = HELP_CONTENT;
        document.getElementById('helpModal').style.display = 'flex';
    }
    function closeHelpModal() {
        document.getElementById('helpModal').style.display = 'none';
    }
    // Close help modal on Escape key or backdrop click
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && document.getElementById('helpModal').style.display === 'flex') {
            closeHelpModal();
        }
    });
    document.getElementById('helpModal').addEventListener('click', function(e) {
        if (e.target === this) closeHelpModal();
    });

    // --- Init ---
    loadSettings();
    loadConnectionKey();
    loadWeatherSettings();
    loadStatus();
    setInterval(loadStatus, 30000);
</script>
</body>
</html>
"""
