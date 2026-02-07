"""
Configuration management for the Flux Irrigation Management API.
Loads settings from the HA add-on options.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ApiKeyConfig:
    key: str
    name: str
    permissions: list[str] = field(default_factory=list)


@dataclass
class Config:
    mode: str = "homeowner"
    homeowner_url: str = ""
    homeowner_label: str = ""
    homeowner_address: str = ""
    homeowner_city: str = ""
    homeowner_state: str = ""
    homeowner_zip: str = ""
    api_keys: list[ApiKeyConfig] = field(default_factory=list)
    irrigation_device_id: str = ""
    allowed_zone_entities: list[str] = field(default_factory=list)
    allowed_sensor_entities: list[str] = field(default_factory=list)
    allowed_control_entities: list[str] = field(default_factory=list)
    rate_limit_per_minute: int = 60
    log_retention_days: int = 30
    enable_audit_log: bool = True
    supervisor_token: Optional[str] = None

    @classmethod
    def load(cls, prefer_file: bool = False) -> "Config":
        """Load configuration from add-on options or environment.

        Args:
            prefer_file: If True, always read from /data/options.json instead of
                the ADDON_OPTIONS env var. Used by reload_config() to pick up
                changes saved at runtime (e.g., mode switch, device selection).
        """
        config = cls()

        # Load supervisor token
        config.supervisor_token = os.environ.get("SUPERVISOR_TOKEN")
        if config.supervisor_token:
            print(f"[CONFIG] SUPERVISOR_TOKEN loaded ({len(config.supervisor_token)} chars)")
        else:
            print("[CONFIG] WARNING: SUPERVISOR_TOKEN is empty/missing - HA API calls will fail")

        # Load add-on options — always prefer the file for runtime reloads
        # because the ADDON_OPTIONS env var is set at startup and becomes stale
        options = {}
        options_path = "/data/options.json"

        if prefer_file and os.path.exists(options_path):
            with open(options_path, "r") as f:
                options = json.load(f)
        else:
            options_str = os.environ.get("ADDON_OPTIONS")
            if options_str:
                try:
                    options = json.loads(options_str)
                except json.JSONDecodeError:
                    options = {}
            elif os.path.exists(options_path):
                with open(options_path, "r") as f:
                    options = json.load(f)

        # Parse API keys
        for key_entry in options.get("api_keys", []):
            config.api_keys.append(
                ApiKeyConfig(
                    key=key_entry.get("key", ""),
                    name=key_entry.get("name", "Unknown"),
                    permissions=key_entry.get("permissions", []),
                )
            )

        config.mode = options.get("mode", config.mode)
        config.homeowner_url = options.get("homeowner_url", config.homeowner_url)
        config.homeowner_label = options.get("homeowner_label", config.homeowner_label)
        config.homeowner_address = options.get("homeowner_address", config.homeowner_address)
        config.homeowner_city = options.get("homeowner_city", config.homeowner_city)
        config.homeowner_state = options.get("homeowner_state", config.homeowner_state)
        config.homeowner_zip = options.get("homeowner_zip", config.homeowner_zip)
        config.irrigation_device_id = options.get(
            "irrigation_device_id", config.irrigation_device_id
        )
        config.rate_limit_per_minute = options.get(
            "rate_limit_per_minute", config.rate_limit_per_minute
        )
        config.log_retention_days = options.get(
            "log_retention_days", config.log_retention_days
        )
        config.enable_audit_log = options.get(
            "enable_audit_log", config.enable_audit_log
        )

        return config

    async def resolve_device_entities(self):
        """Resolve the allowed entity lists from the selected device."""
        if not self.irrigation_device_id:
            self.allowed_zone_entities = []
            self.allowed_sensor_entities = []
            self.allowed_control_entities = []
            return

        import ha_client

        try:
            result = await ha_client.get_device_entities(self.irrigation_device_id)
            self.allowed_zone_entities = [
                e["entity_id"] for e in result.get("zones", [])
            ]
            self.allowed_sensor_entities = [
                e["entity_id"] for e in result.get("sensors", [])
            ]
            self.allowed_control_entities = [
                e["entity_id"] for e in result.get("other", [])
            ]
        except Exception as e:
            print(f"[CONFIG] Failed to resolve device entities: {e}")
            self.allowed_zone_entities = []
            self.allowed_sensor_entities = []
            self.allowed_control_entities = []


# Global config instance
_config: Optional[Config] = None


async def async_initialize() -> Config:
    """Load config and resolve device entities. Call once at startup.

    Device entities are always resolved when a device ID is set, regardless
    of mode. The homeowner API endpoints (/api/zones, /api/sensors, etc.)
    are always active and may be called via the Nabu Casa proxy even when
    the UI is in management mode.
    """
    global _config
    _config = Config.load()
    await _config.resolve_device_entities()
    return _config


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config.load()
    return _config


async def reload_config() -> Config:
    """Reload config from disk and re-resolve device entities.

    Uses prefer_file=True so runtime changes (mode switch, device selection)
    are picked up from /data/options.json rather than the stale env var.
    Device entities are always resolved when a device ID is set, regardless
    of mode.
    """
    global _config
    _config = Config.load(prefer_file=True)
    await _config.resolve_device_entities()
    print(f"[CONFIG] Reloaded: mode={_config.mode}, device={_config.irrigation_device_id or '(none)'}, "
          f"zones={len(_config.allowed_zone_entities)}, sensors={len(_config.allowed_sensor_entities)}, "
          f"controls={len(_config.allowed_control_entities)}")
    return _config
