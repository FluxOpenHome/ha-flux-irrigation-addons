"""
Flux Open Home - Configuration Change Log
==========================================
Tracks all configuration changes made to the irrigation system.
Rolling buffer of 1000 entries stored in JSONL format.
Records WHO made the change (Homeowner/Management), WHEN, and WHAT changed.
"""

import json
import os
import re
from datetime import datetime, timezone

CHANGELOG_FILE = "/data/config_changelog.jsonl"
MAX_ENTRIES = 1000


def log_change(actor: str, category: str, description: str, details: dict = None, ai_suggested: bool = False):
    """Append a configuration change entry. Trim to MAX_ENTRIES."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "category": category,
        "description": description,
    }
    if details:
        entry["details"] = details
    if ai_suggested:
        entry["ai_suggested"] = True

    try:
        os.makedirs(os.path.dirname(CHANGELOG_FILE), exist_ok=True)
        with open(CHANGELOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Trim to MAX_ENTRIES if needed
        _trim_changelog()
    except Exception as e:
        print(f"[CHANGELOG] Failed to write entry: {e}")


def _trim_changelog():
    """Keep only the last MAX_ENTRIES lines in the changelog file."""
    try:
        with open(CHANGELOG_FILE, "r") as f:
            lines = f.readlines()
        if len(lines) > MAX_ENTRIES:
            with open(CHANGELOG_FILE, "w") as f:
                f.writelines(lines[-MAX_ENTRIES:])
    except Exception as e:
        print(f"[CHANGELOG] Failed to trim: {e}")


def get_changelog(limit: int = 200) -> list[dict]:
    """Read changelog entries, newest first."""
    if not os.path.exists(CHANGELOG_FILE):
        return []
    entries = []
    try:
        with open(CHANGELOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []
    # Return newest first, limited
    entries.reverse()
    return entries[:limit]


def export_changelog_csv() -> str:
    """Return CSV string of all entries."""
    entries = get_changelog(limit=MAX_ENTRIES)
    lines = ["timestamp,actor,category,description"]
    for e in entries:
        lines.append(",".join([
            _csv_escape(e.get("timestamp", "")),
            _csv_escape(e.get("actor", "")),
            _csv_escape(e.get("category", "")),
            _csv_escape(e.get("description", "")),
        ]))
    return "\n".join(lines) + "\n"


def _csv_escape(value: str) -> str:
    """Escape a value for CSV output."""
    if not value:
        return ""
    if "," in value or '"' in value or "\n" in value:
        return '"' + value.replace('"', '""') + '"'
    return value


# --- Actor Detection ---

def get_actor(request=None) -> str:
    """Determine who made a change: 'Homeowner' or 'Management'.

    Checks X-Actor header (direct proxy) and query param (Nabu Casa proxy).
    Defaults to 'Homeowner' for local dashboard requests.
    """
    if request is None:
        return "Homeowner"
    # Check header first (direct proxy mode)
    actor = request.headers.get("X-Actor", "")
    if not actor:
        # Check query param (Nabu Casa proxy mode)
        actor = request.query_params.get("X-Actor", "")
    return actor if actor in ("Homeowner", "Management") else "Homeowner"


def is_ai_suggested(request=None) -> bool:
    """Check if this change was suggested by AI (Claude).

    Checks X-AI-Suggested header (direct proxy) and query param (Nabu Casa proxy).
    """
    if request is None:
        return False
    val = request.headers.get("X-AI-Suggested", "")
    if not val:
        val = request.query_params.get("X-AI-Suggested", "")
    return val.lower() in ("true", "1", "yes")


# --- Friendly Name Helpers ---

def friendly_entity_name(entity_id: str) -> str:
    """Convert an entity_id to a human-readable name for the changelog.

    Examples:
      number.irrigation_system_zone_1 → "Zone 1 duration"
      number.irrigation_controller_zone_2_duration → "Zone 2 duration"
      switch.irrigation_system_zone_1_enable → "Zone 1 schedule enable"
      switch.irrigation_system_monday → "Monday"
      number.irrigation_system_start_time_1 → "Start Time 1"
    """
    if "." not in entity_id:
        return entity_id

    name = entity_id.split(".", 1)[1]

    # Strip common prefixes
    for prefix in ("irrigation_system_", "irrigation_controller_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break

    # Zone duration: "zone_N" or "zone_N_duration" or "zone_N_run_duration"
    m = re.match(r"zone_(\d+)(?:_(?:run_)?duration)?$", name)
    if m:
        return f"Zone {m.group(1)} duration"

    # Zone enable: "zone_N_enable"
    m = re.match(r"zone_(\d+)_enable$", name)
    if m:
        return f"Zone {m.group(1)} schedule enable"

    # Day switches
    days = {
        "monday": "Monday", "tuesday": "Tuesday", "wednesday": "Wednesday",
        "thursday": "Thursday", "friday": "Friday", "saturday": "Saturday",
        "sunday": "Sunday",
    }
    if name.lower() in days:
        return days[name.lower()]

    # Start times: "start_time_N"
    m = re.match(r"start_time_(\d+)$", name)
    if m:
        return f"Start Time {m.group(1)}"

    # Fallback: replace underscores and title-case
    return name.replace("_", " ").title()
