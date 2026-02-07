"""
Home Assistant Supervisor API client.
Communicates with HA to read entity states and call services.
Uses REST API for states/services and WebSocket API for device/entity registry.
"""

import json
import httpx
import websockets
from typing import Optional
from config import get_config


HA_BASE_URL = "http://supervisor/core/api"
HA_WS_URL = "ws://supervisor/core/websocket"


def _get_headers() -> dict:
    config = get_config()
    return {
        "Authorization": f"Bearer {config.supervisor_token}",
        "Content-Type": "application/json",
    }


# --- WebSocket helpers for device/entity registry ---


async def _ws_command(command: str) -> list[dict]:
    """Connect to HA WebSocket, authenticate, run a single command, and return the result."""
    config = get_config()
    token = config.supervisor_token

    # Pass auth header during WebSocket upgrade handshake (required by Supervisor proxy)
    extra_headers = {"Authorization": f"Bearer {token}"}

    async with websockets.connect(HA_WS_URL, additional_headers=extra_headers) as ws:
        # Step 1: Receive auth_required
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_required":
            raise ConnectionError(f"Unexpected WS message: {msg}")

        # Step 2: Authenticate
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_ok":
            raise PermissionError(f"WS authentication failed: {msg}")

        # Step 3: Send command
        await ws.send(json.dumps({"id": 1, "type": command}))
        msg = json.loads(await ws.recv())
        if not msg.get("success"):
            raise RuntimeError(f"WS command '{command}' failed: {msg}")

        return msg.get("result", [])


async def get_device_registry() -> list[dict]:
    """Get all registered devices from Home Assistant.

    Uses the template API as a reliable fallback since WebSocket auth
    through the Supervisor proxy can fail with SUPERVISOR_TOKEN.
    """
    try:
        return await _ws_command("config/device_registry/list")
    except Exception as ws_err:
        print(f"[HA_CLIENT] WebSocket device registry failed ({ws_err}), using template API fallback")
        return await _get_devices_via_template()


async def _get_devices_via_template() -> list[dict]:
    """Get devices using the template API (REST-based fallback).

    Uses pipe-delimited format to avoid JSON escaping issues.
    """
    template = """{%- set ns = namespace(devices=[]) -%}
{%- for state in states -%}
  {%- set did = device_id(state.entity_id) -%}
  {%- if did and did not in ns.devices -%}
    {%- set ns.devices = ns.devices + [did] -%}
  {%- endif -%}
{%- endfor -%}
{%- for did in ns.devices -%}
{%- set d_name = device_attr(did, 'name') or '' -%}
{%- set d_name_by_user = device_attr(did, 'name_by_user') or '' -%}
{%- set d_manufacturer = device_attr(did, 'manufacturer') or '' -%}
{%- set d_model = device_attr(did, 'model') or '' -%}
{%- set d_area = device_attr(did, 'area_id') or '' -%}
{{ did }}|{{ (d_name_by_user or d_name) | replace('|', ' ') }}|{{ d_manufacturer | replace('|', ' ') }}|{{ d_model | replace('|', ' ') }}|{{ d_area }}
{% endfor -%}"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{HA_BASE_URL}/template",
            headers=_get_headers(),
            json={"template": template},
            timeout=30.0,
        )
        if response.status_code == 200:
            devices = []
            for line in response.text.strip().split("\n"):
                line = line.strip()
                if not line or "|" not in line:
                    continue
                parts = line.split("|", 4)
                if len(parts) >= 2:
                    devices.append({
                        "id": parts[0].strip(),
                        "name": parts[1].strip() if len(parts) > 1 else "",
                        "manufacturer": parts[2].strip() if len(parts) > 2 else "",
                        "model": parts[3].strip() if len(parts) > 3 else "",
                        "area_id": parts[4].strip() if len(parts) > 4 else "",
                    })
            print(f"[HA_CLIENT] Template fallback returned {len(devices)} devices")
            return devices
        else:
            print(f"[HA_CLIENT] Template API returned {response.status_code}: {response.text[:200]}")
            return []


async def get_entity_registry() -> list[dict]:
    """Get all registered entities from Home Assistant.

    Uses the template API as a reliable fallback since WebSocket auth
    through the Supervisor proxy can fail with SUPERVISOR_TOKEN.
    """
    try:
        return await _ws_command("config/entity_registry/list")
    except Exception as ws_err:
        print(f"[HA_CLIENT] WebSocket entity registry failed ({ws_err}), using template API fallback")
        return await _get_entities_via_template()


async def _get_entities_via_template() -> list[dict]:
    """Get entities with device_id using the template API (REST-based fallback).

    Uses a simple line-per-entity format to avoid JSON escaping issues in Jinja,
    then parses the lines into dicts.
    """
    # Output one line per entity: entity_id|device_id|name
    # Using pipe-delimited format avoids all JSON/quote escaping problems
    template = """{%- for state in states -%}
{{ state.entity_id }}|{{ device_id(state.entity_id) or '' }}|{{ state.name | replace('|', ' ') }}
{% endfor -%}"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{HA_BASE_URL}/template",
            headers=_get_headers(),
            json={"template": template},
            timeout=30.0,
        )
        if response.status_code == 200:
            entities = []
            for line in response.text.strip().split("\n"):
                line = line.strip()
                if not line or "|" not in line:
                    continue
                parts = line.split("|", 2)
                if len(parts) >= 2:
                    eid = parts[0].strip()
                    did = parts[1].strip()
                    name = parts[2].strip() if len(parts) > 2 else ""
                    entities.append({
                        "entity_id": eid,
                        "device_id": did,
                        "name": name,
                        "original_name": name,
                        "disabled_by": None,
                        "platform": "",
                    })
            print(f"[HA_CLIENT] Template fallback returned {len(entities)} entities")
            return entities
        else:
            print(f"[HA_CLIENT] Entity template API returned {response.status_code}: {response.text[:200]}")
            return []


async def get_device_entities(device_id: str) -> dict:
    """Get all entities belonging to a specific device, categorized by domain.

    Zones can be switch.* or valve.* entities (irrigation controllers vary).
    Sensors include sensor.* and binary_sensor.* entities.
    All other entity types are included in the "other" list for full visibility.

    Returns:
        {
            "zones": [{"entity_id": "switch.xxx", "domain": "switch", ...}, ...],
            "sensors": [{"entity_id": "sensor.xxx", "domain": "sensor", ...}, ...],
            "other": [{"entity_id": "number.xxx", "domain": "number", ...}, ...],
        }
    """
    entities = await get_entity_registry()

    # Domains that represent controllable irrigation zones
    # ESPHome sprinkler component creates switch.* for valve controls and enable toggles
    # valve.* is included for non-ESPHome controllers that use the valve domain
    ZONE_DOMAINS = {"switch", "valve"}
    # Domains that represent sensor readings
    # text_sensor covers ESPHome text_sensor entities (Status, Time Remaining, Progress, etc.)
    SENSOR_DOMAINS = {"sensor", "binary_sensor", "text_sensor"}

    zones = []
    sensors = []
    other = []
    matched_count = 0

    for entity in entities:
        if entity.get("device_id") != device_id:
            continue
        if entity.get("disabled_by"):
            continue

        eid = entity.get("entity_id", "")
        domain = eid.split(".")[0] if "." in eid else ""
        matched_count += 1

        entry = {
            "entity_id": eid,
            "original_name": entity.get("original_name", ""),
            "name": entity.get("name") or entity.get("original_name", ""),
            "platform": entity.get("platform", ""),
            "domain": domain,
        }

        if domain in ZONE_DOMAINS:
            zones.append(entry)
        elif domain in SENSOR_DOMAINS:
            sensors.append(entry)
        else:
            other.append(entry)

    print(f"[HA_CLIENT] Device {device_id}: {matched_count} total entities, "
          f"{len(zones)} zones, {len(sensors)} sensors, {len(other)} other")
    if matched_count > 0 and len(zones) == 0 and len(sensors) == 0:
        # Log what domains we did find for debugging
        all_domains = set()
        for entity in entities:
            if entity.get("device_id") == device_id and not entity.get("disabled_by"):
                eid = entity.get("entity_id", "")
                if "." in eid:
                    all_domains.add(eid.split(".")[0])
        print(f"[HA_CLIENT] Entity domains found on device: {all_domains}")

    return {"zones": zones, "sensors": sensors, "other": other}


# --- REST API helpers ---


async def get_entity_state(entity_id: str) -> Optional[dict]:
    """Get the current state of a single entity."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{HA_BASE_URL}/states/{entity_id}",
            headers=_get_headers(),
            timeout=10.0,
        )
        if response.status_code == 200:
            return response.json()
        return None


async def get_all_states() -> list[dict]:
    """Get all entity states from Home Assistant."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{HA_BASE_URL}/states",
            headers=_get_headers(),
            timeout=15.0,
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_entities_by_ids(entity_ids: list[str]) -> list[dict]:
    """Get states for a specific list of entity IDs."""
    if not entity_ids:
        return []
    all_states = await get_all_states()
    allowed = set(entity_ids)
    return [s for s in all_states if s.get("entity_id", "") in allowed]


async def call_service(
    domain: str, service: str, data: Optional[dict] = None
) -> bool:
    """Call a Home Assistant service."""
    payload = data or {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{HA_BASE_URL}/services/{domain}/{service}",
            headers=_get_headers(),
            json=payload,
            timeout=15.0,
        )
        return response.status_code == 200


async def get_history(
    entity_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> list:
    """Get entity history from Home Assistant."""
    params = {}
    url = f"{HA_BASE_URL}/history/period"
    if start_time:
        url = f"{HA_BASE_URL}/history/period/{start_time}"
    if end_time:
        params["end_time"] = end_time
    params["filter_entity_id"] = entity_id
    params["minimal_response"] = "true"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=_get_headers(),
            params=params,
            timeout=30.0,
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_logbook(
    entity_id: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> list:
    """Get logbook entries from Home Assistant."""
    params = {}
    url = f"{HA_BASE_URL}/logbook"
    if start_time:
        url = f"{HA_BASE_URL}/logbook/{start_time}"
    if end_time:
        params["end_time"] = end_time
    if entity_id:
        params["entity"] = entity_id

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=_get_headers(),
            params=params,
            timeout=30.0,
        )
        if response.status_code == 200:
            return response.json()
        return []


async def fire_event(event_type: str, event_data: Optional[dict] = None) -> bool:
    """Fire a Home Assistant event."""
    payload = event_data or {}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{HA_BASE_URL}/events/{event_type}",
            headers=_get_headers(),
            json=payload,
            timeout=10.0,
        )
        return response.status_code == 200


async def check_connection() -> bool:
    """Check if the connection to Home Assistant is working."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{HA_BASE_URL}/",
                headers=_get_headers(),
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False
