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

    async with websockets.connect(HA_WS_URL) as ws:
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
    """Get all registered devices from Home Assistant."""
    return await _ws_command("config/device_registry/list")


async def get_entity_registry() -> list[dict]:
    """Get all registered entities from Home Assistant."""
    return await _ws_command("config/entity_registry/list")


async def get_device_entities(device_id: str) -> dict:
    """Get all entities belonging to a specific device, categorized by domain.

    Returns:
        {
            "zones": [{"entity_id": "switch.xxx", ...}, ...],
            "sensors": [{"entity_id": "sensor.xxx", ...}, ...],
        }
    """
    entities = await get_entity_registry()

    zones = []
    sensors = []

    for entity in entities:
        if entity.get("device_id") != device_id:
            continue
        if entity.get("disabled_by"):
            continue

        eid = entity.get("entity_id", "")
        entry = {
            "entity_id": eid,
            "original_name": entity.get("original_name", ""),
            "name": entity.get("name") or entity.get("original_name", ""),
            "platform": entity.get("platform", ""),
        }

        if eid.startswith("switch."):
            zones.append(entry)
        elif eid.startswith("sensor."):
            sensors.append(entry)

    return {"zones": zones, "sensors": sensors}


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
