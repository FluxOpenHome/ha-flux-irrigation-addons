"""
Flux Open Home - Management Client
====================================
HTTP client for management mode. Connects to remote homeowner
irrigation APIs using connection key credentials.

Supports two connection modes:
  - "direct": Connect directly to homeowner's add-on (port 8099)
  - "nabu_casa": Route through HA REST API → rest_command proxy → add-on
"""

import json
import httpx
from typing import Optional
from connection_key import ConnectionKeyData

_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=20.0,
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
    extra_headers: Optional[dict] = None,
) -> tuple[int, dict]:
    """
    Send a request to a remote homeowner's irrigation API.
    Routes through HA REST API proxy for nabu_casa mode.
    Returns (status_code, response_json).
    """
    # Validate URL before attempting any request
    url = (connection.url or "").strip()
    print(f"[MGMT_CLIENT] proxy_request: url='{url}', mode='{connection.mode}', ha_token={'SET' if connection.ha_token else 'EMPTY'}, method={method}, path={path}")
    if not url:
        return 400, {"error": "No URL configured", "detail": "The connection key has no URL. Remove and re-add this customer with a valid connection key."}
    if not url.startswith("http://") and not url.startswith("https://"):
        return 400, {"error": "Invalid URL", "detail": f"URL must start with http:// or https:// — got: {url[:50]}"}

    if connection.mode == "nabu_casa" and connection.ha_token:
        return await _proxy_via_nabu_casa(connection, method, path, json_body, params, extra_headers)

    # If mode is nabu_casa but token is missing, give a clear error
    if connection.mode == "nabu_casa" and not connection.ha_token:
        return 400, {
            "error": "Missing HA token",
            "detail": "This customer uses Nabu Casa mode but the HA Long-Lived Access Token is missing. Re-generate the connection key on the homeowner side.",
        }

    return await _proxy_direct(connection, method, path, json_body, params, extra_headers)


async def _proxy_direct(
    connection: ConnectionKeyData,
    method: str,
    path: str,
    json_body: Optional[dict] = None,
    params: Optional[dict] = None,
    extra_headers: Optional[dict] = None,
) -> tuple[int, dict]:
    """Direct HTTP connection to homeowner's add-on on port 8099."""
    client = _get_client()
    url = f"{connection.url.rstrip('/')}{path}"
    headers = {
        "X-API-Key": connection.key,
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

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
            raw = response.text[:200].strip()
            data = {"raw": f"{response.status_code}: {raw}"}
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
            "detail": f"Request timed out after 20 seconds: {url}",
        }
    except Exception as e:
        print(f"[MGMT_CLIENT] Error connecting to {url}: {type(e).__name__}: {e}")
        return 502, {
            "error": "Communication error",
            "detail": str(e),
        }


async def _proxy_via_nabu_casa(
    connection: ConnectionKeyData,
    method: str,
    path: str,
    json_body: Optional[dict] = None,
    params: Optional[dict] = None,
    extra_headers: Optional[dict] = None,
) -> tuple[int, dict]:
    """
    Route request through HA REST API → rest_command/irrigation_proxy_*.

    The homeowner's HA has per-method rest_commands (irrigation_proxy_get,
    irrigation_proxy_post, etc.) that forward requests to localhost:8099.
    We call the appropriate one via:
      POST {nabu_casa_url}/api/services/rest_command/irrigation_proxy_{method}?return_response

    The HA REST API returns:
      { "service_response": { "status": 200, "content": "...", "headers": {...} } }
    """
    client = _get_client()
    base_url = connection.url.rstrip("/")

    # Pick the correct per-method rest_command service
    method_lower = method.lower()
    if method_lower not in ("get", "post", "put", "delete"):
        return 400, {"error": f"Unsupported HTTP method: {method}"}
    service_name = f"irrigation_proxy_{method_lower}"
    service_url = f"{base_url}/api/services/rest_command/{service_name}?return_response"

    # Build the full path with query params if any
    all_params = dict(params) if params else {}
    # Pass extra headers as query params since Nabu Casa rest_command
    # proxy doesn't support custom HTTP headers to the add-on
    if extra_headers:
        for k, v in extra_headers.items():
            all_params[k] = v
    full_path = path
    if all_params:
        qs = "&".join(f"{k}={v}" for k, v in all_params.items())
        full_path = f"{path}?{qs}"

    # Service call data — these become template variables in the rest_command
    service_data = {
        "path": full_path.lstrip("/"),
        "api_key": connection.key,
    }
    # Only include payload for methods that use it
    if method_lower in ("post", "put"):
        service_data["payload"] = json.dumps(json_body) if json_body else "{}"

    headers = {
        "Authorization": f"Bearer {connection.ha_token}",
        "Content-Type": "application/json",
    }

    try:
        print(f"[MGMT_CLIENT] Nabu Casa proxy: {method} {path} via {base_url}")
        print(f"[MGMT_CLIENT]   -> POST {service_url} (service: {service_name})")
        print(f"[MGMT_CLIENT]   -> service_data: {json.dumps(service_data)[:200]}")
        response = await client.request(
            method="POST",
            url=service_url,
            headers=headers,
            json=service_data,
        )

        print(f"[MGMT_CLIENT]   <- HA responded: HTTP {response.status_code}")
        print(f"[MGMT_CLIENT]   <- Body: {response.text[:500]}")

        if response.status_code == 401:
            return 401, {
                "error": "HA token rejected",
                "detail": "The Home Assistant Long-Lived Access Token was rejected. The homeowner may need to generate a new token.",
            }

        if response.status_code == 404:
            return 404, {
                "error": "rest_command not found",
                "detail": (
                    f"The rest_command.{service_name} service is not configured on the homeowner's HA. "
                    "The homeowner needs to rebuild the Flux Open Home Irrigation Control add-on and then restart HA."
                ),
            }

        if response.status_code == 400:
            return 400, {
                "error": "HA rejected the service call (HTTP 400)",
                "detail": (
                    f"Home Assistant returned 400 Bad Request for rest_command.{service_name}. "
                    "This usually means the service is not registered. "
                    "The homeowner needs to: (1) Ensure configuration.yaml has "
                    "'homeassistant: packages: !include_dir_named packages', "
                    "(2) Rebuild the Flux Open Home Irrigation Control add-on (to regenerate the packages file), "
                    "(3) Fully restart Home Assistant (not just reload)."
                ),
            }

        if response.status_code != 200:
            try:
                err_data = response.json()
            except Exception:
                err_data = {"raw": response.text[:200]}
            return response.status_code, {
                "error": f"HA API error (HTTP {response.status_code})",
                "detail": _error_to_string(err_data),
            }

        # Parse the HA service response
        try:
            ha_response = response.json()
        except Exception:
            return 502, {
                "error": "Invalid response from HA",
                "detail": f"Could not parse HA response: {response.text[:200]}",
            }

        # Extract the rest_command's response from service_response
        service_response = ha_response.get("service_response", {})
        print(f"[MGMT_CLIENT]   <- service_response keys: {list(service_response.keys()) if isinstance(service_response, dict) else type(service_response)}")

        # rest_command returns: {"status": int, "content": str/dict, "headers": dict}
        # The service_response may be nested under rest_command.{service_name}
        if "rest_command" in service_response:
            service_response = service_response.get("rest_command", {}).get(service_name, service_response)
            print(f"[MGMT_CLIENT]   <- unwrapped service_response keys: {list(service_response.keys()) if isinstance(service_response, dict) else type(service_response)}")

        inner_status = service_response.get("status", 502)
        inner_content = service_response.get("content", {})

        print(f"[MGMT_CLIENT]   <- inner_status={inner_status}, inner_content type={type(inner_content).__name__}, preview={str(inner_content)[:200]}")

        # content may be a string (JSON) or already parsed dict
        if isinstance(inner_content, str):
            try:
                inner_content = json.loads(inner_content)
            except (json.JSONDecodeError, ValueError):
                inner_content = {"raw": inner_content[:200]}

        return inner_status, inner_content

    except httpx.ConnectError as e:
        print(f"[MGMT_CLIENT] ConnectError to Nabu Casa {base_url}: {e}")
        return 503, {
            "error": "Cannot reach homeowner's Home Assistant",
            "detail": f"Connection failed to {base_url}. Check that the Nabu Casa URL is correct and the homeowner's HA is online.",
        }
    except httpx.TimeoutException:
        print(f"[MGMT_CLIENT] Timeout connecting to Nabu Casa {base_url}")
        return 504, {
            "error": "Homeowner system timeout",
            "detail": f"Request timed out connecting to {base_url}. The homeowner's HA may be offline or slow.",
        }
    except Exception as e:
        print(f"[MGMT_CLIENT] Error with Nabu Casa proxy {base_url}: {type(e).__name__}: {e}")
        detail = str(e)
        # Give a clearer message for the most common issue
        if "UnsupportedProtocol" in type(e).__name__ or "missing" in detail.lower() and "protocol" in detail.lower():
            detail = (
                f"The customer URL '{base_url}' is not a valid URL. "
                f"It must start with https:// (e.g., https://xxxxxxxx.ui.nabu.casa). "
                f"Delete this customer and re-add with a corrected connection key."
            )
        return 502, {
            "error": "Communication error",
            "detail": detail,
        }


def _error_to_string(err) -> str:
    """Convert an error value (str, dict, or other) to a readable string."""
    if isinstance(err, str):
        return err
    if isinstance(err, dict):
        return err.get("detail") or err.get("error") or err.get("message") or str(err)
    return str(err)


def _diagnose_error(status: int, response_data: dict, url: str) -> str:
    """Analyze a failed response and produce a helpful diagnostic message."""
    raw = response_data.get("raw", "")

    # Detect plain-text 404 — hallmark of hitting HA's web server on port 8123
    if status == 404 and ("Not Found" in raw or "404" in raw) and "detail" not in response_data:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        port = parsed.port
        if port is None or port in (80, 443, 8123):
            return (
                f"Got a plain 404 from {parsed.hostname} — this looks like Home Assistant's "
                f"web server, not the Flux Open Home Irrigation Control API. The connection key URL must "
                f"include port 8099 (e.g., http://{parsed.hostname}:8099). "
                f"Port 8099 must also be forwarded on the homeowner's router."
            )
        return (
            f"Got a plain 404 from {url}. The server responded but doesn't have the "
            f"Flux Open Home Irrigation Control API. Check that the add-on is running on the homeowner's HA instance."
        )

    # Detect JSON 404 from our own API (mode guard or wrong path)
    if status == 404 and "detail" in response_data:
        return response_data["detail"]

    return _error_to_string(response_data)


async def check_homeowner_connection(connection: ConnectionKeyData) -> dict:
    """
    Test connectivity to a homeowner's system.
    Phase 1: /api/system/health (no auth) — reachability + explicit revoked flag.
    Phase 2: /api/system/status (with auth) — full system status.
    """
    print(f"[MGMT_CLIENT] Testing connection to {connection.url} (mode={connection.mode})")

    if connection.mode == "nabu_casa":
        # Nabu Casa: call health first (via proxy) to check explicit revoked flag
        health_status, health_data = await proxy_request(
            connection, "GET", "/api/system/health"
        )
        if health_status == 200 and isinstance(health_data, dict) and health_data.get("revoked"):
            print(f"[MGMT_CLIENT] Homeowner explicitly revoked access (Nabu Casa)")
            return {
                "reachable": True,
                "authenticated": False,
                "revoked": True,
                "error": "Management access was revoked by homeowner",
            }

        # Now try the authenticated status call for full data
        status, system_status = await proxy_request(
            connection, "GET", "/api/system/status"
        )
        if status == 401:
            error_str = _error_to_string(system_status)
            if "HA token rejected" in error_str:
                return {
                    "reachable": False,
                    "authenticated": False,
                    "error": "HA token rejected. The homeowner may need to generate a new Long-Lived Access Token.",
                }
            # Health endpoint already told us revoked=false, so this 401 means
            # the API key is stale — not that access was revoked.
            return {
                "reachable": True,
                "authenticated": False,
                "error": "API key rejected. The homeowner may have generated a new connection key — ask them for the updated key.",
            }
        if status == 404:
            return {
                "reachable": False,
                "authenticated": False,
                "error": _error_to_string(system_status),
            }
        if status != 200:
            error_msg = _error_to_string(system_status)
            return {
                "reachable": False,
                "authenticated": False,
                "error": error_msg,
            }
        return {
            "reachable": True,
            "authenticated": True,
            "system_status": system_status,
        }

    # Direct mode — two-phase check
    # Phase 1: health check (no auth) — also carries the explicit revoked flag
    status, health = await proxy_request(connection, "GET", "/api/system/health")
    if status != 200:
        error_msg = _diagnose_error(status, health, connection.url)
        print(f"[MGMT_CLIENT] Health check failed: status={status}, error={error_msg}")
        return {"reachable": False, "authenticated": False, "error": error_msg}

    # Verify the health response looks like our API
    if not isinstance(health, dict) or "status" not in health:
        return {
            "reachable": False,
            "authenticated": False,
            "error": (
                f"The server at {connection.url} responded, but it doesn't appear to be "
                f"a Flux Open Home Irrigation Control API. Make sure the URL points to port 8099."
            ),
        }

    # Check the explicit revoked flag from health response
    if health.get("revoked"):
        print(f"[MGMT_CLIENT] Homeowner explicitly revoked access (direct mode)")
        return {
            "reachable": True,
            "authenticated": False,
            "revoked": True,
            "error": "Management access was revoked by homeowner",
        }

    # Phase 2: authenticated status check
    status, system_status = await proxy_request(
        connection, "GET", "/api/system/status"
    )
    if status == 401:
        # Health endpoint already told us revoked=false, so this 401 means
        # the API key is stale (homeowner generated a new connection key).
        # Do NOT set revoked=true — the homeowner hasn't revoked access,
        # the management company just needs the updated connection key.
        return {
            "reachable": True,
            "authenticated": False,
            "error": "API key rejected. The homeowner may have generated a new connection key — ask them for the updated key.",
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
