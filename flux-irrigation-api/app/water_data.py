"""
Flux Open Home - Water Source Settings
=======================================
Persists water source configuration (city/reclaimed/well) and cost per
1,000 gallons for the Estimated Gallons card.

Persists data in /data/water_settings.json.
"""

import json
import os

WATER_SETTINGS_FILE = "/data/water_settings.json"

VALID_SOURCES = ("city", "reclaimed", "well", "")

DEFAULT_SETTINGS = {
    "water_source": "",           # "city", "reclaimed", "well", or "" (not configured)
    "cost_per_1000_gal": 0.0,     # $/1,000 gallons (for city/reclaimed)
    "pressure_psi": 50.0,         # Water pressure in PSI (default 50, used when no pump)
}


def _load_settings() -> dict:
    """Load water settings from persistent storage."""
    if os.path.exists(WATER_SETTINGS_FILE):
        try:
            with open(WATER_SETTINGS_FILE, "r") as f:
                data = json.load(f)
                # Merge with defaults for forward-compat
                merged = dict(DEFAULT_SETTINGS)
                merged.update(data)
                return merged
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_SETTINGS)


def _save_settings(data: dict):
    """Save water settings to persistent storage."""
    os.makedirs(os.path.dirname(WATER_SETTINGS_FILE), exist_ok=True)
    with open(WATER_SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_water_settings() -> dict:
    """Get the current water source settings."""
    return _load_settings()


def save_water_settings(settings: dict) -> dict:
    """Save water source settings with validation.

    - water_source must be one of: "city", "reclaimed", "well", ""
    - If water_source is "well", cost_per_1000_gal is set to 0
      (well water has no utility cost; pump electricity is tracked separately)
    - cost_per_1000_gal must be >= 0
    """
    current = _load_settings()
    current.update(settings)

    # Validate water_source
    ws = str(current.get("water_source", "") or "").lower().strip()
    if ws not in VALID_SOURCES:
        ws = ""
    current["water_source"] = ws

    # Ensure numeric cost
    try:
        cost = float(current.get("cost_per_1000_gal", 0) or 0)
    except (ValueError, TypeError):
        cost = 0.0
    current["cost_per_1000_gal"] = max(0.0, cost)

    # Well water has no utility cost
    if current["water_source"] == "well":
        current["cost_per_1000_gal"] = 0.0

    # Ensure numeric pressure
    try:
        pressure = float(current.get("pressure_psi", 50.0) or 50.0)
    except (ValueError, TypeError):
        pressure = 50.0
    current["pressure_psi"] = max(0.0, pressure)

    _save_settings(current)
    return current


def has_saved_settings() -> bool:
    """Check if water settings have been configured (non-empty water_source)."""
    settings = _load_settings()
    return bool(settings.get("water_source"))
