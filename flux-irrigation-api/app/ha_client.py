"""
Home Assistant Supervisor API client.
Communicates with HA to read entity states and call services.
Uses REST API for states/services and WebSocket API for device/entity registry.
"""

import asyncio
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

    async with websockets.connect(
        HA_WS_URL,
        additional_headers=extra_headers,
        open_timeout=10,
        close_timeout=5,
    ) as ws:
        # Step 1: Receive auth_required
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        if msg.get("type") != "auth_required":
            raise ConnectionError(f"Unexpected WS message: {msg}")

        # Step 2: Authenticate
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        if msg.get("type") != "auth_ok":
            raise PermissionError(f"WS authentication failed: {msg}")

        # Step 3: Send command
        await ws.send(json.dumps({"id": 1, "type": command}))
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
        if not msg.get("success"):
            raise RuntimeError(f"WS command '{command}' failed: {msg}")

        return msg.get("result", [])


async def _ws_command_with_data(command: str, data: dict = None):
    """Like _ws_command but supports additional fields in the WebSocket message.

    Used for Lovelace dashboard API calls which require extra payload fields
    (url_path, title, config, etc.) beyond just the command type.
    """
    config = get_config()
    token = config.supervisor_token

    extra_headers = {"Authorization": f"Bearer {token}"}

    async with websockets.connect(
        HA_WS_URL,
        additional_headers=extra_headers,
        open_timeout=10,
        close_timeout=5,
    ) as ws:
        # Step 1: Receive auth_required
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        if msg.get("type") != "auth_required":
            raise ConnectionError(f"Unexpected WS message: {msg}")

        # Step 2: Authenticate
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        if msg.get("type") != "auth_ok":
            raise PermissionError(f"WS authentication failed: {msg}")

        # Step 3: Send command with extra data fields
        payload = {"id": 1, "type": command}
        if data:
            payload.update(data)
        await ws.send(json.dumps(payload))
        msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=30))
        if not msg.get("success"):
            raise RuntimeError(f"WS command '{command}' failed: {msg}")

        return msg.get("result")


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
        result = await _ws_command("config/entity_registry/list")
        print(f"[HA_CLIENT] Entity registry via WebSocket: {len(result)} entities")
        return result
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


import re

# Pattern to identify zone valve switches from ESPHome sprinkler component.
# Matches: switch.{prefix}_zone_{number}  (e.g., switch.irrigation_system_zone_1)
# Does NOT match: switch.{prefix}_enable_zone_{number} or other non-zone switches.
_ZONE_VALVE_PATTERN = re.compile(r"^switch\..+_zone_\d+$")

# Valve domain entities are always zones (non-ESPHome controllers)
_VALVE_DOMAIN = "valve"

# Sensor domains
_SENSOR_DOMAINS = {"sensor", "binary_sensor", "text_sensor"}

# Non-zone switch keywords — switches containing these are controls, not zones
_NON_ZONE_SWITCH_KEYWORDS = {
    "enable", "auto_advance", "start_stop", "resume",
    "schedule", "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday", "restart", "rain_sensor",
    "rain_delay", "12_hour", "time_format",
}


def _is_zone_entity(entity_id: str, name: str) -> bool:
    """Determine if a switch/valve entity is an actual irrigation zone.

    ESPHome sprinkler component creates:
      - switch.*_zone_N  → actual zone valve controls (ZONE)
      - switch.*_enable_zone_N  → zone enable toggles (NOT a zone)
      - switch.*_start_stop_resume  → main switch (NOT a zone)
      - switch.*_auto_advance  → auto advance (NOT a zone)
      - switch.*_schedule_*  → schedule controls (NOT a zone)
      - valve.*  → always a zone (non-ESPHome controllers)
    """
    domain = entity_id.split(".")[0] if "." in entity_id else ""

    # valve.* entities are always zones
    if domain == _VALVE_DOMAIN:
        return True

    if domain != "switch":
        return False

    # Get the part after "switch."
    suffix = entity_id.split(".", 1)[1] if "." in entity_id else entity_id

    # Check for non-zone keywords in the entity_id
    suffix_lower = suffix.lower()
    for keyword in _NON_ZONE_SWITCH_KEYWORDS:
        if keyword in suffix_lower:
            return False

    # Match the zone valve pattern: *_zone_N
    if _ZONE_VALVE_PATTERN.match(entity_id):
        return True

    # Fallback: check the name for "Zone" without "Enable"
    name_lower = (name or "").lower()
    if "zone" in name_lower and "enable" not in name_lower:
        return True

    return False


async def get_device_entities(device_id: str) -> dict:
    """Get all entities belonging to a specific device, categorized intelligently.

    Categories:
      - zones: Actual irrigation zone valve switches (switch.*_zone_N or valve.*)
      - sensors: Sensor readings (sensor.*, binary_sensor.*, text_sensor.*)
      - other: Everything else (number.*, select.*, button.*, light.*, enable switches,
               schedule switches, control switches, etc.)

    Returns:
        {
            "zones": [{"entity_id": "switch.xxx_zone_1", "domain": "switch", ...}, ...],
            "sensors": [{"entity_id": "sensor.xxx", "domain": "sensor", ...}, ...],
            "other": [{"entity_id": "number.xxx", "domain": "number", ...}, ...],
        }
    """
    entities = await get_entity_registry()

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
        name = entity.get("name") or entity.get("original_name", "")
        matched_count += 1

        entry = {
            "entity_id": eid,
            "original_name": entity.get("original_name", ""),
            "name": name,
            "platform": entity.get("platform", ""),
            "domain": domain,
        }

        if _is_zone_entity(eid, name):
            zones.append(entry)
        elif domain in _SENSOR_DOMAINS:
            sensors.append(entry)
        else:
            other.append(entry)

    print(f"[HA_CLIENT] Device {device_id}: {matched_count} total entities, "
          f"{len(zones)} zones, {len(sensors)} sensors, {len(other)} other")
    if matched_count > 0:
        zone_ids = [z["entity_id"] for z in zones]
        print(f"[HA_CLIENT]   Zones: {zone_ids}")
        if other:
            other_ids = [o["entity_id"] for o in other]
            print(f"[HA_CLIENT]   Controls: {other_ids}")
    if matched_count > 0 and len(zones) == 0:
        # Log what we found for debugging
        all_switch_ids = [
            e.get("entity_id", "") for e in entities
            if e.get("device_id") == device_id
            and not e.get("disabled_by")
            and e.get("entity_id", "").startswith("switch.")
        ]
        print(f"[HA_CLIENT]   All switches on device: {all_switch_ids}")

    # Check for expansion board detected_zones sensor
    detected_zones_entity = None
    for s in sensors:
        if "detected_zones" in s["entity_id"].lower():
            detected_zones_entity = s["entity_id"]
            break

    result = {"zones": zones, "sensors": sensors, "other": other}
    if detected_zones_entity:
        result["detected_zones_entity"] = detected_zones_entity
        print(f"[HA_CLIENT]   Expansion sensor found: {detected_zones_entity}")
    return result


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
    """Get states for a specific list of entity IDs.

    For small batches (<=20), fetches individual entity states in parallel
    to avoid the overhead of loading ALL states from HA.
    For larger batches, falls back to fetching all states and filtering.
    """
    if not entity_ids:
        return []

    unique_ids = list(set(entity_ids))

    if len(unique_ids) <= 20:
        # Fetch individual states in parallel — much lighter than get_all_states()
        import asyncio
        tasks = [get_entity_state(eid) for eid in unique_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        states = []
        for eid, result in zip(unique_ids, results):
            if isinstance(result, dict):
                states.append(result)
        return states
    else:
        # Large batch — fetch all states and filter
        all_states = await get_all_states()
        allowed = set(unique_ids)
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
        if response.status_code != 200:
            print(f"[HA_CLIENT] Service call {domain}.{service} failed: "
                  f"status={response.status_code}, payload={payload}, "
                  f"response={response.text[:200]}")
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
