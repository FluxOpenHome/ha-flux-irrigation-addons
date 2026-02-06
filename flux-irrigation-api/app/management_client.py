"""
Flux Open Home - Management Client
====================================
HTTP client for management mode. Connects to remote homeowner
irrigation APIs using connection key credentials.
"""

import httpx
from typing import Optional
from connection_key import ConnectionKeyData

_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            verify=True,
        )
    return _client


async def proxy_request(
    connection: ConnectionKeyData,
    method: str,
    path: str,
    json_body: Optional[dict] = None,
    params: Optional[dict] = None,
) -> tuple[int, dict]:
    """
    Send a request to a remote homeowner's irrigation API.
    Returns (status_code, response_json).
    """
    client = _get_client()
    url = f"{connection.url.rstrip('/')}{path}"
    headers = {
        "X-API-Key": connection.key,
        "Content-Type": "application/json",
    }

    try:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=json_body,
            params=params,
        )
        try:
            data = response.json()
        except Exception:
            data = {"raw": response.text}
        return response.status_code, data
    except httpx.ConnectError:
        return 503, {
            "error": "Cannot connect to homeowner system",
            "detail": "Connection refused or host unreachable",
        }
    except httpx.TimeoutException:
        return 504, {
            "error": "Homeowner system timeout",
            "detail": "Request timed out after 15 seconds",
        }
    except Exception as e:
        return 502, {
            "error": "Communication error",
            "detail": str(e),
        }


async def check_homeowner_connection(connection: ConnectionKeyData) -> dict:
    """
    Test connectivity to a homeowner's system.
    Phase 1: /api/system/health (no auth) to check reachability.
    Phase 2: /api/system/status (with auth) to verify API key.
    """
    # Phase 1: health check (no auth required)
    status, health = await proxy_request(connection, "GET", "/api/system/health")
    if status != 200:
        return {"reachable": False, "authenticated": False, "error": health}

    # Phase 2: authenticated status check
    status, system_status = await proxy_request(
        connection, "GET", "/api/system/status"
    )
    if status == 401:
        return {
            "reachable": True,
            "authenticated": False,
            "error": "API key rejected",
        }
    if status == 403:
        return {
            "reachable": True,
            "authenticated": False,
            "error": "API key lacks permissions",
        }
    if status != 200:
        return {
            "reachable": True,
            "authenticated": False,
            "error": system_status,
        }

    return {
        "reachable": True,
        "authenticated": True,
        "system_status": system_status,
    }
