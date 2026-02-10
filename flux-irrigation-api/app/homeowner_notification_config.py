"""
Flux Open Home - Homeowner HA Notification Configuration
=========================================================
Manages HA push notification settings for the homeowner mode.
When enabled, sends HA notifications (via notify service) when
management makes changes to the homeowner's system.

Persists settings in /data/homeowner_ha_notification_config.json.
"""

import json
import os

HOMEOWNER_HA_NOTIF_FILE = "/data/homeowner_ha_notification_config.json"

DEFAULT_CONFIG = {
    "enabled": False,
    "ha_notify_service": "",           # e.g. "mobile_app_brandons_iphone"
    "notify_service_appointments": True,
    "notify_system_changes": True,
    "notify_weather_changes": True,
    "notify_moisture_changes": True,
    "notify_equipment_changes": True,
    "notify_duration_changes": True,
    "notify_report_changes": True,
}

# Maps event_type (from record_event) → config key
_EVENT_TYPE_TO_CONFIG_KEY = {
    "service_appointments": "notify_service_appointments",
    "system_changes": "notify_system_changes",
    "weather_changes": "notify_weather_changes",
    "moisture_changes": "notify_moisture_changes",
    "equipment_changes": "notify_equipment_changes",
    "duration_changes": "notify_duration_changes",
    "report_changes": "notify_report_changes",
}


def load_config() -> dict:
    """Load homeowner HA notification config from persistent storage."""
    if os.path.exists(HOMEOWNER_HA_NOTIF_FILE):
        try:
            with open(HOMEOWNER_HA_NOTIF_FILE, "r") as f:
                data = json.load(f)
                # Backfill missing keys from defaults
                for key, default in DEFAULT_CONFIG.items():
                    if key not in data:
                        data[key] = default
                return data
        except (json.JSONDecodeError, IOError):
            pass
    return json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy


def save_config(config: dict):
    """Save homeowner HA notification config to persistent storage."""
    os.makedirs(os.path.dirname(HOMEOWNER_HA_NOTIF_FILE), exist_ok=True)
    with open(HOMEOWNER_HA_NOTIF_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_settings() -> dict:
    """Return all user-facing settings."""
    return load_config()


def update_settings(
    enabled: bool | None = None,
    ha_notify_service: str | None = None,
    notify_service_appointments: bool | None = None,
    notify_system_changes: bool | None = None,
    notify_weather_changes: bool | None = None,
    notify_moisture_changes: bool | None = None,
    notify_equipment_changes: bool | None = None,
    notify_duration_changes: bool | None = None,
    notify_report_changes: bool | None = None,
) -> dict:
    """Update homeowner HA notification settings. Returns the updated settings."""
    config = load_config()
    if enabled is not None:
        config["enabled"] = enabled
    if ha_notify_service is not None:
        config["ha_notify_service"] = ha_notify_service.strip()
    if notify_service_appointments is not None:
        config["notify_service_appointments"] = notify_service_appointments
    if notify_system_changes is not None:
        config["notify_system_changes"] = notify_system_changes
    if notify_weather_changes is not None:
        config["notify_weather_changes"] = notify_weather_changes
    if notify_moisture_changes is not None:
        config["notify_moisture_changes"] = notify_moisture_changes
    if notify_equipment_changes is not None:
        config["notify_equipment_changes"] = notify_equipment_changes
    if notify_duration_changes is not None:
        config["notify_duration_changes"] = notify_duration_changes
    if notify_report_changes is not None:
        config["notify_report_changes"] = notify_report_changes
    save_config(config)
    return get_settings()


def should_notify(event_type: str) -> bool:
    """Check if a given event type should trigger an HA notification.

    Maps event_type (e.g. 'system_changes') to the config key
    (e.g. 'notify_system_changes') and checks if enabled.
    """
    config = load_config()
    if not config["enabled"]:
        return False
    if not config["ha_notify_service"]:
        return False
    config_key = _EVENT_TYPE_TO_CONFIG_KEY.get(event_type)
    if not config_key:
        return False
    return config.get(config_key, False)
