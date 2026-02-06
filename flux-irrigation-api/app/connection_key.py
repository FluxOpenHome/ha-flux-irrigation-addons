"""
Flux Open Home - Connection Key Encode/Decode
==============================================
Encodes and decodes connection keys used to link homeowner
irrigation systems with management company dashboards.

A connection key is a base64url-encoded JSON object containing:
  - url: Externally reachable API URL
  - key: API key with full permissions
  - v: Version number (for future-proofing)
  - label: Optional friendly name (e.g., property address)
  - address, city, state, zip: Property location for management filtering
  - zone_count: Number of enabled irrigation zones (auto-detected)
"""

import base64
import json
from dataclasses import dataclass
from typing import Optional

CONNECTION_KEY_VERSION = 1


@dataclass
class ConnectionKeyData:
    url: str
    key: str
    v: int = CONNECTION_KEY_VERSION
    label: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    zone_count: Optional[int] = None


def encode_connection_key(data: ConnectionKeyData) -> str:
    """Encode connection data into a base64url string for sharing."""
    payload = {"url": data.url, "key": data.key, "v": data.v}
    if data.label:
        payload["label"] = data.label
    if data.address:
        payload["address"] = data.address
    if data.city:
        payload["city"] = data.city
    if data.state:
        payload["state"] = data.state
    if data.zip:
        payload["zip"] = data.zip
    if data.zone_count is not None:
        payload["zone_count"] = data.zone_count
    json_str = json.dumps(payload, separators=(",", ":"))
    return base64.urlsafe_b64encode(json_str.encode()).decode()


def decode_connection_key(encoded: str) -> ConnectionKeyData:
    """Decode a base64url connection key string. Raises ValueError on invalid input."""
    try:
        # Strip whitespace that may have been added during copy/paste
        encoded = encoded.strip()
        json_str = base64.urlsafe_b64decode(encoded.encode()).decode()
        payload = json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Invalid connection key: {e}")

    if not isinstance(payload, dict):
        raise ValueError("Connection key must be a JSON object")
    if "url" not in payload or "key" not in payload:
        raise ValueError("Connection key missing required 'url' or 'key' fields")
    if not payload["url"] or not payload["key"]:
        raise ValueError("Connection key 'url' and 'key' must not be empty")

    return ConnectionKeyData(
        url=payload["url"],
        key=payload["key"],
        v=payload.get("v", 1),
        label=payload.get("label"),
        address=payload.get("address"),
        city=payload.get("city"),
        state=payload.get("state"),
        zip=payload.get("zip"),
        zone_count=payload.get("zone_count"),
    )
