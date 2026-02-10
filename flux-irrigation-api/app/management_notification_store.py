"""
Flux Open Home - Management Notification Store
================================================
Manages management notification preferences and in-app notification events
for the management dashboard. Tracks issue lifecycle events (new issue,
acknowledged, service scheduled, resolved) across all customers.

Events are recorded by the server-side health check loop (new issues)
and by management API endpoints (acknowledge, schedule, resolve).
The store checks preferences internally — if an event type is disabled,
the event is silently dropped.

Persists data in /data/management_notifications.json.
"""

import json
import os
import uuid
from datetime import datetime, timezone


NOTIFICATION_FILE = "/data/management_notifications.json"

MAX_EVENTS = 200  # Prune oldest beyond this

# Valid notification event type keys
EVENT_TYPES = [
    "new_issue",            # New issue reported by homeowner
    "acknowledged",         # Issue acknowledged by management
    "service_scheduled",    # Service date set/updated
    "resolved",             # Issue resolved
    "returned",             # Homeowner returned a resolved issue
]

DEFAULT_DATA = {
    "version": 1,
    "preferences": {
        "notify_new_issue": True,
        "notify_acknowledged": True,
        "notify_service_scheduled": True,
        "notify_resolved": True,
        "notify_returned": True,
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
                for pkey, pdefault in DEFAULT_DATA["preferences"].items():
                    if pkey not in prefs:
                        prefs[pkey] = pdefault
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
    valid_keys = set(DEFAULT_DATA["preferences"].keys())
    for key, value in prefs.items():
        if isinstance(value, bool) and key in valid_keys:
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


def record_event(
    event_type: str,
    customer_id: str,
    customer_name: str,
    title: str,
    message: str = "",
    severity: str = "",
) -> dict | None:
    """Record a management notification event if the preference for event_type is enabled.

    Returns the created event dict, or None if the preference is disabled
    or the event_type is invalid.
    Prunes the events list to MAX_EVENTS.
    """
    if event_type not in EVENT_TYPES:
        return None

    data = _load_data()
    prefs = data.get("preferences", {})

    # Check preference for this event type
    pref_key = f"notify_{event_type}"
    if not prefs.get(pref_key, True):
        return None

    event = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "customer_id": customer_id,
        "customer_name": customer_name[:100] if customer_name else "",
        "title": title[:200] if title else "",
        "message": message[:1000] if message else "",
        "severity": severity,
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
