"""
Admin settings endpoints and web UI.
Allows the homeowner to configure API keys, entity prefixes,
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


def _save_options(options: dict):
    """Save options to persistent storage and reload config."""
    os.makedirs(os.path.dirname(OPTIONS_FILE), exist_ok=True)
    with open(OPTIONS_FILE, "w") as f:
        json.dump(options, f, indent=2)
    reload_config()


# --- API Endpoints for Settings ---


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    permissions: list[str] = []


class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[list[str]] = None
    regenerate_key: bool = False


class PrefixUpdate(BaseModel):
    irrigation_entity_prefix: Optional[str] = None
    sensor_entity_prefix: Optional[str] = None


class SettingsUpdate(BaseModel):
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=300)
    log_retention_days: Optional[int] = Field(None, ge=1, le=365)
    enable_audit_log: Optional[bool] = None


@router.get("/api/settings", summary="Get current settings")
async def get_settings():
    """Get all current add-on settings."""
    options = _load_options()
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
        "api_keys": api_keys,
        "irrigation_entity_prefix": options.get("irrigation_entity_prefix", "switch.irrigation_"),
        "sensor_entity_prefix": options.get("sensor_entity_prefix", "sensor.irrigation_"),
        "rate_limit_per_minute": options.get("rate_limit_per_minute", 60),
        "log_retention_days": options.get("log_retention_days", 30),
        "enable_audit_log": options.get("enable_audit_log", True),
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
    _save_options(options)

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
    _save_options(options)

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
    _save_options(options)

    return {"success": True, "removed": removed["name"]}


@router.put("/api/prefixes", summary="Update entity prefixes")
async def update_prefixes(body: PrefixUpdate):
    """Update the entity prefixes used to discover irrigation entities."""
    options = _load_options()

    if body.irrigation_entity_prefix is not None:
        options["irrigation_entity_prefix"] = body.irrigation_entity_prefix
    if body.sensor_entity_prefix is not None:
        options["sensor_entity_prefix"] = body.sensor_entity_prefix

    _save_options(options)
    return {"success": True}


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

    _save_options(options)
    return {"success": True}


@router.get("/api/discover", summary="Discover irrigation entities")
async def discover_entities():
    """Scan Home Assistant for entities that could be irrigation-related."""
    import ha_client

    all_states = await ha_client.get_all_states()

    # Look for common irrigation-related patterns
    irrigation_keywords = [
        "irrigation", "sprinkler", "zone", "valve", "water",
        "lawn", "garden", "drip", "spray",
    ]
    sensor_keywords = [
        "moisture", "soil", "rain", "flow", "humidity",
        "precipitation", "water_level",
    ]

    switches = []
    sensors = []

    for entity in all_states:
        eid = entity.get("entity_id", "").lower()
        fname = entity.get("attributes", {}).get("friendly_name", "").lower()
        combined = f"{eid} {fname}"

        if eid.startswith("switch."):
            if any(kw in combined for kw in irrigation_keywords):
                switches.append({
                    "entity_id": entity["entity_id"],
                    "friendly_name": entity.get("attributes", {}).get("friendly_name", ""),
                    "state": entity.get("state", "unknown"),
                })

        elif eid.startswith("sensor."):
            if any(kw in combined for kw in sensor_keywords + irrigation_keywords):
                sensors.append({
                    "entity_id": entity["entity_id"],
                    "friendly_name": entity.get("attributes", {}).get("friendly_name", ""),
                    "state": entity.get("state", "unknown"),
                    "unit": entity.get("attributes", {}).get("unit_of_measurement", ""),
                })

    return {
        "discovered_switches": switches,
        "discovered_sensors": sensors,
        "suggestion": {
            "irrigation_entity_prefix": _suggest_prefix([s["entity_id"] for s in switches]),
            "sensor_entity_prefix": _suggest_prefix([s["entity_id"] for s in sensors]),
        },
    }


def _suggest_prefix(entity_ids: list[str]) -> str:
    """Try to find a common prefix among entity IDs."""
    if not entity_ids:
        return ""
    if len(entity_ids) == 1:
        # Use everything up to the last underscore + digit
        eid = entity_ids[0]
        parts = eid.rsplit("_", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0] + "_"
        return eid
    # Find common prefix
    prefix = os.path.commonprefix(entity_ids)
    return prefix


# --- Web UI ---


@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def admin_ui(request: Request):
    """Serve the admin settings UI."""
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

        .discover-results {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #eee;
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
            display: none;
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
        .entity-state { color: #888; }

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
    </style>
</head>
<body>

<div class="header">
    <div>
        <h1>🌱 Flux Irrigation Management API</h1>
        <div class="subtitle">Configure API access for irrigation management companies</div>
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

    <!-- Entity Prefixes -->
    <div class="card">
        <div class="card-header">
            <h2>Entity Configuration</h2>
            <button class="btn btn-secondary btn-sm" onclick="discoverEntities()">🔍 Auto-Discover</button>
        </div>
        <div class="card-body">
            <div class="form-row">
                <div class="form-group">
                    <label>Irrigation Zone Prefix</label>
                    <input type="text" id="irrigationPrefix" placeholder="switch.irrigation_">
                </div>
                <div class="form-group">
                    <label>Sensor Prefix</label>
                    <input type="text" id="sensorPrefix" placeholder="sensor.irrigation_">
                </div>
            </div>
            <button class="btn btn-primary" onclick="savePrefixes()">Save Prefixes</button>

            <div class="discover-results" id="discoverResults">
                <strong>Discovered Entities</strong>
                <div id="discoverSwitches"></div>
                <div id="discoverSensors"></div>
                <div id="discoverSuggestion" style="margin-top:12px;"></div>
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
                <strong>🔑 New API Key Created</strong>
                <code id="newKeyValue"></code>
                <p class="warning">⚠️ Copy this key now — it will not be shown again!</p>
                <button class="btn btn-secondary btn-sm" onclick="copyKey()">📋 Copy to Clipboard</button>
            </div>

            <div id="apiKeysList"></div>
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
            <a href="/api/docs" target="_blank" class="btn btn-primary">Open API Docs (Swagger UI)</a>
        </div>
    </div>

</div>

<div class="toast" id="toast"></div>

<script>
    const BASE = '/admin/api';

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

            document.getElementById('irrigationPrefix').value = data.irrigation_entity_prefix || '';
            document.getElementById('sensorPrefix').value = data.sensor_entity_prefix || '';
            document.getElementById('rateLimit').value = data.rate_limit_per_minute || 60;
            document.getElementById('logRetention').value = data.log_retention_days || 30;
            document.getElementById('auditLogEnabled').checked = data.enable_audit_log !== false;

            renderApiKeys(data.api_keys || []);
        } catch (e) {
            showToast('Failed to load settings', 'error');
        }
    }

    // --- Status ---
    async function loadStatus() {
        try {
            const res = await fetch('/api/system/health');
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
                        <button class="btn btn-secondary btn-sm" onclick="regenerateKey(${i})">🔄 Regenerate</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteKey(${i}, '${escHtml(key.name)}')">Delete</button>
                    </div>
                </div>
                <div class="permissions-grid">
                    ${['zones.read','zones.control','schedule.read','schedule.write','sensors.read','history.read','system.control'].map(p => `
                        <label class="perm-checkbox">
                            <input type="checkbox" ${(key.permissions||[]).includes(p) ? 'checked' : ''} onchange="updateKeyPermissions(${i})">
                            ${p.replace('.', ': ').replace(/\b\w/g, c => c.toUpperCase())}
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
        const perms = [...card.querySelectorAll('input[type=checkbox]:checked')]
            .map(c => c.parentElement.textContent.trim().toLowerCase().replace(': ', '.'));
        // Map display names back to permission strings
        const permMap = {
            'zones: read': 'zones.read', 'zones: control': 'zones.control',
            'schedule: read': 'schedule.read', 'schedule: write': 'schedule.write',
            'sensors: read': 'sensors.read', 'history: read': 'history.read',
            'system: control': 'system.control',
        };
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

    // --- Prefixes ---
    async function savePrefixes() {
        try {
            await fetch(`${BASE}/prefixes`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    irrigation_entity_prefix: document.getElementById('irrigationPrefix').value,
                    sensor_entity_prefix: document.getElementById('sensorPrefix').value,
                }),
            });
            showToast('Entity prefixes saved');
        } catch (e) {
            showToast('Failed to save prefixes', 'error');
        }
    }

    // --- Discover ---
    async function discoverEntities() {
        try {
            const res = await fetch(`${BASE}/discover`);
            const data = await res.json();
            const container = document.getElementById('discoverResults');
            container.style.display = 'block';

            const swDiv = document.getElementById('discoverSwitches');
            swDiv.innerHTML = '<p style="margin:8px 0; font-weight:600;">Switches (possible zones):</p>' +
                (data.discovered_switches.length ? data.discovered_switches.map(e =>
                    `<div class="entity-item"><span class="entity-id">${escHtml(e.entity_id)}</span><span>${escHtml(e.friendly_name)}</span><span class="entity-state">${e.state}</span></div>`
                ).join('') : '<p style="color:#999;">None found</p>');

            const senDiv = document.getElementById('discoverSensors');
            senDiv.innerHTML = '<p style="margin:8px 0; font-weight:600;">Sensors:</p>' +
                (data.discovered_sensors.length ? data.discovered_sensors.map(e =>
                    `<div class="entity-item"><span class="entity-id">${escHtml(e.entity_id)}</span><span>${escHtml(e.friendly_name)}</span><span class="entity-state">${e.state} ${e.unit||''}</span></div>`
                ).join('') : '<p style="color:#999;">None found</p>');

            const sug = data.suggestion;
            if (sug.irrigation_entity_prefix || sug.sensor_entity_prefix) {
                document.getElementById('discoverSuggestion').innerHTML =
                    `<button class="btn btn-secondary btn-sm" onclick="applySuggestion('${escHtml(sug.irrigation_entity_prefix)}','${escHtml(sug.sensor_entity_prefix)}')">` +
                    `Apply suggested prefixes</button>`;
            }
        } catch (e) {
            showToast('Discovery failed', 'error');
        }
    }

    function applySuggestion(irr, sen) {
        if (irr) document.getElementById('irrigationPrefix').value = irr;
        if (sen) document.getElementById('sensorPrefix').value = sen;
        showToast('Suggestions applied — click Save Prefixes to confirm');
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

    // --- Init ---
    loadSettings();
    loadStatus();
    setInterval(loadStatus, 30000);
</script>
</body>
</html>
"""
