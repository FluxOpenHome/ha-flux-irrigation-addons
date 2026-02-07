"""
System state persistence helpers.
Stores pause/resume and rain delay state in a local JSON file.

NOTE: Schedule programs are no longer managed here. The actual irrigation
schedule is controlled directly through ESPHome device entities (day switches,
start times, run durations) via the /api/entities endpoint.
"""

import json
import os

# Local state storage (persisted in add-on data)
SCHEDULE_FILE = "/data/schedules.json"


def _load_schedules() -> dict:
    """Load system state from persistent storage."""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"system_paused": False, "rain_delay_until": None}


def _save_schedules(data: dict):
    """Save system state to persistent storage."""
    os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=2)
