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
    except httpx.ConnectError as e:
        print(f"[MGMT_CLIENT] ConnectError to {url}: {e}")
        return 503, {
            "error": "Cannot connect to homeowner system",
            "detail": f"Connection refused or host unreachable: {url}",
        }
    except httpx.TimeoutException:
        print(f"[MGMT_CLIENT] Timeout connecting to {url}")
        return 504, {
            "error": "Homeowner system timeout",
            "detail": f"Request timed out after 15 seconds: {url}",
        }
    except Exception as e:
        print(f"[MGMT_CLIENT] Error connecting to {url}: {type(e).__name__}: {e}")
        return 502, {
            "error": "Communication error",
            "detail": str(e),
        }


def _error_to_string(err) -> str:
    """Convert an error value (str, dict, or other) to a readable string."""
    if isinstance(err, str):
        return err
    if isinstance(err, dict):
        # Try common keys for a human-readable message
        return err.get("detail") or err.get("error") or err.get("message") or str(err)
    return str(err)


async def check_homeowner_connection(connection: ConnectionKeyData) -> dict:
    """
    Test connectivity to a homeowner's system.
    Phase 1: /api/system/health (no auth) to check reachability.
    Phase 2: /api/system/status (with auth) to verify API key.
    """
    print(f"[MGMT_CLIENT] Testing connection to {connection.url}")

    # Phase 1: health check (no auth required)
    status, health = await proxy_request(connection, "GET", "/api/system/health")
    if status != 200:
        error_msg = _error_to_string(health)
        print(f"[MGMT_CLIENT] Health check failed: status={status}, error={error_msg}")
        return {"reachable": False, "authenticated": False, "error": error_msg}

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
        error_msg = _error_to_string(system_status)
        return {
            "reachable": True,
            "authenticated": False,
            "error": error_msg,
        }

    return {
        "reachable": True,
        "authenticated": True,
        "system_status": system_status,
    }
