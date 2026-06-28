"""Management-server client — cloud → HA bridge (Approach A, phases 1–2).

Logs into the Flux management server with the homeowner's account and fetches
their CLOUD-connected devices (LoRa gateways, extenders, Gophr probes) and
entities. These devices report to the cloud over MQTT (the "server firmware"),
NOT to the local Home Assistant, so the add-on can't see them via the normal
supervisor API.

Phase 3 mirrors these into HA via MQTT Discovery; phase 4 relays control
commands back through the server (HA → /user/api/entities/{id}/set → cloud
MQTT → device). This module owns the authenticated session + fetch helpers.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

DEFAULT_SERVER_URL = "https://app.fluxopenhome.com"
LORA_CATEGORIES = ("lora_gateway", "lora_extender", "lora_probe")


class MgmtAuthError(Exception):
    """Raised when the account credentials are missing or rejected."""


class MgmtClient:
    """Authenticated async client for the Flux management server portal API.

    The portal_session cookie is kept in the httpx client's cookie jar; a 401
    triggers a single automatic re-login.
    """

    def __init__(self, server_url: str, email: str, password: str):
        self._base = (server_url or DEFAULT_SERVER_URL).rstrip("/")
        self._email = email
        self._password = password
        self._client = httpx.AsyncClient(
            base_url=self._base, timeout=30.0, follow_redirects=False
        )
        self._authed = False
        self._lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self._client.aclose()

    # --- auth ---------------------------------------------------------------

    async def login(self) -> str:
        """Authenticate. Returns the customer_id. Cookie persists in the jar."""
        if not self._email or not self._password:
            raise MgmtAuthError("Missing account email/password")
        resp = await self._client.post(
            "/user/auth/login",
            json={"email": self._email, "password": self._password},
        )
        if resp.status_code == 401:
            raise MgmtAuthError("Invalid email or password")
        if resp.status_code == 403:
            raise MgmtAuthError("Account is disabled")
        resp.raise_for_status()
        self._authed = True
        try:
            return str(resp.json().get("customer_id", ""))
        except Exception:
            return ""

    async def _ensure_auth(self) -> None:
        async with self._lock:
            if not self._authed:
                await self.login()

    # --- reads --------------------------------------------------------------

    async def _get(self, path: str) -> Any:
        """GET with one automatic re-login on 401/403."""
        await self._ensure_auth()
        resp = await self._client.get(path)
        if resp.status_code in (401, 403):
            async with self._lock:
                self._authed = False
            await self._ensure_auth()
            resp = await self._client.get(path)
        resp.raise_for_status()
        return resp.json()

    async def get_devices(self) -> list[dict]:
        data = await self._get("/user/api/devices")
        if isinstance(data, dict):
            return data.get("devices", []) or []
        return data or []

    async def get_lora_devices(self) -> list[dict]:
        """Only the cloud LoRa devices: gateways, extenders, Gophr probes."""
        return [
            d for d in await self.get_devices()
            if d.get("device_category") in LORA_CATEGORIES
        ]

    async def get_lora_network(self) -> dict:
        """Gateway/extender link stats (online, packets, avg RSSI)."""
        data = await self._get("/user/api/lora-network")
        return data if isinstance(data, dict) else {}

    async def get_entities(self) -> Any:
        """All controllable/sensor entities for the account's devices."""
        return await self._get("/user/api/entities")

    # --- writes (phase 4: command relay) ------------------------------------

    async def set_entity(self, entity_id: str, value: Any) -> Any:
        """Relay a control command: HA → server → cloud MQTT → device."""
        await self._ensure_auth()
        resp = await self._client.post(
            f"/user/api/entities/{entity_id}/set",
            json={"value": value},
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {"status": "ok"}
