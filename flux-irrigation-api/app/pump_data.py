"""
Flux Open Home - Pump Settings & Statistics
=============================================
Persists pump configuration (HP/kW, voltage, brand, electricity rates)
and calculates usage statistics (cycles, run hours, kWh, cost) from
the zone run history for the pump start relay zone.
"""

import json
import os
from typing import Optional

import run_log

PUMP_SETTINGS_FILE = "/data/pump_settings.json"

HP_TO_KW = 0.7457  # 1 HP = 0.7457 kW

DEFAULT_SETTINGS = {
    "pump_entity_id": "",
    "pump_type": "",
    "voltage": 240,
    "hp": 0.0,
    "kw": 0.0,
    "brand": "",
    "model": "",
    "year_installed": "",
    "cost_per_kwh": 0.12,
    "peak_rate_per_kwh": 0.0,
    "pressure_psi": 0.0,
    "max_gpm": 0.0,
    "max_head_ft": 0.0,
}


def _load_settings() -> dict:
    """Load pump settings from persistent storage."""
    if os.path.exists(PUMP_SETTINGS_FILE):
        try:
            with open(PUMP_SETTINGS_FILE, "r") as f:
                data = json.load(f)
                # Merge with defaults for forward-compat
                merged = dict(DEFAULT_SETTINGS)
                merged.update(data)
                return merged
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_SETTINGS)


def _save_settings(data: dict):
    """Save pump settings to persistent storage."""
    os.makedirs(os.path.dirname(PUMP_SETTINGS_FILE), exist_ok=True)
    with open(PUMP_SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_pump_settings() -> dict:
    """Get the current pump settings."""
    return _load_settings()


def save_pump_settings(settings: dict) -> dict:
    """Save pump settings with HP/kW auto-sync.

    If hp is provided and > 0, kw is recalculated.
    If kw is provided and > 0 but hp is 0, hp is recalculated from kw.
    Both are stored so the UI can display either.
    """
    current = _load_settings()
    current.update(settings)

    # Auto-sync HP ↔ kW
    hp = float(current.get("hp", 0) or 0)
    kw = float(current.get("kw", 0) or 0)

    if hp > 0:
        current["kw"] = round(hp * HP_TO_KW, 4)
    elif kw > 0:
        current["hp"] = round(kw / HP_TO_KW, 4)

    # Ensure numeric types
    for key in ("voltage", "hp", "kw", "cost_per_kwh", "peak_rate_per_kwh", "pressure_psi", "max_gpm", "max_head_ft"):
        try:
            current[key] = float(current.get(key, 0) or 0)
        except (ValueError, TypeError):
            current[key] = 0.0

    _save_settings(current)
    return current


def get_pump_stats(hours: int, pump_entity_id: str, settings: Optional[dict] = None) -> dict:
    """Calculate pump usage statistics from run history.

    Args:
        hours: Time window in hours
        pump_entity_id: The switch entity_id of the pump zone
        settings: Pump settings dict (loaded if not provided)

    Returns:
        dict with cycles, run_hours, total_kwh, estimated_cost
    """
    if settings is None:
        settings = _load_settings()

    # Get run history filtered to the pump entity
    events = run_log.get_run_history(hours=hours, zone_id=None)

    # Filter to pump entity — OFF events have duration_seconds
    pump_events = [
        e for e in events
        if e.get("entity_id") == pump_entity_id
    ]

    # Count cycles (OFF events = completed cycles)
    off_events = [
        e for e in pump_events
        if e.get("state") in ("off", "closed")
        and e.get("duration_seconds")
        and e["duration_seconds"] > 0
    ]

    cycles = len(off_events)
    total_seconds = sum(e.get("duration_seconds", 0) for e in off_events)
    run_hours = total_seconds / 3600.0

    # Calculate power usage
    hp = float(settings.get("hp", 0) or 0)
    kw = float(settings.get("kw", 0) or 0)

    if kw > 0:
        power_kw = kw
    elif hp > 0:
        power_kw = hp * HP_TO_KW
    else:
        power_kw = 0.0

    total_kwh = power_kw * run_hours

    # Calculate cost
    cost_per_kwh = float(settings.get("cost_per_kwh", 0) or 0)
    peak_rate = float(settings.get("peak_rate_per_kwh", 0) or 0)

    # Simple cost model: base rate for all usage
    # Peak rate shown in settings for user reference
    estimated_cost = total_kwh * cost_per_kwh

    return {
        "pump_entity_id": pump_entity_id,
        "cycles": cycles,
        "run_hours": round(run_hours, 2),
        "total_seconds": round(total_seconds, 1),
        "total_kwh": round(total_kwh, 3),
        "estimated_cost": round(estimated_cost, 2),
        "power_kw": round(power_kw, 4),
        "cost_per_kwh": cost_per_kwh,
        "peak_rate_per_kwh": peak_rate,
        "hours": hours,
    }
