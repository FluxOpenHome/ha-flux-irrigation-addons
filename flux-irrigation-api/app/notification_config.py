"""
Flux Open Home - HA Notification Configuration
================================================
Manages notification settings for the management mode.
When enabled, sends HA notifications (via notify service) when
new customer issues are detected during health check polling.

Persists settings in /data/notification_config.json.
"""

import json
import os

NOTIFICATION_CONFIG_FILE = "/data/notification_config.json"

DEFAULT_CONFIG = {
    "enabled": False,
    "ha_notify_service": "",       # e.g. "mobile_app_brandons_iphone"
    "notify_severe": True,
    "notify_annoyance": True,
    "notify_clarification": False,
    "last_known_issues": {},       # customer_id → {"ids": [...]}
    "last_known_dismissed": {},    # customer_id → {"ids": [...]}
}


def load_config() -> dict:
    """Load notification config from persistent storage."""
    if os.path.exists(NOTIFICATION_CONFIG_FILE):
        try:
            with open(NOTIFICATION_CONFIG_FILE, "r") as f:
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
    """Save notification config to persistent storage."""
    os.makedirs(os.path.dirname(NOTIFICATION_CONFIG_FILE), exist_ok=True)
    with open(NOTIFICATION_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_settings() -> dict:
    """Return user-facing settings (excludes internal state like last_known_issues)."""
    config = load_config()
    return {
        "enabled": config["enabled"],
        "ha_notify_service": config["ha_notify_service"],
        "notify_severe": config["notify_severe"],
        "notify_annoyance": config["notify_annoyance"],
        "notify_clarification": config["notify_clarification"],
    }


def update_settings(
    enabled: bool | None = None,
    ha_notify_service: str | None = None,
    notify_severe: bool | None = None,
    notify_annoyance: bool | None = None,
    notify_clarification: bool | None = None,
) -> dict:
    """Update notification settings. Returns the updated settings."""
    config = load_config()
    if enabled is not None:
        config["enabled"] = enabled
    if ha_notify_service is not None:
        config["ha_notify_service"] = ha_notify_service.strip()
    if notify_severe is not None:
        config["notify_severe"] = notify_severe
    if notify_annoyance is not None:
        config["notify_annoyance"] = notify_annoyance
    if notify_clarification is not None:
        config["notify_clarification"] = notify_clarification
    save_config(config)
    return get_settings()


def get_last_known_issues() -> dict:
    """Get the last known issue IDs per customer."""
    config = load_config()
    return config.get("last_known_issues", {})


def update_last_known_issues(last_known: dict):
    """Update the last known issue IDs per customer."""
    config = load_config()
    config["last_known_issues"] = last_known
    save_config(config)


def should_notify(severity: str) -> bool:
    """Check if a given severity should trigger a notification."""
    config = load_config()
    if not config["enabled"]:
        return False
    if not config["ha_notify_service"]:
        return False
    severity_map = {
        "severe": config["notify_severe"],
        "annoyance": config["notify_annoyance"],
        "clarification": config["notify_clarification"],
    }
    return severity_map.get(severity, False)
