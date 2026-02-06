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
            verify=False,  # Allow self-signed certs for DuckDNS/local setups
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
            # Non-JSON response — likely hitting the wrong server (HA on 8123 instead of add-on on 8099)
            raw = response.text[:200].strip()
            data = {"raw": f"{response.status_code}: {raw}"}
        return response.status_code, data
    except httpx.ConnectError as e:
        print(f"[MGMT_CLIENT] ConnectError to {url}: {e}")
        # Detect Nabu Casa URLs — they don't forward add-on ports
        if ".ui.nabu.casa" in url or ".nabucasa.com" in url:
            return 503, {
                "error": "Nabu Casa URLs cannot be used for API connections",
                "detail": (
                    "Nabu Casa only proxies HA's web interface (port 8123), not add-on ports like 8099. "
                    "The homeowner needs to use router port forwarding + DuckDNS, Cloudflare Tunnel, or Tailscale."
                ),
            }
        return 503, {
            "error": "Cannot connect to homeowner system",
            "detail": f"Connection refused or host unreachable: {url}",
        }
    except httpx.TimeoutException:
        print(f"[MGMT_CLIENT] Timeout connecting to {url}")
        # Detect Nabu Casa URLs — they always timeout on non-8123 ports
        if ".ui.nabu.casa" in url or ".nabucasa.com" in url:
            return 504, {
                "error": "Nabu Casa URLs cannot be used for API connections",
                "detail": (
                    "Nabu Casa only proxies HA's web interface (port 8123), not add-on ports like 8099. "
                    "The homeowner needs to use router port forwarding + DuckDNS, Cloudflare Tunnel, or Tailscale."
                ),
            }
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


def _diagnose_error(status: int, response_data: dict, url: str) -> str:
    """Analyze a failed response and produce a helpful diagnostic message."""
    # Detect Nabu Casa URLs — they never work for add-on API traffic
    if ".ui.nabu.casa" in url or ".nabucasa.com" in url:
        return (
            "Nabu Casa URLs cannot be used for API connections. "
            "Nabu Casa only proxies HA's web interface (port 8123), not add-on ports like 8099. "
            "The homeowner needs to set up router port forwarding + DuckDNS, Cloudflare Tunnel, or Tailscale."
        )

    raw = response_data.get("raw", "")

    # Detect plain-text 404 — hallmark of hitting HA's web server on port 8123
    if status == 404 and ("Not Found" in raw or "404" in raw) and "detail" not in response_data:
        # Check if URL is missing port 8099
        from urllib.parse import urlparse
        parsed = urlparse(url)
        port = parsed.port
        if port is None or port in (80, 443, 8123):
            return (
                f"Got a plain 404 from {parsed.hostname} — this looks like Home Assistant's "
                f"web server, not the Flux Irrigation API. The connection key URL must "
                f"include port 8099 (e.g., http://{parsed.hostname}:8099). "
                f"Port 8099 must also be forwarded on the homeowner's router."
            )
        return (
            f"Got a plain 404 from {url}. The server responded but doesn't have the "
            f"Flux Irrigation API. Check that the add-on is running on the homeowner's HA instance."
        )

    # Detect JSON 404 from our own API (mode guard or wrong path)
    if status == 404 and "detail" in response_data:
        return response_data["detail"]

    return _error_to_string(response_data)


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
        error_msg = _diagnose_error(status, health, connection.url)
        print(f"[MGMT_CLIENT] Health check failed: status={status}, error={error_msg}")
        return {"reachable": False, "authenticated": False, "error": error_msg}

    # Verify the health response looks like our API (not some random server)
    if not isinstance(health, dict) or "status" not in health:
        return {
            "reachable": False,
            "authenticated": False,
            "error": (
                f"The server at {connection.url} responded, but it doesn't appear to be "
                f"a Flux Irrigation API. Make sure the URL points to port 8099."
            ),
        }

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
        error_msg = _diagnose_error(status, system_status, connection.url)
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
