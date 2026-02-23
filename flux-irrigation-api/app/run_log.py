"""
Flux Open Home - Run History Logger
====================================
Persistent JSONL-based run history with weather context.
Captures zone on/off events from all sources:
  - Manual starts/stops (API, dashboard)
  - Timed shutoffs
  - Weather pauses, system pauses, stop-all
  - Schedule-triggered runs (detected by background state watcher)

Each entry includes weather conditions at the time of the event.
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

RUN_LOG_FILE = "/data/run_history.jsonl"

_ZONE_NUM_RE = re.compile(r'zone[_]?(\d+)', re.IGNORECASE)


def _extract_zone_number(entity_id: str) -> int:
    """Extract numeric zone number from entity_id (e.g. 'switch.xxx_zone_3' → 3)."""
    m = _ZONE_NUM_RE.search(entity_id)
    return int(m.group(1)) if m else 0

# Cache of last-known zone states for the background watcher
_zone_states: dict[str, str] = {}
# Cache of zone start times for duration calculation
_zone_start_times: dict[str, str] = {}

# Pre-announced zone sources — set BEFORE calling ha_client.call_service() so
# the WebSocket watcher knows the real source even if the log entry hasn't been
# written yet.  This fixes a race condition where the WebSocket event arrives
# before log_zone_event() is called, causing the moisture system to default to
# "schedule" source and auto-skip manual/API-triggered zone starts.
_pre_announced_sources: dict[str, tuple[str, float]] = {}  # entity_id -> (source, timestamp)
_PRE_ANNOUNCE_TTL_S = 15  # auto-expire after 15 seconds


def pre_announce_zone_source(entity_id: str, source: str) -> None:
    """Register the intended source for an upcoming zone state change.

    Call this BEFORE ha_client.call_service() to win the race against the
    WebSocket watcher.  The entry auto-expires after _PRE_ANNOUNCE_TTL_S.
    """
    import time
    _pre_announced_sources[entity_id] = (source, time.time())
    print(f"[RUN_LOG] Pre-announced source for {entity_id}: {source}")


def _consume_pre_announced_source(entity_id: str) -> Optional[str]:
    """Pop and return the pre-announced source if it hasn't expired."""
    import time
    entry = _pre_announced_sources.pop(entity_id, None)
    if entry is None:
        return None
    source, ts = entry
    if time.time() - ts > _PRE_ANNOUNCE_TTL_S:
        return None  # expired
    return source

# --- Remote ↔ Controller entity mirroring ---
# Guard to prevent infinite loops: when we mirror a state change, the resulting
# state_changed event should be ignored.
_remote_mirror_guard: set = set()  # entity_ids currently being mirrored

# Cached entity maps (rebuilt when config changes)
_remote_maps_cache: dict = {}  # {"r2c": {}, "c2r": {}, "remote_all": set(), "controller_status": set()}
_remote_maps_logged: bool = False

# Per-device entity maps for multi-remote support (max 5 remotes)
_remote_maps_by_device: dict = {}  # device_id -> maps dict
_remote_maps_logged_by_device: dict = {}  # device_id -> bool

# Per-device sync/reconnect state
_remote_reconnect_pending_by_device: dict = {}  # device_id -> bool
_reconnect_sync_running_by_device: dict = {}  # device_id -> bool
_sync_needed_by_device: dict = {}  # device_id -> entity_id or "" (searched, not found) or None (not searched)
_manual_stop_by_device: dict = {}  # device_id -> entity_id or "" or None

# Cached set of zone numbers that are pump/relay/master valve.
# Populated by update_special_zone_nums() (called from sync_remote_settings).
# Read by the synchronous map builders to filter out pump/MV zone entities.
_special_zone_nums: set[int] = set()


def update_special_zone_nums(zone_nums: set[int]):
    """Update the cached set of special (pump/relay/master valve) zone numbers.

    Called from sync_remote_settings() after async detection completes.
    The synchronous map builders read this to filter pump/MV zone entities.
    """
    global _special_zone_nums
    if zone_nums != _special_zone_nums:
        _remote_log(f"Broker: special zone numbers updated: {_special_zone_nums} -> {zone_nums}")
        _special_zone_nums = zone_nums


def get_special_zone_nums() -> set[int]:
    """Return the cached set of special zone numbers."""
    return _special_zone_nums


def _filter_special_zone_entities(entity_ids: set[str]) -> set[str]:
    """Remove entities belonging to pump/relay/master valve zones.

    Uses the cached _special_zone_nums set.  If no special zones are
    configured, returns the input unchanged (no-op fast path).
    """
    if not _special_zone_nums:
        return entity_ids
    return {eid for eid in entity_ids
            if not (_extract_zone_number(eid) and _extract_zone_number(eid) in _special_zone_nums)}


# Reverse lookup: entity_id -> device_id (for fast routing in WebSocket handler)
_entity_to_device_cache: dict = {}  # entity_id -> device_id

# Suffix aliases — different firmware names that refer to the same function.
# Both sides are normalized to the canonical (value) name.
_SUFFIX_ALIASES = {
    "start_stop_resume": "start_stop",
    "main_start_stop": "start_stop",
    "progress_percent": "progress",
}


def _convert_time_for_relay(value: str, source_eid: str) -> str:
    """Convert time format when relaying start_time values between devices.

    If the system is in 12hr mode and the value looks like 24hr time (e.g. "17:00"),
    convert to 12hr format (e.g. "5:00 PM").
    If the system is in 24hr mode and the value looks like 12hr time (e.g. "5:00 PM"),
    convert to 24hr format (e.g. "17:00").
    Non-start-time entities pass through unchanged.
    """
    suffix = _extract_entity_suffix(source_eid)
    if "start_time" not in suffix:
        return value

    # Read current time format setting
    use_12h = True
    try:
        sf = "/data/settings.json"
        if os.path.exists(sf):
            with open(sf) as f:
                use_12h = json.load(f).get("time_format", "12h") != "24h"
    except Exception:
        pass

    value = value.strip()

    if use_12h:
        # Convert 24hr → 12hr if value looks like "HH:MM" (no AM/PM)
        m = re.match(r'^(\d{1,2}):(\d{2})$', value)
        if m:
            h, mn = int(m.group(1)), m.group(2)
            if h == 0:
                return f"12:{mn} AM"
            elif h < 12:
                return f"{h}:{mn} AM"
            elif h == 12:
                return f"12:{mn} PM"
            else:
                return f"{h - 12}:{mn} PM"
    else:
        # Convert 12hr → 24hr if value contains AM/PM
        m = re.match(r'^(\d{1,2}):(\d{2})\s*(AM|PM)$', value, re.IGNORECASE)
        if m:
            h, mn, ap = int(m.group(1)), m.group(2), m.group(3).upper()
            if ap == "AM":
                h = 0 if h == 12 else h
            else:
                h = h if h == 12 else h + 12
            return f"{h}:{mn}"

    return value  # Already in correct format or unrecognized


# Suffixes that are one-way: add-on → remote only (remote changes are ignored)
_ONE_WAY_SUFFIXES = {
    "zone_count",               # pushed via sync_remote_settings()
    "use_12_hour_format",       # pushed via sync_remote_settings()
    "sync_needed",              # remote boot flag — add-on reads it, never mirrors it
    "pump_start_master_valve",  # pushed via sync_remote_settings()
}

# Duration suffix pattern — zone_N_duration entities are NOT broker-mirrored.
# They use the add-on's base_duration system instead:
#   - Add-on → Remote: pushes BASE durations (not the factored controller values)
#   - Remote → Add-on: updates base_durations in moisture.json (then re-applies factors)
# This prevents the factored value on the controller from overwriting the remote's
# input field, and prevents remote changes from bypassing the factor system.
_DURATION_SUFFIX_RE = re.compile(r'^zone_\d+_duration$')

# --- Remote Debug Log ---
_REMOTE_DEBUG_LOG_FILE = "/data/remote_debug.log"
_REMOTE_DEBUG_LOG_MAX_LINES = 500


def _remote_log(msg: str):
    """Write a timestamped message to both console and the broker debug log file."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(f"[BROKER] {msg}")
    try:
        with open(_REMOTE_DEBUG_LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def get_remote_debug_log(max_lines: int = 200) -> list[str]:
    """Read the last N lines of the remote debug log."""
    if not os.path.exists(_REMOTE_DEBUG_LOG_FILE):
        return []
    try:
        with open(_REMOTE_DEBUG_LOG_FILE) as f:
            lines = f.readlines()
        return [l.rstrip() for l in lines[-max_lines:]]
    except Exception:
        return []


def clear_remote_debug_log():
    """Clear the remote debug log file."""
    try:
        with open(_REMOTE_DEBUG_LOG_FILE, "w") as f:
            f.write("")
    except Exception:
        pass


def log_zone_event(
    entity_id: str,
    state: str,
    source: str = "api",
    zone_name: str = "",
    duration_seconds: Optional[float] = None,
    scheduled_minutes: Optional[float] = None,
):
    """Log a zone on/off event with current weather context.

    Args:
        entity_id: The HA entity_id (e.g. switch.zone_1)
        state: "on" or "off"
        source: Where this event originated (api, dashboard, timed_shutoff,
                weather_pause, system_pause, stop_all, schedule, unknown)
        zone_name: Human-readable zone name
        duration_seconds: For "off" events, how long the zone ran
        scheduled_minutes: The zone's scheduled run duration in minutes.
                          Used as fallback for water savings when base_durations
                          is not available (apply_factors_to_schedule disabled).
    """
    now = datetime.now(timezone.utc)
    entry = {
        "timestamp": now.isoformat(),
        "entity_id": entity_id,
        "zone_name": zone_name,
        "state": state,
        "source": source,
        "duration_seconds": duration_seconds,
    }

    # Capture weather context at this moment
    try:
        from routes.weather import _get_current_weather_snapshot
        wx = _get_current_weather_snapshot()
        if wx and wx.get("condition"):
            entry["weather"] = {
                "condition": wx.get("condition", ""),
                "temperature": wx.get("temperature"),
                "humidity": wx.get("humidity"),
                "wind_speed": wx.get("wind_speed"),
                "watering_multiplier": wx.get("watering_multiplier", 1.0),
                "active_adjustments": [
                    a.get("rule", "") for a in wx.get("active_adjustments", [])
                ],
            }
    except Exception:
        pass

    # Capture moisture context at this moment
    try:
        from routes.moisture import (
            _load_data as _load_moisture_data,
            calculate_zone_moisture_multiplier,
            get_cached_sensor_states,
        )
        moisture_data = _load_moisture_data()
        if moisture_data.get("enabled") and moisture_data.get("probes") and entity_id != "system":
            # Check if this zone has any mapped probes (sync-safe check)
            has_probes = any(
                entity_id in probe.get("zone_mappings", [])
                for probe in moisture_data.get("probes", {}).values()
            )
            if has_probes:
                entry["moisture"] = {
                    "enabled": True,
                    "has_probes": True,
                    "last_evaluation": moisture_data.get("last_evaluation"),
                    "duration_adjustment_active": moisture_data.get("duration_adjustment_active", False),
                }
                # Compute moisture multiplier live from cached sensor data
                # (adjusted_durations may be empty/stale — this is always fresh)
                sensor_states = get_cached_sensor_states(moisture_data.get("probes", {}))
                zone_result = calculate_zone_moisture_multiplier(
                    entity_id, moisture_data, sensor_states,
                )
                moisture_mult = zone_result.get("multiplier")
                if moisture_mult is not None:
                    entry["moisture"]["moisture_multiplier"] = round(moisture_mult, 3)
                    entry["moisture"]["profile"] = zone_result.get("profile", "")
                    entry["moisture"]["reason"] = zone_result.get("reason", "")
                    entry["moisture"]["skip"] = zone_result.get("skip", False)
                    # Capture sensor readings (T/M/B) from probe details
                    for detail in zone_result.get("probe_details", []):
                        readings = detail.get("depth_readings", {})
                        if readings:
                            sr = {}
                            if "shallow" in readings:
                                sr["T"] = round(readings["shallow"].get("value", 0), 1)
                            if "mid" in readings:
                                sr["M"] = round(readings["mid"].get("value", 0), 1)
                            if "deep" in readings:
                                sr["B"] = round(readings["deep"].get("value", 0), 1)
                            if sr:
                                entry["moisture"]["sensor_readings"] = sr
                            break  # Use first probe's readings
                # Also include adjusted duration info if available
                adjusted = moisture_data.get("adjusted_durations", {})
                for dur_eid, adj in adjusted.items():
                    zone_suffix = entity_id.split(".", 1)[1] if "." in entity_id else entity_id
                    if zone_suffix in dur_eid:
                        entry["moisture"]["combined_multiplier"] = adj.get("combined_multiplier")
                        entry["moisture"]["original_duration"] = adj.get("original")
                        entry["moisture"]["adjusted_duration"] = adj.get("adjusted")
                        break
    except Exception as e:
        print(f"[RUN_LOG] Moisture context capture error: {e}")
        import traceback
        traceback.print_exc()

    # Track start times for duration calculation
    if state in ("on", "open"):
        _zone_start_times[entity_id] = now.isoformat()
    elif state in ("off", "closed") and duration_seconds is None:
        # Calculate duration from tracked start time
        start_ts = _zone_start_times.pop(entity_id, None)
        if start_ts:
            try:
                start_dt = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
                entry["duration_seconds"] = round((now - start_dt).total_seconds(), 1)
            except (ValueError, TypeError):
                pass

    # Calculate water savings on OFF events — ONLY for system-initiated reductions.
    # Manual starts/stops do NOT count. The system must have reduced or stopped
    # the zone via weather adjustments, rain sensor, or moisture probes.
    #
    # Sources that indicate system-initiated savings:
    #   weather_pause, pause_enforced  — weather/rain stopped or prevented the run
    #   moisture_skip                  — zone skipped due to soil saturation
    #   moisture_cutoff                — zone cut short mid-run due to moisture threshold
    #   schedule                       — normal schedule run that was shortened by applied factors
    #
    # Sources that do NOT count (user-initiated):
    #   api, dashboard, timed_shutoff, stop_all, unknown
    SAVINGS_SOURCES = {
        "weather_pause", "pause_enforced", "moisture_skip", "weather_skip",
        "moisture_cutoff", "schedule", "system_pause", "precip_adjustment",
    }
    actual_dur = entry.get("duration_seconds")
    # For moisture_skip / weather_skip events, the zone never ran — duration
    # is 0 but the full base duration was saved.  Treat actual_dur=0 as valid.
    is_skip = state in ("moisture_skip", "weather_skip")
    if (state in ("off", "closed", "moisture_skip", "weather_skip")
            and (is_skip or (actual_dur and actual_dur > 0))
            and source in SAVINGS_SOURCES):
        try:
            from routes.moisture import _load_data as _load_moisture_data
            import zone_nozzle_data

            moisture_data = _load_moisture_data()
            base_durations = moisture_data.get("base_durations", {})
            zone_suffix = entity_id.split(".", 1)[1] if "." in entity_id else entity_id

            # Find the base (original schedule) duration for this zone
            base_minutes = None
            for dur_eid, bd in base_durations.items():
                if zone_suffix in dur_eid:
                    base_minutes = bd.get("base_value")
                    break

            # Fallback: if base_durations is empty (apply_factors_to_schedule
            # not enabled), use the scheduled_minutes passed by the caller.
            # For weather_skip events this is the zone's configured run duration
            # — the full amount that would have run but was prevented.
            if base_minutes is None and scheduled_minutes is not None and scheduled_minutes > 0:
                base_minutes = scheduled_minutes

            if base_minutes is not None and base_minutes > 0:
                actual_minutes = (actual_dur or 0) / 60.0
                saved_minutes = base_minutes - actual_minutes

                if saved_minutes > 0.05:  # Only record meaningful savings (>3 seconds)
                    # Get GPM for this zone
                    heads_data = zone_nozzle_data.get_zone_heads(entity_id)
                    total_gpm = heads_data.get("total_gpm", 0)

                    entry["water_saved_minutes"] = round(saved_minutes, 2)
                    entry["water_saved_source"] = source
                    if total_gpm > 0:
                        water_saved = round(saved_minutes * total_gpm, 2)
                        entry["water_saved_gallons"] = water_saved
                        print(f"[RUN_LOG] Water saved ({source}): {entity_id} ran "
                              f"{actual_minutes:.1f}min vs {base_minutes:.1f}min base → "
                              f"saved {saved_minutes:.1f}min × {total_gpm:.2f}GPM = "
                              f"{water_saved:.2f} gal")
                    else:
                        entry["water_saved_no_gpm"] = True
                        print(f"[RUN_LOG] Time saved ({source}, no GPM): {entity_id} ran "
                              f"{actual_minutes:.1f}min vs {base_minutes:.1f}min base → "
                              f"saved {saved_minutes:.1f}min")
        except Exception as e:
            print(f"[RUN_LOG] Water savings calculation error: {e}")

    try:
        os.makedirs(os.path.dirname(RUN_LOG_FILE), exist_ok=True)
        with open(RUN_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[RUN_LOG] Failed to write: {e}")


def log_probe_event(
    probe_id: str,
    event_type: str,
    display_name: str = "",
    zone_entity_id: str = "",
    zone_name: str = "",
    details: Optional[dict] = None,
):
    """Log a moisture probe event (wake, moisture_skip, etc.).

    Args:
        probe_id: The probe identifier (e.g. "gophr_1")
        event_type: "probe_wake", "moisture_skip", etc.
        display_name: Human-readable probe name/alias
        zone_entity_id: The zone entity this event relates to (if any)
        zone_name: Human-readable zone name
        details: Extra context (sensor readings, multiplier, etc.)
    """
    now = datetime.now(timezone.utc)
    entry = {
        "timestamp": now.isoformat(),
        "entity_id": zone_entity_id or f"probe.{probe_id}",
        "zone_name": zone_name,
        "state": event_type,
        "source": "moisture_probe",
        "probe_id": probe_id,
        "probe_name": display_name or probe_id,
    }
    if details:
        entry.update(details)

    try:
        os.makedirs(os.path.dirname(RUN_LOG_FILE), exist_ok=True)
        with open(RUN_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[RUN_LOG] Failed to write probe event: {e}")


def get_run_history(hours: int = 24, zone_id: Optional[str] = None, limit: int = 5000) -> list[dict]:
    """Read run history entries from the JSONL log.

    Args:
        hours: Only return events from the last N hours
        zone_id: Filter to a specific entity_id
        limit: Max entries to return
    """
    if not os.path.exists(RUN_LOG_FILE):
        return []

    cutoff = None
    if hours > 0:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    # Filter out hidden zones beyond detected_zone_count
    max_zones = 0
    try:
        from config import get_config
        cfg = get_config()
        max_zones = cfg.detected_zone_count if hasattr(cfg, "detected_zone_count") else 0
    except Exception:
        pass

    entries = []
    try:
        with open(RUN_LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if cutoff and entry.get("timestamp", "") < cutoff:
                        continue
                    is_probe_event = entry.get("source") == "moisture_probe"
                    if zone_id and entry.get("entity_id") != zone_id:
                        # Allow probe events through if they relate to the filtered zone
                        if not is_probe_event:
                            continue
                    # Skip hidden zones beyond detected expansion board count
                    # (but never filter out probe events)
                    if max_zones > 0 and not is_probe_event:
                        zn = _extract_zone_number(entry.get("entity_id", ""))
                        if zn > max_zones:
                            continue
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []

    # Return most recent entries, sorted newest first
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]


def clear_run_history():
    """Delete the run history log file."""
    try:
        if os.path.exists(RUN_LOG_FILE):
            os.remove(RUN_LOG_FILE)
        return True
    except Exception as e:
        print(f"[RUN_LOG] Failed to clear: {e}")
        return False


def cleanup_run_history(retention_days: int = 365):
    """Remove run history entries older than retention period."""
    if not os.path.exists(RUN_LOG_FILE):
        return
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    kept = []
    try:
        with open(RUN_LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("timestamp", "") >= cutoff:
                        kept.append(line)
                except json.JSONDecodeError:
                    continue
        with open(RUN_LOG_FILE, "w") as f:
            for line in kept:
                f.write(line + "\n")
    except Exception as e:
        print(f"[RUN_LOG] Failed to cleanup: {e}")


async def _handle_state_change(entity_id: str, new_state: str, old_state: str,
                               zone_name: str, source: str = "schedule"):
    """Process a zone state change: log the event."""
    import ha_client

    global _zone_states

    is_on = new_state in ("on", "open")
    is_off = new_state in ("off", "closed")

    if is_on or is_off:
        # Skip OFF events where we never saw the ON — these are state snapshots
        # from add-on restarts or initial WebSocket subscription, not real runs.
        # Exception: if there's a recent unmatched ON event in the log (zone was
        # running when the add-on restarted), still log the OFF to close the cycle.
        if is_off and entity_id not in _zone_start_times:
            recent = get_run_history(hours=24, zone_id=entity_id, limit=1)
            if recent and recent[0].get("state") in ("on", "open"):
                # There's an unmatched ON — this OFF closes the cycle, let it through
                pass
            else:
                _zone_states[entity_id] = new_state
                return

        # Only log as "schedule" source if we don't already have
        # a recent entry (to avoid duplicating API-triggered events)
        recent = get_run_history(hours=1, zone_id=entity_id, limit=1)
        already_logged = False
        if recent:
            last_ts = recent[0].get("timestamp", "")
            last_state = recent[0].get("state", "")
            try:
                last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - last_dt).total_seconds()
                if age < 5 and last_state == new_state:
                    already_logged = True
            except (ValueError, TypeError):
                pass

        if not already_logged:
            log_zone_event(
                entity_id=entity_id,
                state=new_state,
                source=source,
                zone_name=zone_name,
            )

    _zone_states[entity_id] = new_state

    # Notify moisture probe module for Gophr sleep/wake control
    if is_on or is_off:
        try:
            from routes.moisture import on_zone_state_change
            # Determine effective source: if the event was already logged by
            # the API endpoint (manual start), use that source so moisture
            # module knows not to auto-skip manual runs.
            #
            # Priority:
            # 1. Pre-announced source (set before call_service, wins the race)
            # 2. Already-logged source from run history
            # 3. Default source parameter ("schedule")
            pre_source = _consume_pre_announced_source(entity_id)
            if pre_source:
                effective_source = pre_source
                print(f"[RUN_LOG] Using pre-announced source for {entity_id}: {pre_source}")
            elif already_logged and recent:
                effective_source = recent[0].get("source", source)
            else:
                effective_source = source
            await on_zone_state_change(entity_id, new_state, effective_source)
        except Exception as e:
            print(f"[RUN_LOG] Moisture zone state hook error: {e}")


def _extract_entity_suffix(entity_id: str) -> str:
    """Extract the functional suffix from an entity_id by stripping device name prefix.

    Both controller and remote share suffixes like _zone_1, _schedule_monday,
    _zone_1_duration, _schedule_start_time_1, etc.  The device name portion
    (e.g. 'irrigation_controller_abc123' or 'irrigation_remote_12b894') differs,
    but the functional tail is the same.

    Strategy: find the longest known suffix pattern that matches the tail of the
    entity_id (after the domain prefix 'switch.', 'number.', etc.).
    Aliases are normalized so controller and remote use the same key even when
    firmware names differ (e.g. 'start_stop_resume' ↔ 'start_stop').
    """
    # Strip domain prefix
    if "." in entity_id:
        slug = entity_id.split(".", 1)[1]
    else:
        slug = entity_id

    # Known suffix patterns — ordered longest-first so we match greedily
    # Schedule times — handle multiple naming conventions:
    #   _schedule_start_time_N, _start_time_N, _schedule_N_start_time
    #   Also handles firmware names with extra description after the number
    #   e.g. _start_time_1_24hr_06_00_or_12hr_6_00_am, _start_time_2_optional
    m = re.search(r'(?:schedule_)?start_time_(\d+)', slug)
    if m:
        return f"schedule_start_time_{m.group(1)}"
    # Zone durations
    m = re.search(r'zone_(\d+)_dur(?:ation)?$', slug)
    if m:
        return f"zone_{m.group(1)}_duration"
    # Zone switches (plain zone_N, NOT enable_zone_N)
    m = re.search(r'(?<!enable_)zone_(\d+)$', slug)
    if m:
        return f"zone_{m.group(1)}"
    # Enable zone switches
    m = re.search(r'enable_zone_(\d+)$', slug)
    if m:
        return f"enable_zone_{m.group(1)}"
    # Schedule day switches
    for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"):
        if slug.endswith(f"_schedule_{day}") or slug.endswith(f"_{day}"):
            if "schedule" in slug or day in slug:
                return f"schedule_{day}"
    # Named entities — check longest variants first, then shorter aliases.
    # Both variants normalize to the SAME key so controller ↔ remote match.
    for suffix in (
        "auto_advance", "schedule_enabled",
        "start_stop_resume",  # controller firmware name → normalized to "start_stop"
        "main_start_stop",    # alternate controller name → normalized to "start_stop"
        "start_stop",         # remote firmware name → normalized to "start_stop"
        "valve_status", "status",
        "time_remaining", "progress", "progress_percent",
        "active_zone", "zone_count", "detected_zones",
        "use_12_hour_format", "rain_sensor", "pause",
    ):
        if slug.endswith(f"_{suffix}") or slug == suffix:
            return _SUFFIX_ALIASES.get(suffix, suffix)
    # Fallback: return everything after the last hex-like mac segment
    # e.g. 'irrigation_remote_12b894_schedule_monday' → try splitting on known device patterns
    return slug


def _classify_device_entities(entity_ids: list[str]) -> dict[tuple[str, str], str]:
    """Classify a device's entities by (domain, function_key) -> entity_id.

    Each entity is independently analyzed to determine what function it serves.
    This is one half of the broker model — the other device is classified
    separately, then the two inventories are matched by function.
    """
    inventory: dict[tuple[str, str], str] = {}
    for eid in entity_ids:
        domain = eid.split(".")[0] if "." in eid else ""
        func_key = _extract_entity_suffix(eid)
        inventory[(domain, func_key)] = eid

    # Post-process: number entities with plain zone_N suffix are durations, not switches.
    # ESPHome SprinklerController names durations as "zone_N" (no _duration suffix),
    # but the remote uses "zone_N_duration". Reclassify so they match.
    import re
    remap = {}
    for (domain, func), eid in list(inventory.items()):
        if domain == "number" and re.fullmatch(r'zone_\d+', func):
            new_func = func + "_duration"
            remap[(domain, func)] = (domain, new_func)
    for old_key, (new_domain, new_func) in remap.items():
        eid = inventory.pop(old_key)
        inventory[(new_domain, new_func)] = eid

    return inventory


def invalidate_remote_maps():
    """Clear cached entity maps so they are rebuilt on next access.

    Call this when the remote device config changes (e.g. add/remove remote).
    """
    global _remote_maps_cache, _remote_maps_logged
    global _remote_maps_by_device, _remote_maps_logged_by_device
    global _sync_needed_by_device, _manual_stop_by_device, _entity_to_device_cache
    _remote_maps_cache = {}
    _remote_maps_logged = False
    _remote_maps_by_device = {}
    _remote_maps_logged_by_device = {}
    _sync_needed_by_device = {}
    _manual_stop_by_device = {}
    _entity_to_device_cache = {}


def _build_remote_entity_maps_for_device(device_id: str) -> dict:
    """Build entity maps for a single remote device.

    Returns {"r2c": {}, "c2r": {}, "status_map": {}, "remote_all": set(), ...}
    Uses the same classification logic as _build_remote_entity_maps but scoped to one device.
    """
    global _remote_maps_by_device, _remote_maps_logged_by_device

    if device_id in _remote_maps_by_device and _remote_maps_by_device[device_id]:
        return _remote_maps_by_device[device_id]

    from config import get_config
    config = get_config()
    device_entities = config.allowed_remote_entities_by_device.get(device_id, [])
    if not device_entities:
        empty = {"r2c": {}, "c2r": {}, "status_map": {}, "remote_all": set(), "controller_watched": set()}
        _remote_maps_by_device[device_id] = empty
        return empty

    # Build using the same logic as the merged builder but scoped to this device's entities
    all_controller = (set(config.allowed_zone_entities or [])
                      | set(config.allowed_control_entities or [])
                      | set(config.allowed_sensor_entities or []))
    # Exclude entities belonging to pump/relay/master valve zones
    all_controller = _filter_special_zone_entities(all_controller)
    controller_inv = _classify_device_entities(list(all_controller))
    remote_inv = _classify_device_entities(device_entities)

    r2c = {}
    c2r = {}
    status_map = {}
    controller_watched = set()

    for func_key, remote_eid in remote_inv.items():
        ctrl_eid = controller_inv.get(func_key)
        if not ctrl_eid:
            continue
        suffix = _extract_entity_suffix(remote_eid)
        # Status entities are one-way controller→remote
        if remote_eid.startswith("text.") and suffix in ("valve_status", "time_remaining", "active_zone"):
            status_map[ctrl_eid] = remote_eid
            controller_watched.add(ctrl_eid)
        else:
            r2c[remote_eid] = ctrl_eid
            c2r[ctrl_eid] = remote_eid
            controller_watched.add(ctrl_eid)

    result = {
        "r2c": r2c,
        "c2r": c2r,
        "status_map": status_map,
        "remote_all": set(device_entities),
        "controller_watched": controller_watched,
    }
    _remote_maps_by_device[device_id] = result

    if not _remote_maps_logged_by_device.get(device_id, False):
        _remote_log(f"Broker: built maps for device {device_id[:12]}: "
                    f"{len(r2c)} bidirectional, {len(status_map)} status, "
                    f"{len(device_entities)} remote entities")
        _remote_maps_logged_by_device[device_id] = True

    return result


def _get_entity_device_id(entity_id: str) -> str | None:
    """Look up which remote device an entity belongs to."""
    global _entity_to_device_cache
    if entity_id in _entity_to_device_cache:
        return _entity_to_device_cache[entity_id] or None

    from config import get_config
    config = get_config()
    for did, entities in config.allowed_remote_entities_by_device.items():
        if entity_id in entities:
            _entity_to_device_cache[entity_id] = did
            return did
    _entity_to_device_cache[entity_id] = ""
    return None


def _build_remote_entity_maps() -> dict:
    """Build bidirectional entity mapping between controller and remote.

    Uses a two-phase broker model:
      Phase 1: Classify each device's entities independently by function.
      Phase 2: Match the two inventories by (domain_class, function_key).

    The add-on acts as the middleman — it understands what each entity does
    on each device and brokers state changes between them.

    Returns dict with:
      r2c: remote_entity -> controller_entity (for user actions on remote)
      c2r: controller_entity -> remote_entity (for mirroring state to remote)
      remote_all: set of ALL remote entity IDs to watch
      controller_watched: set of controller entity IDs that have a remote counterpart
      status_map: controller_sensor -> remote_text (one-way: controller->remote)
      controller_inv: classified controller inventory (for debug UI)
      remote_inv: classified remote inventory (for debug UI)
    """
    global _remote_maps_cache, _remote_maps_logged
    # Return cached maps if already built (rebuild via invalidate_remote_maps())
    if _remote_maps_cache:
        return _remote_maps_cache

    from config import get_config
    config = get_config()

    if not config.allowed_remote_entities:
        _remote_maps_cache = {"r2c": {}, "c2r": {}, "remote_all": set(),
                              "controller_watched": set(), "status_map": {},
                              "controller_inv": {}, "remote_inv": {}}
        return _remote_maps_cache

    # ── Phase 1: Classify each device's entities independently ──
    all_controller_raw = (set(config.allowed_zone_entities or [])
                          | set(config.allowed_control_entities or [])
                          | set(config.allowed_sensor_entities or []))
    # Exclude entities belonging to pump/relay/master valve zones
    all_controller = _filter_special_zone_entities(all_controller_raw)
    if not _remote_maps_logged and len(all_controller) < len(all_controller_raw):
        _remote_log(f"Broker: filtered {len(all_controller_raw) - len(all_controller)} "
                    f"entities from special zones {_special_zone_nums}")
    controller_inv = _classify_device_entities(list(all_controller))
    remote_inv = _classify_device_entities(list(config.allowed_remote_entities))

    # Log inventories on first build
    if not _remote_maps_logged:
        _remote_log(f"Controller inventory ({len(controller_inv)} entities):")
        for (domain, func), eid in sorted(controller_inv.items(), key=lambda x: x[0][1]):
            _remote_log(f"  {domain:<12} | {func:<30} -> {eid}")
        _remote_log(f"Remote inventory ({len(remote_inv)} entities):")
        for (domain, func), eid in sorted(remote_inv.items(), key=lambda x: x[0][1]):
            _remote_log(f"  {domain:<12} | {func:<30} -> {eid}")

    # ── Phase 2: Match by function key ──
    # Build a remote lookup: also index by wildcard domain for cross-domain matching
    remote_by_func: dict[tuple[str, str], str] = {}
    for (domain, func), eid in remote_inv.items():
        remote_by_func[(domain, func)] = eid
        remote_by_func[("*", func)] = eid  # wildcard for cross-domain

    r2c: dict[str, str] = {}
    c2r: dict[str, str] = {}
    status_map: dict[str, str] = {}

    for (ctrl_domain, func), ctrl_eid in controller_inv.items():
        # Exact domain match first
        remote_eid = remote_by_func.get((ctrl_domain, func))

        # Cross-domain: controller text_sensor -> remote text (status entities)
        if not remote_eid and ctrl_domain == "text_sensor":
            remote_eid = remote_by_func.get(("text", func))
            if remote_eid:
                status_map[ctrl_eid] = remote_eid
                continue

        # Cross-domain: controller sensor -> remote text (time_remaining, progress, status)
        if not remote_eid and ctrl_domain == "sensor":
            remote_eid = remote_by_func.get(("text", func))
            if remote_eid:
                status_map[ctrl_eid] = remote_eid
                continue

        # Wildcard domain match with compatibility check
        if not remote_eid:
            remote_eid = remote_by_func.get(("*", func))
            if remote_eid:
                r_domain = remote_eid.split(".")[0] if "." in remote_eid else ""
                if ctrl_domain != r_domain and not (
                    {ctrl_domain, r_domain} <= {"switch", "valve"} or
                    {ctrl_domain, r_domain} <= {"text", "text_sensor"} or
                    ctrl_domain == r_domain
                ):
                    remote_eid = None

        if remote_eid and remote_eid != ctrl_eid:
            r2c[remote_eid] = ctrl_eid
            c2r[ctrl_eid] = remote_eid

    remote_all = set(config.allowed_remote_entities)

    _remote_maps_cache = {
        "r2c": r2c,
        "c2r": c2r,
        "remote_all": remote_all,
        "controller_watched": set(c2r.keys()) | set(status_map.keys()),
        "status_map": status_map,
        "controller_inv": controller_inv,
        "remote_inv": remote_inv,
    }

    # Log broker matching summary on first build only
    if not _remote_maps_logged:
        _remote_maps_logged = True
        _remote_log(f"Broker matched {len(r2c)} bidirectional + {len(status_map)} status (one-way) pairs:")
        for ctrl_eid, remote_eid in sorted(c2r.items(), key=lambda x: _extract_entity_suffix(x[0])):
            func = _extract_entity_suffix(ctrl_eid)
            _remote_log(f"  ↔ {func}: {ctrl_eid} ↔ {remote_eid}")
        for ctrl_eid, remote_eid in sorted(status_map.items(), key=lambda x: _extract_entity_suffix(x[0])):
            func = _extract_entity_suffix(ctrl_eid)
            _remote_log(f"  → {func}: {ctrl_eid} → {remote_eid} (one-way)")
        # Check schedule start_time mapping
        st_mapped = {k: v for k, v in c2r.items() if "start_time" in k.lower()}
        if st_mapped:
            _remote_log(f"  ✓ Start time mappings: {len(st_mapped)} found")
        else:
            _remote_log("  ✗ WARNING: No start_time entities mapped!")
        # Log unmatched entities
        mapped_ctrl = set(c2r.keys()) | set(status_map.keys())
        mapped_remote = set(r2c.keys()) | set(status_map.values())
        unmapped_ctrl = all_controller - mapped_ctrl
        unmapped_remote = remote_all - mapped_remote
        if unmapped_ctrl:
            _remote_log(f"  Unmatched controller ({len(unmapped_ctrl)}):")
            for eid in sorted(unmapped_ctrl):
                _remote_log(f"    - {_extract_entity_suffix(eid)}: {eid}")
        if unmapped_remote:
            _remote_log(f"  Unmatched remote ({len(unmapped_remote)}):")
            for eid in sorted(unmapped_remote):
                _remote_log(f"    - {_extract_entity_suffix(eid)}: {eid}")

    return _remote_maps_cache


def _get_remote_entities() -> set:
    """Get ALL remote entity IDs to watch via WebSocket."""
    try:
        from config import get_config
        config = get_config()
        if not config.allowed_remote_entities:
            return set()
        return set(config.allowed_remote_entities)
    except Exception:
        return set()


def _get_controller_entities_for_remote() -> set:
    """Get controller entity IDs that should be mirrored to the remote."""
    try:
        maps = _build_remote_entity_maps()
        return maps.get("controller_watched", set())
    except Exception:
        return set()


async def _mirror_entity_state(source_eid: str, target_eid: str, new_state: str):
    """Mirror a state change from one entity to another.

    Handles all entity domains: switch, number, text, select, button, valve.
    """
    # NEVER relay unavailable/unknown — these are not real values
    if new_state in ("unavailable", "unknown"):
        return

    import ha_client
    global _remote_mirror_guard

    _remote_mirror_guard.add(target_eid)
    try:
        target_domain = target_eid.split(".")[0] if "." in target_eid else ""

        if target_domain in ("switch", "light"):
            is_on = new_state in ("on", "open")
            svc = "turn_on" if is_on else "turn_off"
            await ha_client.call_service(target_domain, svc, {"entity_id": target_eid})
        elif target_domain == "valve":
            is_on = new_state in ("on", "open")
            svc = "open_valve" if is_on else "close_valve"
            await ha_client.call_service("valve", svc, {"entity_id": target_eid})
        elif target_domain == "number":
            try:
                val = float(new_state)
                await ha_client.call_service("number", "set_value",
                                             {"entity_id": target_eid, "value": val})
            except (ValueError, TypeError):
                return  # Can't mirror non-numeric state to number entity
        elif target_domain in ("text", "text_sensor"):
            # text entities accept set_value; text_sensor is read-only but
            # remote uses text (not text_sensor) so this works
            if target_domain == "text":
                write_val = _convert_time_for_relay(str(new_state), source_eid)
                await ha_client.call_service("text", "set_value",
                                             {"entity_id": target_eid, "value": write_val})
            # text_sensor can't be written to — skip
        elif target_domain == "select":
            await ha_client.call_service("select", "select_option",
                                         {"entity_id": target_eid, "option": str(new_state)})
        elif target_domain == "button":
            await ha_client.call_service("button", "press", {"entity_id": target_eid})
        else:
            return  # Unknown domain

        suffix = _extract_entity_suffix(source_eid)
        # Show time conversion in log if it happened
        converted_note = ""
        if target_domain == "text" and "start_time" in suffix:
            write_val = _convert_time_for_relay(str(new_state), source_eid)
            if write_val != str(new_state):
                converted_note = f" (converted {new_state} → {write_val})"
        _remote_log(f"Relayed {suffix}: {new_state}{converted_note} ({source_eid} → {target_eid})")
    except Exception as e:
        _remote_log(f"Relay FAILED {source_eid} → {target_eid}: {e}")
    finally:
        import asyncio
        async def _clear():
            await asyncio.sleep(2)
            _remote_mirror_guard.discard(target_eid)
        asyncio.create_task(_clear())


async def _handle_remote_entity_change(entity_id: str, new_state: str, old_state: str):
    """A remote entity changed — mirror to the controller AND all other remotes.

    One-way entities (zone_count, use_12_hour_format, pump_start_master_valve) are
    skipped — the remote cannot update those on the controller.

    Suppressed while the source device's reconnect is pending to prevent remote
    defaults from overwriting real controller values.
    """
    global _remote_reconnect_pending
    # Determine which remote device this entity belongs to
    source_device_id = _get_entity_device_id(entity_id)

    # LIVE CHECK: If this device's sync_needed switch is ON, block and trigger sync
    if source_device_id:
        sync_eid = _find_sync_needed_entity_for_device(source_device_id)
        if sync_eid and not _remote_reconnect_pending_by_device.get(source_device_id, True):
            try:
                import ha_client
                st = await ha_client.get_entity_state(sync_eid)
                if st and st.get("state") == "on":
                    _remote_reconnect_pending_by_device[source_device_id] = True
                    _remote_reconnect_pending = True
                    _remote_log(f"Suppressed remote→controller: {_extract_entity_suffix(entity_id)} "
                                f"= {new_state} — sync_needed is ON (live check, device {source_device_id[:12]})")
                    import asyncio
                    asyncio.create_task(_handle_remote_reconnect(entity_id, set(), source_device_id))
                    return
            except Exception:
                pass

    # Block remote→controller during this device's startup/reconnect sync
    if source_device_id and _remote_reconnect_pending_by_device.get(source_device_id, True):
        _remote_log(f"Suppressed remote→controller: {_extract_entity_suffix(entity_id)} "
                    f"= {new_state} (device {(source_device_id or '?')[:12]} syncing)")
        return
    # Fallback: global flag for backward compat
    if _remote_reconnect_pending:
        _remote_log(f"Suppressed remote→controller: {_extract_entity_suffix(entity_id)} "
                    f"= {new_state} (global sync in progress)")
        return

    # Skip one-way entities (add-on → remote only)
    suffix = _extract_entity_suffix(entity_id)
    if suffix in _ONE_WAY_SUFFIXES:
        return
    # Duration entities: update the add-on's base_durations instead of mirroring
    if _DURATION_SUFFIX_RE.match(suffix):
        await _handle_remote_duration_change(entity_id, new_state, suffix)
        # Also push the duration change to other remotes
        await _mirror_to_other_remotes(entity_id, source_device_id, new_state)
        return

    # Find controller entity via per-device map
    if source_device_id:
        maps = _build_remote_entity_maps_for_device(source_device_id)
    else:
        maps = _build_remote_entity_maps()
    controller_eid = maps["r2c"].get(entity_id)
    if not controller_eid:
        return
    # Mirror to controller
    await _mirror_entity_state(entity_id, controller_eid, new_state)
    # Mirror to all OTHER remotes (keep all remotes in sync)
    await _mirror_to_other_remotes(entity_id, source_device_id, new_state)


async def _mirror_to_other_remotes(source_entity_id: str, source_device_id: str | None, new_state: str):
    """Push a state change from one remote to all other connected remotes."""
    from config import get_config
    config = get_config()
    if len(config.remote_device_ids) < 2:
        return  # Only one remote, nothing to cross-sync
    suffix = _extract_entity_suffix(source_entity_id)
    for device_id in config.remote_device_ids:
        if device_id == source_device_id:
            continue  # Don't echo back to source
        if _remote_reconnect_pending_by_device.get(device_id, True):
            continue  # This remote is still syncing
        maps = _build_remote_entity_maps_for_device(device_id)
        # Find the matching remote entity by looking up controller_eid → other remote's entity
        # First find controller entity from source entity
        if source_device_id:
            src_maps = _build_remote_entity_maps_for_device(source_device_id)
            controller_eid = src_maps["r2c"].get(source_entity_id)
        else:
            controller_eid = _build_remote_entity_maps()["r2c"].get(source_entity_id)
        if not controller_eid:
            return
        other_remote_eid = maps["c2r"].get(controller_eid)
        if other_remote_eid:
            await _mirror_entity_state(source_entity_id, other_remote_eid, new_state)


async def _handle_remote_duration_change(remote_eid: str, new_state: str, suffix: str):
    """Handle a duration change from the remote by updating the add-on's base_durations.

    Instead of mirroring directly to the controller (which would bypass the factor
    system), we:
    1. Find the corresponding controller duration entity
    2. Update base_durations in moisture.json with the new value
    3. Re-apply factors (so controller gets base × multiplier)

    This keeps the remote's input field showing the BASE value while the controller
    gets the properly factored value.
    """
    try:
        new_val = float(new_state)
    except (ValueError, TypeError):
        _remote_log(f"Broker: ignoring non-numeric duration from remote: "
                    f"{suffix} = {new_state!r}")
        return

    # Find the controller entity this maps to
    maps = _build_remote_entity_maps()
    controller_eid = maps["r2c"].get(remote_eid)
    if not controller_eid:
        _remote_log(f"Broker: no controller mapping for remote duration {suffix}")
        return

    try:
        from routes.moisture import (
            _load_data as _load_moisture_data,
            _save_data as _save_moisture_data,
            apply_adjusted_durations,
        )
        from datetime import datetime, timezone

        mdata = _load_moisture_data()
        base_durations = mdata.get("base_durations", {})

        old_base = base_durations.get(controller_eid, {}).get("base_value")
        if old_base is not None and abs(float(old_base) - new_val) < 0.01:
            # Value unchanged — skip to avoid unnecessary writes
            return

        base_durations[controller_eid] = base_durations.get(controller_eid, {})
        base_durations[controller_eid]["entity_id"] = controller_eid
        base_durations[controller_eid]["base_value"] = new_val
        base_durations[controller_eid]["captured_at"] = datetime.now(timezone.utc).isoformat()
        mdata["base_durations"] = base_durations
        _save_moisture_data(mdata)

        _remote_log(f"Broker: remote duration {suffix} = {new_val} → "
                    f"updated base_durations[{controller_eid}]")

        # Always write the BASE value to the controller immediately.
        # Factors only apply to scheduled runs — if the user sets a duration
        # on the remote and hits "run", the zone must run for exactly that
        # duration (manual run).  The periodic factor re-application will
        # overwrite with the factored value before the next scheduled run.
        import ha_client
        await ha_client.call_service(
            "number", "set_value",
            {"entity_id": controller_eid, "value": new_val},
        )
        _remote_log(f"Broker: wrote base {new_val} to {controller_eid}")

    except Exception as e:
        _remote_log(f"Broker: error handling remote duration change: {e}")
        import traceback
        traceback.print_exc()


async def sync_base_durations_to_remote():
    """Push BASE durations (not factored) from the add-on to ALL remote devices.

    Called during full sync and after base durations are captured/changed.
    Reads base_durations from moisture.json and writes them to the corresponding
    remote duration entities on each connected remote.
    """
    import ha_client
    from config import get_config

    config = get_config()
    if not config.allowed_remote_entities_by_device:
        return

    try:
        from routes.moisture import _load_data as _load_moisture_data
        mdata = _load_moisture_data()
        base_durations = mdata.get("base_durations", {})
        if not base_durations:
            _remote_log("Broker: no base_durations to sync to remotes")
            return

        total_synced = 0
        for device_id in config.remote_device_ids:
            maps = _build_remote_entity_maps_for_device(device_id)
            synced = 0
            for controller_eid, dur_info in base_durations.items():
                base_val = dur_info.get("base_value")
                if base_val is None:
                    continue
                remote_eid = maps["c2r"].get(controller_eid)
                if not remote_eid:
                    continue
                await _mirror_entity_state(controller_eid, remote_eid, str(base_val))
                synced += 1
            total_synced += synced

        if total_synced > 0:
            _remote_log(f"Broker: synced base durations to {len(config.remote_device_ids)} remote(s) "
                        f"({total_synced} total writes)")
    except Exception as e:
        _remote_log(f"Broker: error syncing base durations to remotes: {e}")


# Guard to prevent multiple concurrent reconnect syncs.
# Starts True to block remote→controller mirroring until first startup sync completes.
_remote_reconnect_pending = True

_reconnect_sync_running = False  # prevents duplicate concurrent syncs
_sync_needed_entity: str | None = None  # auto-detected switch.xxx_sync_needed


def _find_sync_needed_entity_for_device(device_id: str) -> str | None:
    """Auto-detect the sync_needed switch for a specific remote device."""
    global _sync_needed_by_device
    cached = _sync_needed_by_device.get(device_id)
    if cached is not None:
        return cached if cached else None
    try:
        from config import get_config
        config = get_config()
        entities = config.allowed_remote_entities_by_device.get(device_id, [])
        for eid in entities:
            if eid.startswith("switch.") and eid.endswith("_sync_needed"):
                _sync_needed_by_device[device_id] = eid
                _remote_log(f"Broker: found sync_needed entity for {device_id[:12]}: {eid}")
                return eid
    except Exception:
        pass
    _sync_needed_by_device[device_id] = ""
    return None


def _find_sync_needed_entity() -> str | None:
    """Auto-detect any sync_needed switch (backward compat — returns first found)."""
    global _sync_needed_entity
    if _sync_needed_entity is not None:
        return _sync_needed_entity if _sync_needed_entity else None
    try:
        from config import get_config
        config = get_config()
        for eid in (config.allowed_remote_entities or []):
            if eid.startswith("switch.") and eid.endswith("_sync_needed"):
                _sync_needed_entity = eid
                return eid
    except Exception:
        pass
    _sync_needed_entity = ""
    return None


# --- Manual Stop flag (tells remote a zone was manually stopped) ---
_manual_stop_entity: str | None = None  # None=not searched, ""=not found


def _find_manual_stop_entity_for_device(device_id: str) -> str | None:
    """Auto-detect the manual_stop switch for a specific remote device."""
    global _manual_stop_by_device
    cached = _manual_stop_by_device.get(device_id)
    if cached is not None:
        return cached if cached else None
    try:
        from config import get_config
        config = get_config()
        entities = config.allowed_remote_entities_by_device.get(device_id, [])
        for eid in entities:
            if eid.startswith("switch.") and eid.endswith("_manual_stop"):
                _manual_stop_by_device[device_id] = eid
                _remote_log(f"Broker: found manual_stop entity for {device_id[:12]}: {eid}")
                return eid
    except Exception:
        pass
    _manual_stop_by_device[device_id] = ""
    return None


def _find_manual_stop_entity() -> str | None:
    """Auto-detect any manual_stop switch (backward compat — returns first found)."""
    global _manual_stop_entity
    if _manual_stop_entity is not None:
        return _manual_stop_entity if _manual_stop_entity else None
    try:
        from config import get_config
        config = get_config()
        for eid in (config.allowed_remote_entities or []):
            if eid.startswith("switch.") and eid.endswith("_manual_stop"):
                _manual_stop_entity = eid
                return eid
    except Exception:
        pass
    _manual_stop_entity = ""
    return None


async def signal_manual_stop():
    """Turn ON manual_stop switch on ALL connected remotes."""
    from config import get_config
    config = get_config()
    import ha_client
    for device_id in config.remote_device_ids:
        eid = _find_manual_stop_entity_for_device(device_id)
        if not eid:
            continue
        try:
            await ha_client.call_service("switch", "turn_on", {"entity_id": eid})
            _remote_log(f"Broker: signaled manual_stop ON → {eid}")
        except Exception as e:
            _remote_log(f"Broker: failed to signal manual_stop on {device_id[:12]}: {e}")


async def _handle_remote_reconnect(entity_id: str, remote_entities: set, device_id: str | None = None):
    """Remote device signaled sync needed — push ALL controller state to it.

    Triggered when:
    1. The sync_needed switch is detected ON (device just booted — ALWAYS_ON)
    2. A remote entity transitions from unavailable (backup detection)

    Per-device: only blocks and syncs the specific device that reconnected.
    Other remotes continue operating normally.
    """
    global _remote_reconnect_pending

    # Per-device guard
    if device_id:
        if _reconnect_sync_running_by_device.get(device_id, False):
            return
        _reconnect_sync_running_by_device[device_id] = True
    else:
        # Fallback: global guard (legacy)
        global _reconnect_sync_running
        if _reconnect_sync_running:
            return
        _reconnect_sync_running = True

    import asyncio
    import ha_client
    dev_label = f" (device {device_id[:12]})" if device_id else ""
    _remote_log(f"Broker: remote sync triggered{dev_label} — suppressing, "
               f"pushing controller state in 3s")

    await asyncio.sleep(3)
    try:
        await sync_all_remote_state()
    except Exception as e:
        _remote_log(f"Broker: reconnect sync FAILED{dev_label}: {e}")

    _remote_log(f"Broker: holding suppression 5s for remote{dev_label} to settle")
    await asyncio.sleep(5)

    # Turn OFF sync_needed for this specific device
    if device_id:
        sync_eid = _find_sync_needed_entity_for_device(device_id)
    else:
        sync_eid = _find_sync_needed_entity()
    if sync_eid:
        try:
            await ha_client.call_service("switch", "turn_off", {"entity_id": sync_eid})
            _remote_log(f"Broker: turned OFF {sync_eid}")
        except Exception as e:
            _remote_log(f"Broker: failed to turn off sync_needed: {e}")

    # Re-sync
    try:
        await sync_all_remote_state()
        _remote_log(f"Broker: second sync complete{dev_label} (post-settle)")
    except Exception as e:
        _remote_log(f"Broker: second sync FAILED{dev_label}: {e}")

    await asyncio.sleep(3)

    if device_id:
        _reconnect_sync_running_by_device[device_id] = False
        _remote_reconnect_pending_by_device[device_id] = False
        # Clear global flag only if ALL devices are done
        from config import get_config
        config = get_config()
        all_done = all(not _remote_reconnect_pending_by_device.get(d, True) for d in config.remote_device_ids)
        if all_done:
            _remote_reconnect_pending = False
    else:
        _reconnect_sync_running = False
        _remote_reconnect_pending = False

    _remote_log(f"Broker: remote→controller mirroring re-enabled{dev_label}")


async def _refresh_special_zones_on_mode_change():
    """Re-detect special zones and rebuild broker maps when a zone mode changes."""
    try:
        from routes.admin import get_special_zone_numbers, sync_remote_settings
        from config import get_config
        config = get_config()

        new_special = await get_special_zone_numbers(config)
        old_special = _special_zone_nums

        update_special_zone_nums(new_special)

        if new_special != old_special:
            _remote_log(f"Broker: zone mode change detected — special zones "
                        f"{old_special} -> {new_special}, rebuilding maps")
            invalidate_remote_maps()
            # Re-sync settings (zone count + pump flag) to remotes
            await sync_remote_settings()
    except Exception as e:
        print(f"[RUN_LOG] Special zone refresh on mode change failed: {e}")


async def _handle_controller_to_remote(entity_id: str, new_state: str):
    """A controller entity changed — mirror to ALL connected remote devices."""
    # Never push unavailable/unknown to remote
    if new_state in ("unavailable", "unknown"):
        return
    # Skip duration entities — the add-on manages these through base_durations.
    suffix = _extract_entity_suffix(entity_id)
    if _DURATION_SUFFIX_RE.match(suffix):
        return

    from config import get_config
    config = get_config()

    # Push to each connected remote device
    for device_id in config.remote_device_ids:
        if _remote_reconnect_pending_by_device.get(device_id, True):
            continue  # This remote is syncing, skip
        maps = _build_remote_entity_maps_for_device(device_id)
        # Check bidirectional map first
        remote_eid = maps["c2r"].get(entity_id)
        if remote_eid:
            await _mirror_entity_state(entity_id, remote_eid, new_state)
            continue
        # Check status (one-way) map
        remote_eid = maps["status_map"].get(entity_id)
        if remote_eid:
            await _mirror_entity_state(entity_id, remote_eid, new_state)


async def sync_all_remote_state():
    """Push ALL current controller state to ALL connected remote devices.

    Called on startup and when remote device is first connected.
    Reads current state of every mapped controller entity and pushes to each remote.
    """
    import ha_client
    from config import get_config

    config = get_config()
    if not config.allowed_remote_entities_by_device:
        return

    import asyncio
    total_synced = 0

    for device_id in config.remote_device_ids:
        maps = _build_remote_entity_maps_for_device(device_id)
        total_c2r = {**maps["c2r"], **maps["status_map"]}
        if not total_c2r:
            continue

        controller_eids = list(total_c2r.keys())
        sched_count = sum(1 for k in total_c2r if "start_time" in k.lower() or "schedule" in k.lower())
        _remote_log(f"Broker: syncing {len(total_c2r)} entities ({sched_count} schedule-related) "
                    f"to remote {device_id[:12]}")
        states = await ha_client.get_entities_by_ids(controller_eids)

        synced = 0
        skipped_durations = 0
        for entity_state in states:
            ctrl_eid = entity_state.get("entity_id", "")
            state_val = entity_state.get("state", "")
            if not ctrl_eid or not state_val or state_val in ("unavailable", "unknown"):
                continue
            remote_eid = total_c2r.get(ctrl_eid)
            if not remote_eid:
                continue
            suffix = _extract_entity_suffix(ctrl_eid)
            if _DURATION_SUFFIX_RE.match(suffix):
                skipped_durations += 1
                continue
            try:
                await _mirror_entity_state(ctrl_eid, remote_eid, state_val)
                synced += 1
                if synced % 10 == 0:
                    await asyncio.sleep(0.1)
            except Exception as e:
                _remote_log(f"Broker: sync FAILED for {ctrl_eid} → {device_id[:12]}: {e}")

        _remote_log(f"Broker: sync to {device_id[:12]} — {synced}/{len(total_c2r)} pushed "
                    f"({skipped_durations} durations skipped)")
        total_synced += synced

    _remote_log(f"Broker: full sync complete — {total_synced} total values pushed to "
                f"{len(config.remote_device_ids)} remote(s)")

    # Sync base durations separately (uses base values, not factored controller values)
    await sync_base_durations_to_remote()


async def get_broker_status() -> dict:
    """Return the broker's current entity mapping state for the debug UI.

    Provides a structured view of what the add-on (broker) understands about
    each device's entities and how they are paired, including sync state.
    """
    maps = _build_remote_entity_maps()
    controller_inv = maps.get("controller_inv", {})
    remote_inv = maps.get("remote_inv", {})
    c2r = maps.get("c2r", {})
    status_map = maps.get("status_map", {})

    # Build matched pairs list
    matched = []
    for ctrl_eid, remote_eid in c2r.items():
        func = _extract_entity_suffix(ctrl_eid)
        matched.append({"function": func, "controller": ctrl_eid,
                         "remote": remote_eid, "direction": "bidirectional"})
    for ctrl_eid, remote_eid in status_map.items():
        func = _extract_entity_suffix(ctrl_eid)
        matched.append({"function": func, "controller": ctrl_eid,
                         "remote": remote_eid, "direction": "one-way"})

    # Unmatched entities
    mapped_ctrl = set(c2r.keys()) | set(status_map.keys())
    mapped_remote = set(c2r.values()) | set(status_map.values())
    unmatched_ctrl = [{"entity_id": eid, "function": _extract_entity_suffix(eid)}
                      for (d, f), eid in controller_inv.items()
                      if eid not in mapped_ctrl]
    unmatched_remote = [{"entity_id": eid, "function": _extract_entity_suffix(eid)}
                        for (d, f), eid in remote_inv.items()
                        if eid not in mapped_remote]

    # Read live sync_needed state
    sync_eid = _find_sync_needed_entity()
    sync_state = None
    if sync_eid:
        try:
            import ha_client
            st = await ha_client.get_entity_state(sync_eid)
            sync_state = st.get("state") if st else None
        except Exception:
            pass

    # Per-device status
    per_device = {}
    for did in config.remote_device_ids:
        dev_sync_eid = _find_sync_needed_entity_for_device(did)
        dev_sync_state = None
        if dev_sync_eid:
            try:
                import ha_client
                dst = await ha_client.get_entity_state(dev_sync_eid)
                dev_sync_state = dst.get("state") if dst else None
            except Exception:
                pass
        per_device[did[:12]] = {
            "sync_needed_entity": dev_sync_eid,
            "sync_needed_state": dev_sync_state,
            "reconnect_pending": _remote_reconnect_pending_by_device.get(did, False),
            "sync_running": _reconnect_sync_running_by_device.get(did, False),
        }

    return {
        "matched": sorted(matched, key=lambda x: x["function"]),
        "unmatched_controller": sorted(unmatched_ctrl, key=lambda x: x["function"]),
        "unmatched_remote": sorted(unmatched_remote, key=lambda x: x["function"]),
        "total_controller": len(controller_inv),
        "total_remote": len(remote_inv),
        "sync_needed_entity": sync_eid,
        "sync_needed_state": sync_state,
        "reconnect_pending": _remote_reconnect_pending,
        "sync_running": _reconnect_sync_running,
        "per_device": per_device,
    }


def _get_probe_sensor_entities() -> set:
    """Get the set of moisture probe sensor entity IDs to watch.

    Watches moisture sensors for skip↔factor transitions (only if apply_factors is on),
    AND sleep_duration sensors for wake detection (always, if probes are enabled).
    """
    try:
        from routes.moisture import _load_data as _load_moisture_data
        data = _load_moisture_data()
        if not data.get("enabled"):
            return set()
        entities = set()
        apply_factors = data.get("apply_factors_to_schedule", False)
        for probe_id, probe in data.get("probes", {}).items():
            # Moisture sensors — only if apply_factors is enabled
            if apply_factors:
                for depth in ("shallow", "mid", "deep"):
                    sensor_eid = probe.get("sensors", {}).get(depth)
                    if sensor_eid:
                        entities.add(sensor_eid)
            # Sleep duration sensor — always watched for wake detection
            sleep_eid = probe.get("extra_sensors", {}).get("sleep_duration")
            if sleep_eid:
                entities.add(sleep_eid)
        return entities
    except Exception:
        return set()


def _get_schedule_entities() -> set:
    """Get schedule-related entity IDs that trigger timeline recalculation.

    Watches start times, run durations, zone enables, and schedule enable.
    Changes to any of these require recalculating the irrigation schedule
    timeline so probe wake times are updated.
    """
    try:
        from routes.moisture import _get_schedule_entity_ids
        return _get_schedule_entity_ids()
    except Exception:
        return set()


async def _handle_probe_sensor_change(entity_id: str, new_state: str, old_state: str):
    """Handle a moisture probe sensor state change.

    Checks if the reading change would cause a skip↔factor transition for
    any mapped zone. If so, triggers an immediate factor re-evaluation.
    Also handles probe wake detection for pending sleep duration writes.
    """
    import asyncio

    # Wake detection: unavailable → real value means probe woke up
    # Run as background task so it doesn't block transition detection
    if old_state in ("unavailable", "unknown") and new_state not in ("unavailable", "unknown"):
        try:
            from routes.moisture import on_probe_wake
            asyncio.create_task(on_probe_wake(entity_id))
        except Exception as e:
            print(f"[RUN_LOG] Probe wake hook error: {e}")

    # Skip↔factor transition detection — runs immediately, not blocked by wake handler
    try:
        from routes.moisture import check_skip_factor_transition
        needs_reeval = await check_skip_factor_transition(entity_id, new_state, old_state)
        if needs_reeval:
            print(f"[RUN_LOG] Probe sensor {entity_id} triggered skip↔factor transition — "
                  f"re-evaluating factors")
            from routes.moisture import apply_adjusted_durations
            result = await apply_adjusted_durations()
            applied = result.get("applied", 0)
            print(f"[RUN_LOG] Auto factor re-evaluation complete: {applied} zone(s) updated")
    except Exception as e:
        print(f"[RUN_LOG] Probe sensor transition check error: {e}")


_schedule_recalc_task: "asyncio.Task | None" = None
_schedule_recalc_pending = False


async def _debounced_timeline_recalc():
    """Wait 3 seconds then recalculate the timeline. Debounces rapid changes."""
    import asyncio
    global _schedule_recalc_pending
    await asyncio.sleep(3)
    _schedule_recalc_pending = False
    try:
        from routes.moisture import calculate_irrigation_timeline
        await calculate_irrigation_timeline()
    except Exception as e:
        print(f"[RUN_LOG] Schedule timeline recalculation error: {e}")


async def _handle_schedule_entity_change(entity_id: str, new_state: str, old_state: str):
    """Handle a schedule-related entity state change.

    Triggers recalculation of the irrigation schedule timeline so probe
    wake times are updated when start times, durations, or zone enables change.
    Debounced to 3 seconds to prevent rapid-fire recalculations when many
    entities change at once (e.g., after a restart or bulk update).
    """
    import asyncio
    global _schedule_recalc_task, _schedule_recalc_pending
    print(f"[RUN_LOG] Schedule entity changed: {entity_id} ({old_state} → {new_state})")
    if not _schedule_recalc_pending:
        _schedule_recalc_pending = True
        print(f"[RUN_LOG] Timeline recalculation scheduled (3s debounce)")
    if _schedule_recalc_task and not _schedule_recalc_task.done():
        _schedule_recalc_task.cancel()
    _schedule_recalc_task = asyncio.create_task(_debounced_timeline_recalc())


async def _watch_via_websocket(allowed_entities: set):
    """Subscribe to HA state_changed events via WebSocket for real-time logging.

    This gives sub-second event delivery — HA pushes state changes the instant
    they happen, so pump relay on/off timing is captured accurately relative
    to zone valve changes.

    Also monitors moisture probe sensors for skip↔factor transitions to
    automatically re-apply schedule adjustments.
    """
    global _remote_reconnect_pending
    import websockets
    from config import get_config

    config = get_config()
    token = config.supervisor_token
    ws_url = "ws://supervisor/core/websocket"

    # Build combined watch set: zone entities + probe + schedule + remote + controller-for-remote
    probe_entities = _get_probe_sensor_entities()
    schedule_entities = _get_schedule_entities()
    remote_entities = _get_remote_entities()
    controller_for_remote = _get_controller_entities_for_remote()
    all_watched = (allowed_entities | probe_entities | schedule_entities
                   | remote_entities | controller_for_remote)
    if probe_entities:
        print(f"[RUN_LOG] Also watching {len(probe_entities)} probe sensor entities "
              f"for skip↔factor transitions")
    if schedule_entities:
        print(f"[RUN_LOG] Also watching {len(schedule_entities)} schedule entities "
              f"for timeline recalculation")
    if remote_entities:
        print(f"[RUN_LOG] Broker watching {len(remote_entities)} remote entities "
              f"+ {len(controller_for_remote)} controller entities")
        _remote_log(f"Broker: watching {len(remote_entities)} remote + "
                    f"{len(controller_for_remote)} controller entities")

    extra_headers = {"Authorization": f"Bearer {token}"}

    async with websockets.connect(ws_url, additional_headers=extra_headers) as ws:
        # Step 1: auth_required
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_required":
            raise ConnectionError(f"Unexpected WS message: {msg}")

        # Step 2: Authenticate
        await ws.send(json.dumps({"type": "auth", "access_token": token}))
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_ok":
            raise PermissionError(f"WS auth failed: {msg}")

        # Step 3: Subscribe to state_changed events
        await ws.send(json.dumps({
            "id": 1,
            "type": "subscribe_events",
            "event_type": "state_changed",
        }))
        msg = json.loads(await ws.recv())
        if not msg.get("success"):
            raise RuntimeError(f"WS subscribe failed: {msg}")

        print(f"[RUN_LOG] WebSocket connected — real-time monitoring active "
              f"({len(allowed_entities)} zone + {len(probe_entities)} probe + "
              f"{len(schedule_entities)} schedule + {len(remote_entities)} remote entities)")

        # Step 3.5: On WS connect, check if sync_needed is ON per remote device
        if remote_entities:
            import ha_client as _hac
            for device_id in config.remote_device_ids:
                sync_eid = _find_sync_needed_entity_for_device(device_id)
                if not sync_eid:
                    continue
                try:
                    st = await _hac.get_entity_state(sync_eid)
                    if st and st.get("state") == "on":
                        _remote_reconnect_pending = True
                        _remote_reconnect_pending_by_device[device_id] = True
                        _remote_log(f"Broker: WS connected — sync_needed ON for {device_id[:12]}, triggering sync")
                        asyncio.create_task(
                            _handle_remote_reconnect("ws_connect", remote_entities, device_id=device_id)
                        )
                    elif _remote_reconnect_pending_by_device.get(device_id, False):
                        _remote_log(f"Broker: WS connected — sync_needed OFF for {device_id[:12]}, clearing block")
                        _remote_reconnect_pending_by_device[device_id] = False
                except Exception as e:
                    _remote_log(f"Broker: WS connect sync check failed for {device_id[:12]}: {e}")
            # Update global flag based on per-device state
            all_clear = all(
                not _remote_reconnect_pending_by_device.get(d, False)
                for d in config.remote_device_ids
            )
            if all_clear and _remote_reconnect_pending:
                _remote_reconnect_pending = False
                _remote_log("Broker: all remotes synced — global mirroring unblocked")

        # Step 4: Listen for events
        async for raw_msg in ws:
            try:
                msg = json.loads(raw_msg)
                if msg.get("type") != "event":
                    continue
                event_data = msg.get("event", {}).get("data", {})
                entity_id = event_data.get("entity_id", "")

                if entity_id not in all_watched:
                    continue

                # Skip mirrored events (prevents remote ↔ controller infinite loop)
                if entity_id in _remote_mirror_guard:
                    continue

                new_state_obj = event_data.get("new_state", {})
                old_state_obj = event_data.get("old_state", {})
                new_state = new_state_obj.get("state", "unknown") if new_state_obj else "unknown"
                old_state = old_state_obj.get("state", "unknown") if old_state_obj else "unknown"

                if new_state == old_state:
                    continue

                # Route to appropriate handler(s).
                # An entity may belong to multiple sets (e.g. a schedule day
                # switch is in both controller_for_remote AND schedule_entities
                # and needs both remote mirroring AND timeline recalculation).

                if entity_id in remote_entities:
                    # Determine which remote device this entity belongs to
                    _source_device = _get_entity_device_id(entity_id)

                    # --- Sync trigger 1: sync_needed switch turned ON (device booted) ---
                    if _source_device:
                        _dev_sync_eid = _find_sync_needed_entity_for_device(_source_device)
                    else:
                        _dev_sync_eid = _find_sync_needed_entity()

                    if _dev_sync_eid and entity_id == _dev_sync_eid and new_state == "on":
                        _remote_reconnect_pending = True
                        if _source_device:
                            _remote_reconnect_pending_by_device[_source_device] = True
                        _remote_log(f"Broker: sync_needed ON for {(_source_device or 'unknown')[:12]} — blocking mirroring")
                        import asyncio
                        asyncio.create_task(
                            _handle_remote_reconnect(entity_id, remote_entities, device_id=_source_device)
                        )
                        continue

                    # --- Sync trigger 2 (backup): entity went unavailable → available ---
                    if old_state == "unavailable" and new_state != "unavailable":
                        if _source_device and not _remote_reconnect_pending_by_device.get(_source_device, False):
                            _remote_reconnect_pending_by_device[_source_device] = True
                            _remote_reconnect_pending = True
                            _remote_log(f"Broker: remote {_source_device[:12]} back from unavailable — blocking mirroring")
                            import asyncio
                            asyncio.create_task(
                                _handle_remote_reconnect(entity_id, remote_entities, device_id=_source_device)
                            )
                        elif not _source_device and not _remote_reconnect_pending:
                            _remote_reconnect_pending = True
                            _remote_log("Broker: remote entity back from unavailable — blocking mirroring")
                            import asyncio
                            asyncio.create_task(
                                _handle_remote_reconnect(entity_id, remote_entities)
                            )
                        continue

                    # --- Skip the sync_needed entity itself (never mirror it) ---
                    if _dev_sync_eid and entity_id == _dev_sync_eid:
                        continue

                    # --- Never mirror unavailable/unknown to controller ---
                    if new_state in ("unavailable", "unknown"):
                        continue

                    # Remote entity changed → mirror to controller (+ other remotes)
                    import asyncio
                    asyncio.create_task(
                        _handle_remote_entity_change(entity_id, new_state, old_state)
                    )
                elif entity_id in allowed_entities:
                    # Zone entity on controller
                    attrs = new_state_obj.get("attributes", {}) if new_state_obj else {}
                    zone_name = attrs.get("friendly_name", entity_id)
                    await _handle_state_change(entity_id, new_state, old_state, zone_name)
                    # Also mirror controller zone → remote
                    if remote_entities:
                        import asyncio
                        asyncio.create_task(
                            _handle_controller_to_remote(entity_id, new_state)
                        )
                else:
                    # Non-zone controller entity — check remote mirroring
                    if entity_id in controller_for_remote:
                        import asyncio
                        asyncio.create_task(
                            _handle_controller_to_remote(entity_id, new_state)
                        )
                    # Detect zone mode changes → refresh special zone cache
                    if (entity_id.startswith("select.") and
                            "zone_" in entity_id and "_mode" in entity_id):
                        import asyncio
                        asyncio.create_task(
                            _refresh_special_zones_on_mode_change()
                        )

                # These handlers run IN ADDITION to the above (not exclusive)
                if entity_id in probe_entities:
                    await _handle_probe_sensor_change(entity_id, new_state, old_state)
                if entity_id in schedule_entities:
                    await _handle_schedule_entity_change(entity_id, new_state, old_state)

            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"[RUN_LOG] WebSocket event processing error: {e}")


async def _watch_via_polling(allowed_entities: set):
    """Fallback: poll zone states every 5 seconds if WebSocket is unavailable."""
    import asyncio
    import ha_client
    from config import get_config

    global _zone_states

    print("[RUN_LOG] Polling fallback active (5-second interval)")

    while True:
        try:
            config = get_config()
            if not config.allowed_zone_entities:
                await asyncio.sleep(30)
                continue

            entities = await ha_client.get_entities_by_ids(config.allowed_zone_entities)

            for entity in entities:
                entity_id = entity["entity_id"]
                current_state = entity.get("state", "unknown")
                prev_state = _zone_states.get(entity_id)

                if current_state != prev_state:
                    attrs = entity.get("attributes", {})
                    zone_name = attrs.get("friendly_name", entity_id)

                    if prev_state is None and current_state in ("on", "open"):
                        # First poll and zone is already on
                        log_zone_event(
                            entity_id=entity_id,
                            state=current_state,
                            source="schedule",
                            zone_name=zone_name,
                        )
                        print(f"[RUN_LOG] Initial on state detected: {entity_id} ({zone_name})")
                    elif prev_state is not None:
                        await _handle_state_change(entity_id, current_state,
                                                   prev_state, zone_name)

                    _zone_states[entity_id] = current_state

        except Exception as e:
            print(f"[RUN_LOG] Polling error: {e}")

        await asyncio.sleep(5)


async def watch_zone_states():
    """Background task: monitor zone state changes in real time.

    Uses HA WebSocket subscription for instant event delivery (sub-second).
    Falls back to 5-second polling if the WebSocket connection fails.

    This catches ALL zone state changes regardless of source:
      - API/dashboard starts and stops
      - ESPHome schedule-triggered runs
      - Firmware-controlled entities (pump relay, master valve)
      - HA automations
      - Manual toggles

    Also enforces system pause: if the system is paused and a zone turns on,
    it is immediately turned off.
    """
    global _remote_reconnect_pending
    import asyncio
    from config import get_config

    while True:
        try:
            config = get_config()
            if not config.allowed_zone_entities:
                await asyncio.sleep(30)
                continue

            allowed = set(config.allowed_zone_entities)

            # Filter out hidden zones beyond detected_zone_count
            max_zones = config.detected_zone_count if hasattr(config, "detected_zone_count") else 0
            if max_zones > 0:
                allowed = {
                    eid for eid in allowed
                    if _extract_zone_number(eid) <= max_zones
                }

            # Try WebSocket first (real-time, sub-second)
            try:
                await _watch_via_websocket(allowed)
            except Exception as ws_err:
                print(f"[RUN_LOG] WebSocket failed ({ws_err}), falling back to polling")
                # Block remote→controller on WS drop — will be cleared after sync check
                if config.allowed_remote_entities:
                    _remote_reconnect_pending = True
                    for did in config.remote_device_ids:
                        _remote_reconnect_pending_by_device[did] = True
                    _remote_log("Broker: WebSocket dropped — blocking all remotes")
                await _watch_via_polling(allowed)

        except Exception as e:
            print(f"[RUN_LOG] Zone watcher error: {e}")

        # Block remote→controller before reconnect attempt
        if config.allowed_remote_entities:
            _remote_reconnect_pending = True
            for did in config.remote_device_ids:
                _remote_reconnect_pending_by_device[did] = True
        # If we get here, the connection dropped — reconnect after a brief delay
        await asyncio.sleep(5)
