"""
Home Assistant Supervisor API client.
Communicates with HA to read entity states and call services.
"""

import httpx
from typing import Any, Optional
from config import get_config


HA_BASE_URL = "http://supervisor/core/api"


def _get_headers() -> dict:
    config = get_config()
    return {
        "Authorization": f"Bearer {config.supervisor_token}",
        "Content-Type": "application/json",
    }


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


async def get_entities_by_prefix(prefix: str) -> list[dict]:
    """Get all entities matching a given prefix."""
    all_states = await get_all_states()
    return [s for s in all_states if s.get("entity_id", "").startswith(prefix)]


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
