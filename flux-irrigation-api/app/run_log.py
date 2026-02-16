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

# --- Remote ↔ Controller entity mirroring ---
# Guard to prevent infinite loops: when we mirror a state change, the resulting
# state_changed event should be ignored.
_remote_mirror_guard: set = set()  # entity_ids currently being mirrored

# Cached entity maps (rebuilt when config changes)
_remote_maps_cache: dict = {}  # {"r2c": {}, "c2r": {}, "remote_all": set(), "controller_status": set()}
_remote_maps_logged: bool = False

# Suffix aliases — different firmware names that refer to the same function.
# Both sides are normalized to the canonical (value) name.
_SUFFIX_ALIASES = {
    "start_stop_resume": "start_stop",
    "main_start_stop": "start_stop",
    "progress_percent": "progress",
}

# Suffixes that are one-way: add-on → remote only (remote changes are ignored)
_ONE_WAY_SUFFIXES = {
    "zone_count",       # pushed via sync_remote_settings()
    "use_12_hour_format",  # pushed via sync_remote_settings()
}


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
            effective_source = source
            if already_logged and recent:
                effective_source = recent[0].get("source", source)
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
    # Schedule times
    for i in range(1, 5):
        if slug.endswith(f"_schedule_start_time_{i}") or slug.endswith(f"_start_time_{i}"):
            return f"schedule_start_time_{i}"
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


def invalidate_remote_maps():
    """Clear cached entity maps so they are rebuilt on next access.

    Call this when the remote device config changes (e.g. select_remote_device).
    """
    global _remote_maps_cache, _remote_maps_logged
    _remote_maps_cache = {}
    _remote_maps_logged = False


def _build_remote_entity_maps() -> dict:
    """Build bidirectional entity mapping between controller and remote.

    Maps entities by their functional suffix — both devices share the same
    suffix patterns (zone_1, schedule_monday, zone_1_duration, etc.).

    Returns dict with:
      r2c: remote_entity → controller_entity (for user actions on remote)
      c2r: controller_entity → remote_entity (for mirroring state to remote)
      remote_all: set of ALL remote entity IDs to watch
      controller_watched: set of controller entity IDs that have a remote counterpart
      status_map: controller_sensor → remote_text (one-way: controller→remote)
    """
    global _remote_maps_cache, _remote_maps_logged
    # Return cached maps if already built (rebuild via invalidate_remote_maps())
    if _remote_maps_cache:
        return _remote_maps_cache

    from config import get_config
    config = get_config()

    if not config.allowed_remote_entities:
        _remote_maps_cache = {"r2c": {}, "c2r": {}, "remote_all": set(),
                              "controller_watched": set(), "status_map": {}}
        return _remote_maps_cache

    # Index remote entities by (domain, suffix)
    remote_by_suffix = {}  # suffix → entity_id
    for eid in config.allowed_remote_entities:
        domain = eid.split(".")[0] if "." in eid else ""
        suffix = _extract_entity_suffix(eid)
        remote_by_suffix[(domain, suffix)] = eid
        # Also store without domain for cross-domain matching (text_sensor→text)
        remote_by_suffix[("*", suffix)] = eid

    # Index controller entities by suffix
    # Combine all controller entity lists
    all_controller = set()
    for eid in (config.allowed_zone_entities or []):
        all_controller.add(eid)
    for eid in (config.allowed_control_entities or []):
        all_controller.add(eid)
    for eid in (config.allowed_sensor_entities or []):
        all_controller.add(eid)

    # Debug: log schedule-related suffixes from both sides
    if not _remote_maps_logged:
        _sched_remote = {s: e for (d, s), e in remote_by_suffix.items()
                         if d != "*" and "schedule" in s}
        _sched_ctrl = {_extract_entity_suffix(e): e for e in all_controller
                       if "schedule" in e.lower()}
        if _sched_remote or _sched_ctrl:
            print(f"[REMOTE] Schedule suffixes — remote: {_sched_remote}")
            print(f"[REMOTE] Schedule suffixes — controller: {_sched_ctrl}")

    r2c = {}
    c2r = {}
    status_map = {}  # controller text_sensor → remote text entity

    for ctrl_eid in all_controller:
        ctrl_domain = ctrl_eid.split(".")[0] if "." in ctrl_eid else ""
        suffix = _extract_entity_suffix(ctrl_eid)

        # Try exact domain match first, then cross-domain
        remote_eid = remote_by_suffix.get((ctrl_domain, suffix))

        # Cross-domain: controller text_sensor.* → remote text.* (status entities)
        if not remote_eid and ctrl_domain == "text_sensor":
            remote_eid = remote_by_suffix.get(("text", suffix))
            if remote_eid:
                # Status entities are one-way: controller → remote only
                status_map[ctrl_eid] = remote_eid
                continue

        # Cross-domain: controller number.*_zone_N_duration → remote number.*_zone_N_duration
        # (suffix already normalized to zone_N_duration)
        if not remote_eid:
            remote_eid = remote_by_suffix.get(("*", suffix))
            # Make sure domains are compatible for bidirectional sync
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
    }

    # Log mapping summary on first build only
    if not _remote_maps_logged and (r2c or status_map):
        _remote_maps_logged = True
        print(f"[REMOTE] Entity maps built: {len(r2c)} bidirectional, {len(status_map)} status (one-way)")
        for r_eid, c_eid in sorted(r2c.items()):
            suffix = _extract_entity_suffix(r_eid)
            print(f"[REMOTE]   ↔ {suffix}: {c_eid.split('.')[0]}.* ↔ {r_eid.split('.')[0]}.*")
        for c_eid, r_eid in sorted(status_map.items()):
            suffix = _extract_entity_suffix(c_eid)
            print(f"[REMOTE]   → {suffix}: {c_eid.split('.')[0]}.* → {r_eid.split('.')[0]}.*")
        # Log unmapped remote entities
        mapped_remote = set(r2c.keys()) | set(status_map.values())
        unmapped = remote_all - mapped_remote
        if unmapped:
            print(f"[REMOTE]   Unmapped remote entities ({len(unmapped)}):")
            for eid in sorted(unmapped):
                print(f"[REMOTE]     - {eid} (suffix: {_extract_entity_suffix(eid)})")

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
                await ha_client.call_service("text", "set_value",
                                             {"entity_id": target_eid, "value": str(new_state)})
            # text_sensor can't be written to — skip
        elif target_domain == "select":
            await ha_client.call_service("select", "select_option",
                                         {"entity_id": target_eid, "option": str(new_state)})
        elif target_domain == "button":
            await ha_client.call_service("button", "press", {"entity_id": target_eid})
        else:
            return  # Unknown domain

        suffix = _extract_entity_suffix(source_eid)
        print(f"[REMOTE] Mirrored {suffix}: {new_state} ({source_eid} → {target_eid})")
    except Exception as e:
        print(f"[REMOTE] Mirror failed {source_eid} → {target_eid}: {e}")
    finally:
        import asyncio
        async def _clear():
            await asyncio.sleep(2)
            _remote_mirror_guard.discard(target_eid)
        asyncio.create_task(_clear())


async def _handle_remote_entity_change(entity_id: str, new_state: str, old_state: str):
    """A remote entity changed — mirror to the corresponding controller entity.

    One-way entities (zone_count, use_12_hour_format) are skipped — the remote
    cannot update those on the controller.
    """
    # Skip one-way entities (add-on → remote only)
    suffix = _extract_entity_suffix(entity_id)
    if suffix in _ONE_WAY_SUFFIXES:
        return
    maps = _build_remote_entity_maps()
    controller_eid = maps["r2c"].get(entity_id)
    if not controller_eid:
        return
    await _mirror_entity_state(entity_id, controller_eid, new_state)


async def _handle_controller_to_remote(entity_id: str, new_state: str):
    """A controller entity changed — mirror to the corresponding remote entity."""
    maps = _build_remote_entity_maps()
    # Check bidirectional map first
    remote_eid = maps["c2r"].get(entity_id)
    if remote_eid:
        await _mirror_entity_state(entity_id, remote_eid, new_state)
        return
    # Check status (one-way) map
    remote_eid = maps["status_map"].get(entity_id)
    if remote_eid:
        await _mirror_entity_state(entity_id, remote_eid, new_state)


async def sync_all_remote_state():
    """Push ALL current controller state to the remote device.

    Called on startup and when remote device is first connected.
    Reads current state of every mapped controller entity and pushes to remote.
    """
    import ha_client
    from config import get_config

    config = get_config()
    if not config.allowed_remote_entities:
        return

    maps = _build_remote_entity_maps()
    total_c2r = {**maps["c2r"], **maps["status_map"]}
    if not total_c2r:
        print("[REMOTE] No entity mappings found — cannot sync")
        return

    # Fetch current states of all controller entities that have remote counterparts
    controller_eids = list(total_c2r.keys())
    states = await ha_client.get_entities_by_ids(controller_eids)

    import asyncio
    synced = 0
    for entity_state in states:
        ctrl_eid = entity_state.get("entity_id", "")
        state_val = entity_state.get("state", "")
        if not ctrl_eid or not state_val or state_val in ("unavailable", "unknown"):
            continue
        remote_eid = total_c2r.get(ctrl_eid)
        if not remote_eid:
            continue
        try:
            await _mirror_entity_state(ctrl_eid, remote_eid, state_val)
            synced += 1
            # Small delay to avoid overwhelming the ESPHome device
            if synced % 10 == 0:
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[REMOTE] Initial sync failed for {ctrl_eid}: {e}")

    print(f"[REMOTE] Full state sync complete: {synced}/{len(total_c2r)} entities pushed to remote")


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
        print(f"[RUN_LOG] Also watching {len(remote_entities)} remote entities "
              f"+ {len(controller_for_remote)} controller entities for remote mirroring")

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
                    # Remote entity changed → mirror to controller
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
                await _watch_via_polling(allowed)

        except Exception as e:
            print(f"[RUN_LOG] Zone watcher error: {e}")

        # If we get here, the connection dropped — reconnect after a brief delay
        await asyncio.sleep(5)
