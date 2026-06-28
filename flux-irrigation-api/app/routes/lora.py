"""Cloud LoRa proxy — serves the user-portal LoRa data inside the add-on.

The LoRa gateways / extenders / Gophr probes report to the cloud management
server (the "server firmware"), NOT to local Home Assistant — so the add-on
can't read them via ha_client like local ESPHome devices. These endpoints
proxy the exact same data the user portal shows, via an authenticated
MgmtClient, so the add-on's homeowner UI can render LoRa identically to the
portal (network map, gateways, extenders, Gophr probes, link quality).

Enabled by the add-on options: mgmt_bridge_enabled + mgmt_account_email/password.
"""
from fastapi import APIRouter, HTTPException

from config import get_config
import mgmt_client as _mc

router = APIRouter(tags=["LoRa (cloud)"])

_client: "_mc.MgmtClient | None" = None


def _get_client() -> "_mc.MgmtClient":
    """Lazily build the shared authenticated client from add-on options."""
    global _client
    cfg = get_config()
    if not getattr(cfg, "mgmt_bridge_enabled", False):
        raise HTTPException(
            status_code=503,
            detail="LoRa cloud bridge disabled — enable mgmt_bridge_enabled and set the account in the add-on options.",
        )
    if not cfg.mgmt_account_email or not cfg.mgmt_account_password:
        raise HTTPException(status_code=400, detail="Flux account email/password not configured.")
    if _client is None:
        _client = _mc.MgmtClient(
            cfg.mgmt_server_url,
            cfg.mgmt_account_email,
            cfg.mgmt_account_password,
        )
    return _client


async def _safe(coro):
    try:
        return await coro
    except _mc.MgmtAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:  # network / server error
        raise HTTPException(status_code=502, detail=f"Cloud request failed: {exc}")


@router.get("/lora/status")
async def lora_status():
    """Whether the cloud bridge is configured + reachable (for the UI)."""
    cfg = get_config()
    enabled = bool(getattr(cfg, "mgmt_bridge_enabled", False))
    configured = bool(cfg.mgmt_account_email and cfg.mgmt_account_password)
    if not enabled or not configured:
        return {"enabled": enabled, "configured": configured, "connected": False}
    try:
        await _get_client().login()
        return {"enabled": True, "configured": True, "connected": True}
    except Exception as exc:
        return {"enabled": True, "configured": True, "connected": False, "error": str(exc)}


@router.get("/lora/devices")
async def lora_devices():
    """LoRa gateways, extenders, and Gophr probes for the account."""
    return {"devices": await _safe(_get_client().get_lora_devices())}


@router.get("/lora/network")
async def lora_network():
    """Gateway/extender link stats — same as the portal LoRa Network card."""
    return await _safe(_get_client().get_lora_network())


@router.get("/lora/topology")
async def lora_topology():
    """Network-map graph (nodes + edges) — same as the portal map modal."""
    return await _safe(_get_client().get_lora_topology())


@router.get("/lora/probes")
async def lora_probes():
    """Moisture probes (incl. LoRa Gophr) with readings + telemetry."""
    return await _safe(_get_client().get_moisture_probes())
