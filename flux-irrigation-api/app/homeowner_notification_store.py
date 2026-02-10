"""
Flux Open Home - Homeowner Notification Store
===============================================
Manages homeowner notification preferences and in-app notification events.
Homeowners choose which management actions to be notified about.

Events are recorded by the management proxy after successful settings changes
on the homeowner instance. The store checks preferences internally — if a
category is disabled, the event is silently dropped.

Persists data in /data/homeowner_notifications.json.
"""

import json
import os
import uuid
from datetime import datetime, timezone


NOTIFICATION_FILE = "/data/homeowner_notifications.json"

MAX_EVENTS = 100  # Prune oldest beyond this

# Valid notification category keys
NOTIFICATION_CATEGORIES = [
    "service_appointments",   # Service date created/updated
    "system_changes",         # System pause/resume
    "weather_changes",        # Weather rule changes
    "moisture_changes",       # Moisture settings changes
    "equipment_changes",      # Pump/water settings changes
    "duration_changes",       # Duration apply/restore
    "report_changes",         # Report settings changes
]

DEFAULT_DATA = {
    "version": 1,
    "preferences": {
        "enabled": True,                 # Master toggle — all management notifications
        "service_appointments": True,
        "system_changes": True,
        "weather_changes": False,
        "moisture_changes": False,
        "equipment_changes": False,
        "duration_changes": False,
        "report_changes": False,
    },
    "events": [],
}


# --- Persistence ---

def _load_data() -> dict:
    """Load notification data from persistent storage."""
    if os.path.exists(NOTIFICATION_FILE):
        try:
            with open(NOTIFICATION_FILE, "r") as f:
                data = json.load(f)
                # Backfill missing keys from defaults
                for key, default in DEFAULT_DATA.items():
                    if key not in data:
                        data[key] = default
                # Backfill missing preference keys
                prefs = data.get("preferences", {})
                if "enabled" not in prefs:
                    prefs["enabled"] = True
                for cat in NOTIFICATION_CATEGORIES:
                    if cat not in prefs:
                        prefs[cat] = DEFAULT_DATA["preferences"].get(cat, False)
                return data
        except (json.JSONDecodeError, IOError):
            pass
    return json.loads(json.dumps(DEFAULT_DATA))  # deep copy


def _save_data(data: dict):
    """Save notification data to persistent storage."""
    os.makedirs(os.path.dirname(NOTIFICATION_FILE), exist_ok=True)
    with open(NOTIFICATION_FILE, "w") as f:
        json.dump(data, f, indent=2)


# --- Preferences ---

def get_preferences() -> dict:
    """Return the notification preferences dict."""
    data = _load_data()
    return dict(data.get("preferences", DEFAULT_DATA["preferences"]))


def update_preferences(prefs: dict) -> dict:
    """Merge a partial preferences update. Returns the updated preferences."""
    data = _load_data()
    for key, value in prefs.items():
        if isinstance(value, bool) and (key in NOTIFICATION_CATEGORIES or key == "enabled"):
            data["preferences"][key] = value
    _save_data(data)
    return dict(data["preferences"])


# --- Events ---

def get_events(limit: int = 50) -> list:
    """Return events newest-first, up to limit."""
    data = _load_data()
    events = data.get("events", [])
    return events[:limit]


def get_unread_count() -> int:
    """Return count of events where read is False."""
    data = _load_data()
    return sum(1 for ev in data.get("events", []) if not ev.get("read", False))


def record_event(event_type: str, title: str, message: str = "") -> dict | None:
    """Record a notification event if the preference for event_type is enabled.

    Returns the created event dict, or None if the preference is disabled
    or the event_type is invalid.
    Prunes the events list to MAX_EVENTS.
    """
    if event_type not in NOTIFICATION_CATEGORIES:
        return None

    data = _load_data()
    prefs = data.get("preferences", {})

    # Check master toggle first, then category-specific toggle
    if not prefs.get("enabled", True):
        return None
    if not prefs.get(event_type, False):
        return None

    event = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "title": title[:200] if title else "",
        "message": message[:1000] if message else "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False,
    }

    # Insert at beginning (newest first)
    data.setdefault("events", []).insert(0, event)

    # Prune oldest events
    if len(data["events"]) > MAX_EVENTS:
        data["events"] = data["events"][:MAX_EVENTS]

    _save_data(data)
    return event


def mark_read(event_id: str) -> bool:
    """Mark a single event as read. Returns True if found."""
    data = _load_data()
    for ev in data.get("events", []):
        if ev.get("id") == event_id:
            ev["read"] = True
            _save_data(data)
            return True
    return False


def mark_all_read() -> int:
    """Mark all events as read. Returns count of events marked."""
    data = _load_data()
    count = 0
    for ev in data.get("events", []):
        if not ev.get("read", False):
            ev["read"] = True
            count += 1
    if count > 0:
        _save_data(data)
    return count


def clear_all() -> int:
    """Remove all notification events. Returns count of events removed."""
    data = _load_data()
    count = len(data.get("events", []))
    data["events"] = []
    _save_data(data)
    return count
