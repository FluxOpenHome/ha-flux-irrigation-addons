"""Cloud -> HA bridge (Approach A, phase 3): MQTT Discovery.

Mirrors the homeowner's CLOUD LoRa devices (gateways, extenders, Gophr probes)
and their entities into Home Assistant as NATIVE, controllable entities by
publishing HA MQTT Discovery messages to the user's MQTT broker.

This module has two halves:
  * Pure builders (``device_info``, ``discovery_for_entity``,
    ``build_discovery``) that turn the management server's device + entity
    JSON into (config_topic, config_payload, state_topic, command_topic)
    tuples. These are deterministic and unit-tested.
  * A thin runtime (``get_mqtt_broker``) that reads the HA MQTT add-on
    credentials from the supervisor so the publisher can connect.

Phase 4 wires command_topic subscriptions back to MgmtClient.set_entity.
"""
from __future__ import annotations

import re
from typing import Any, Optional

DISCOVERY_PREFIX = "homeassistant"
# All bridged entities live under this MQTT base so they're easy to find/purge.
BASE = "flux_lora"

# entity_id domain (the part before the dot) -> HA MQTT Discovery component.
_DOMAIN_TO_COMPONENT = {
    "sensor": "sensor",
    "binary_sensor": "binary_sensor",
    "switch": "switch",
    "number": "number",
    "select": "select",
    "light": "light",
    "text": "text",
}

# Sensors that should carry a device_class / unit for nicer HA display.
_SENSOR_HINTS = {
    "rssi": ("signal_strength", "dBm"),
    "snr": (None, "dB"),
    "battery": ("battery", "%"),
    "soc": ("battery", "%"),
    "moisture": ("moisture", "%"),
    "percentage": ("moisture", "%"),
    "temperature": ("temperature", "°C"),
    "voltage": ("voltage", "V"),
    "current": ("current", "A"),
    "power": ("power", "W"),
}


def _slug(value: str) -> str:
    """MQTT-topic-safe slug."""
    return re.sub(r"[^a-z0-9_]+", "_", (value or "").lower()).strip("_") or "x"


def device_info(device: dict) -> dict:
    """HA device-registry block so all of a device's entities group together."""
    dev_id = str(device.get("id", ""))
    name = device.get("display_name") or device.get("mac_address") or "LoRa Device"
    model = {
        "lora_gateway": "Flux LoRa Gateway",
        "lora_extender": "Flux LoRa Extender",
        "lora_probe": "Gophr LoRa Probe",
    }.get(device.get("device_category", ""), "Flux LoRa Device")
    info: dict[str, Any] = {
        "identifiers": [f"{BASE}_{_slug(dev_id)}"],
        "name": name,
        "manufacturer": "Flux Open Home",
        "model": model,
    }
    if device.get("mac_address"):
        info["connections"] = [["mac", device["mac_address"]]]
    if device.get("firmware_version"):
        info["sw_version"] = device["firmware_version"]
    return info


def _sensor_hint(entity_id: str) -> tuple[Optional[str], Optional[str]]:
    low = entity_id.lower()
    for key, (dclass, unit) in _SENSOR_HINTS.items():
        if key in low:
            return dclass, unit
    return None, None


def discovery_for_entity(device: dict, entity: dict) -> Optional[dict]:
    """Build a single HA MQTT Discovery config for one entity.

    Returns a dict with config_topic, config_payload, state_topic, and
    (for controllable domains) command_topic — or None for unsupported domains.
    """
    entity_id = entity.get("entity_id", "")
    if "." not in entity_id:
        return None
    domain = entity_id.split(".", 1)[0]
    component = _DOMAIN_TO_COMPONENT.get(domain)
    if component is None:
        return None

    obj_id = f"{BASE}_{_slug(entity_id)}"
    node_id = _slug(str(device.get("id", "dev")))
    state_topic = f"{BASE}/{node_id}/{_slug(entity_id)}/state"

    payload: dict[str, Any] = {
        "name": entity.get("friendly_name") or entity.get("attributes", {}).get("friendly_name") or entity_id,
        "unique_id": obj_id,
        "object_id": obj_id,
        "state_topic": state_topic,
        "device": device_info(device),
        "availability_topic": f"{BASE}/{node_id}/availability",
    }

    result: dict[str, Any] = {
        "config_topic": f"{DISCOVERY_PREFIX}/{component}/{obj_id}/config",
        "state_topic": state_topic,
    }

    if component == "sensor":
        dclass, unit = _sensor_hint(entity_id)
        if dclass:
            payload["device_class"] = dclass
        if unit:
            payload["unit_of_measurement"] = unit
    elif component == "binary_sensor":
        payload["payload_on"] = "on"
        payload["payload_off"] = "off"
    elif component in ("switch", "number", "select", "light", "text"):
        # Controllable: HA -> command_topic -> (phase 4) server -> device.
        command_topic = f"{BASE}/{node_id}/{_slug(entity_id)}/set"
        payload["command_topic"] = command_topic
        result["command_topic"] = command_topic
        if component == "switch":
            payload["payload_on"] = "on"
            payload["payload_off"] = "off"

    result["config_payload"] = payload
    return result


def build_discovery(devices: list[dict], entities: list[dict]) -> list[dict]:
    """Build discovery configs for every entity, grouped to its device.

    ``entities`` items carry ``device_id``; we match them to ``devices`` by id.
    Entities whose device isn't a known LoRa device are skipped.
    """
    by_id = {str(d.get("id", "")): d for d in devices}
    out: list[dict] = []
    for ent in entities:
        dev = by_id.get(str(ent.get("device_id", "")))
        if dev is None:
            continue
        cfg = discovery_for_entity(dev, ent)
        if cfg is not None:
            cfg["entity"] = ent
            out.append(cfg)
    return out


async def get_mqtt_broker(supervisor_token: Optional[str]) -> Optional[dict]:
    """Read the HA MQTT add-on connection info from the supervisor services API.

    Returns {host, port, username, password, ssl} or None if MQTT isn't set up.
    """
    if not supervisor_token:
        return None
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "http://supervisor/services/mqtt",
                headers={"Authorization": f"Bearer {supervisor_token}"},
            )
            if resp.status_code != 200:
                return None
            data = resp.json().get("data", {})
            if not data.get("host"):
                return None
            return {
                "host": data.get("host"),
                "port": int(data.get("port", 1883)),
                "username": data.get("username", ""),
                "password": data.get("password", ""),
                "ssl": bool(data.get("ssl", False)),
            }
    except Exception:
        return None
