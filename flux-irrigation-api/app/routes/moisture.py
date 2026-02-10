"""
Flux Open Home - Gophr Moisture Probe Integration
===================================================
Auto-detects Gophr moisture probes from HA sensors, provides many-to-many
probe-to-zone mapping, and produces a moisture multiplier that combines with
the weather multiplier to adjust zone run durations.

Key concepts:
  - Probes are discovered by scanning all HA sensor entities for keywords
    (gophr, moisture, soil)
  - Each probe has up to 3 depth sensors: shallow, mid, deep
  - Probes can be mapped to multiple zones; zones can have multiple probes
  - The moisture multiplier is calculated before irrigation (pre-run only)
  - Combined multiplier = weather_multiplier × moisture_multiplier
  - For ESPHome scheduled runs: temporarily writes adjusted durations to
    number.*_run_duration HA entities, then restores originals after runs finish
  - For API/dashboard timed runs: adjusts the duration passed to _timed_shutoff()
"""

import asyncio
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from config import get_config
import ha_client
from config_changelog import log_change, get_actor


router = APIRouter(prefix="/admin/api/homeowner/moisture", tags=["Moisture Probes"])

MOISTURE_FILE = "/data/moisture_probes.json"
SENSOR_CACHE_FILE = "/data/moisture_sensor_cache.json"
SCHEDULE_TIMELINE_FILE = "/data/irrigation_schedule.json"

# --- Probe-Aware Irrigation Constants ---
PREP_BUFFER_MINUTES = 20     # How far ahead of the mapped zone start to reprogram sleep
TARGET_WAKE_BEFORE_MINUTES = 10  # Target: probe wakes this many minutes before zone starts

# Keywords used to auto-discover moisture probe sensor entities
PROBE_KEYWORDS = ["gophr", "moisture", "soil"]

# --- Last-Known-Good Sensor Cache ---
# Gophr devices sleep between readings.  While asleep HA marks entities as
# "unavailable".  Without a cache the algorithm would fall back to 1.0x
# (neutral), effectively erasing the moisture adjustment every sleep cycle.
#
# The cache stores the last VALID numeric reading for every sensor entity and
# is used as a transparent fallback when HA returns "unavailable" / "unknown".
# It persists to disk so it survives add-on restarts.

_sensor_cache: dict[str, dict] = {}  # in-memory: {entity_id: {state, last_updated, ...}}
_sensor_cache_loaded = False

# --- Probe Awake Status Cache ---
# Gophr probes expose a status LED entity (light.*_status_led).
# When the light is ON the device is awake; when OFF it is sleeping.
# This is a simple HA state read — no writes required.
_probe_awake_cache: dict[str, bool] = {}  # probe_id -> True=awake, False=sleeping


def _load_sensor_cache():
    """Load the sensor value cache from disk (once)."""
    global _sensor_cache, _sensor_cache_loaded
    if _sensor_cache_loaded:
        return
    _sensor_cache_loaded = True
    if os.path.exists(SENSOR_CACHE_FILE):
        try:
            with open(SENSOR_CACHE_FILE, "r") as f:
                _sensor_cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            _sensor_cache = {}


def _save_sensor_cache():
    """Persist the sensor value cache to disk."""
    try:
        os.makedirs(os.path.dirname(SENSOR_CACHE_FILE), exist_ok=True)
        with open(SENSOR_CACHE_FILE, "w") as f:
            json.dump(_sensor_cache, f, indent=2)
    except IOError:
        pass


async def _find_status_led(probe_id: str, probe: dict) -> Optional[str]:
    """Find the status LED entity for a probe by scanning the entity registry.

    If the status_led key is missing from extra_sensors (e.g. probe was set up
    before the feature was added), this function searches for a light.*status_led
    entity belonging to the same device_id and persists the result.
    """
    device_id = probe.get("device_id")
    if not device_id:
        return None

    try:
        entity_registry = await ha_client.get_entity_registry()
        for entity in entity_registry:
            if entity.get("device_id") != device_id:
                continue
            if entity.get("disabled_by"):
                continue
            eid = entity.get("entity_id", "")
            if eid.startswith("light.") and "status_led" in eid.lower():
                # Found it — persist so we don't scan every time
                data = _load_data()
                p = data.get("probes", {}).get(probe_id)
                if p:
                    extra = p.get("extra_sensors") or {}
                    extra["status_led"] = eid
                    p["extra_sensors"] = extra
                    _save_data(data)
                    print(f"[MOISTURE] Auto-discovered status_led for {probe_id}: {eid}")
                return eid
    except Exception as e:
        print(f"[MOISTURE] Error scanning for status_led: {e}")
    return None


async def _check_probe_awake(probe_id: str) -> bool:
    """Determine if a Gophr probe is awake by reading its status LED entity.

    The Gophr device exposes a light.*_status_led entity.
    ON = awake, OFF = sleeping.  Result is cached in _probe_awake_cache.

    If the status_led entity isn't in extra_sensors yet, auto-discovers it
    by scanning the entity registry for the probe's device_id.
    """
    data = _load_data()
    probe = data.get("probes", {}).get(probe_id)
    if not probe:
        return False

    status_led_eid = (probe.get("extra_sensors") or {}).get("status_led")
    if not status_led_eid:
        # Try to auto-discover from entity registry
        status_led_eid = await _find_status_led(probe_id, probe)
        if not status_led_eid:
            # No status LED entity found — assume awake (can't determine)
            return True

    state = await ha_client.get_entity_state(status_led_eid)
    if not state:
        # Couldn't read state — use cached value or assume sleeping
        return _probe_awake_cache.get(probe_id, False)

    raw = state.get("state", "").lower()
    is_awake = raw == "on"
    _probe_awake_cache[probe_id] = is_awake
    return is_awake


_awake_poller_task: asyncio.Task | None = None
_AWAKE_POLL_INTERVAL = 5  # seconds


async def _awake_poll_loop():
    """Background task that polls all configured probes every 5 seconds.

    Reads each probe's status LED entity (light.*_status_led) to determine
    awake/sleeping state.  Detects wake transitions and fires pending writes.

    Also handles probe-aware irrigation scheduling:
    1. Time-based check: when we reach the prep trigger time, reprogram the
       probe's sleep duration so it wakes ~10 min before the zone starts
    2. Wake transition check: when a prepped probe wakes up, check moisture
       and either skip the zone (saturated) or disable sleep (keep awake)
    """
    while True:
        try:
            await asyncio.sleep(_AWAKE_POLL_INTERVAL)
            data = _load_data()
            if not data.get("enabled"):
                continue
            probes = data.get("probes", {})

            # Load schedule timeline for prep logic
            timeline = _load_schedule_timeline()
            probe_prep = timeline.get("probe_prep", {}) if timeline else {}
            now = datetime.now()
            current_minutes = now.hour * 60 + now.minute

            for probe_id, probe in probes.items():
                was_awake = _probe_awake_cache.get(probe_id, False)
                now_awake = await _check_probe_awake(probe_id)

                # Log state transitions (not every poll — only changes)
                if now_awake != was_awake:
                    display = probe.get("display_name", probe_id)
                    transition = "SLEEPING → AWAKE" if now_awake else "AWAKE → SLEEPING"
                    print(f"[MOISTURE] Probe {display} state change: {transition}")

                # --- Schedule-aware prep: time-based trigger ---
                prep = probe_prep.get(probe_id)
                if prep and prep.get("state") == "idle":
                    for entry in prep.get("prep_entries", []):
                        trigger_min = entry.get("prep_trigger_minutes", -1)
                        zone_start_min = entry.get("zone_start_minutes", -1)
                        # Check if we've reached the prep trigger time
                        # Use a 2-minute window to avoid missing the trigger
                        time_diff = (current_minutes - trigger_min) % 1440
                        if 0 <= time_diff <= 2:
                            asyncio.create_task(
                                _prep_probe_for_schedule(
                                    probe_id, probe, entry, prep, timeline
                                )
                            )
                            break  # Only handle one prep per cycle

                # --- Wake transition detection ---
                if now_awake and not was_awake:
                    print(f"[MOISTURE] Awake poll detected wake: {probe_id}")
                    asyncio.create_task(on_probe_wake(probe_id))

                    # Schedule-aware: check if this is a prepped wake
                    if prep and prep.get("state") == "prep_pending":
                        asyncio.create_task(
                            _handle_prepped_wake(probe_id, probe, prep, timeline)
                        )

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[MOISTURE] Awake poll error: {e}")
            await asyncio.sleep(10)


async def _prep_probe_for_schedule(
    probe_id: str, probe: dict, entry: dict, prep: dict, timeline: dict
):
    """Reprogram a probe's sleep duration so it wakes before a mapped zone.

    Called when the current time reaches the prep trigger time.
    Sets the sleep duration so the probe will wake ~10 minutes before
    the mapped zone starts.
    """
    zone_start_min = entry["zone_start_minutes"]
    target_wake = entry["target_wake_minutes"]
    zone_eid = entry["zone_entity_id"]
    zone_num = entry["zone_num"]
    sched_time = entry["schedule_start_time"]

    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute

    # Calculate how long probe should sleep to wake at target time
    sleep_needed = (target_wake - current_minutes) % 1440
    if sleep_needed <= 0:
        sleep_needed = 1  # Wake ASAP

    display_name = probe.get("display_name", probe_id)

    # Save original sleep duration before we change it
    if probe_id not in _original_sleep_durations:
        extra = probe.get("extra_sensors") or {}
        sleep_sensor_eid = extra.get("sleep_duration")
        if sleep_sensor_eid:
            try:
                states = await ha_client.get_entities_by_ids([sleep_sensor_eid])
                if states:
                    raw = states[0].get("state", "0")
                    if raw not in ("unavailable", "unknown"):
                        orig = float(raw)
                        _original_sleep_durations[probe_id] = orig
                        print(f"[MOISTURE] Saved original sleep duration for {display_name}: {orig} min")
            except (ValueError, TypeError):
                pass

    # Check if probe is currently awake — if so, just disable sleep immediately
    is_awake = _probe_awake_cache.get(probe_id, False)
    if is_awake:
        print(f"[MOISTURE] Schedule prep: {display_name} is already awake — "
              f"disabling sleep for {sched_time} schedule (zone {zone_num})")
        # Don't disable sleep yet — let the wake check logic handle moisture check
        # Just mark as prep_pending so when the schedule runs, we're ready
    else:
        # Reprogram sleep duration
        success = await _set_probe_sleep_duration(probe_id, sleep_needed)
        if success:
            print(f"[MOISTURE] Schedule prep: reprogrammed {display_name} sleep to "
                  f"{sleep_needed} min — will wake ~{TARGET_WAKE_BEFORE_MINUTES} min "
                  f"before zone {zone_num} ({sched_time} schedule)")
        else:
            print(f"[MOISTURE] Schedule prep: FAILED to reprogram {display_name} sleep "
                  f"— probe may not wake in time for zone {zone_num}")

    # Update prep state
    prep["state"] = "prep_pending"
    prep["active_schedule_start_time"] = sched_time
    prep["active_zone_entity_id"] = zone_eid
    prep["active_zone_num"] = zone_num
    _save_schedule_timeline(timeline)


async def _handle_prepped_wake(
    probe_id: str, probe: dict, prep: dict, timeline: dict
):
    """Handle wake of a probe that was prepped for an upcoming zone.

    The probe just woke up and we're expecting a mapped zone to start soon.
    Wait a few seconds for the reading, then check moisture:
    - Saturated → skip the zone (disable enable_zone switch)
    - Not saturated → disable sleep (keep probe awake for the run)
    """
    display_name = probe.get("display_name", probe_id)
    zone_eid = prep.get("active_zone_entity_id")
    zone_num = prep.get("active_zone_num", 0)
    sched_time = prep.get("active_schedule_start_time", "?")

    if not zone_eid:
        prep["state"] = "idle"
        _save_schedule_timeline(timeline)
        return

    # Wait for the probe to take its reading (it reads on wake)
    print(f"[MOISTURE] Schedule wake: {display_name} woke for zone {zone_num} "
          f"({sched_time}) — waiting 8s for sensor reading...")
    await asyncio.sleep(8)

    # Reload fresh data and sensor states
    data = _load_data()
    fresh_probe = data.get("probes", {}).get(probe_id)
    if not fresh_probe:
        prep["state"] = "idle"
        _save_schedule_timeline(timeline)
        return

    # Get sensor states and check moisture
    sensor_states = await _get_probe_sensor_states({probe_id: fresh_probe})
    zone_result = calculate_zone_moisture_multiplier(zone_eid, data, sensor_states)

    if zone_result.get("skip"):
        # SATURATED — skip the zone by disabling its enable_zone switch
        config = get_config()
        enable_sw = _find_enable_zone_switch(zone_num, config)
        if enable_sw:
            success = await ha_client.call_service("switch", "turn_off", {
                "entity_id": enable_sw,
            })
            if success:
                # Track skipped zone for re-enable later
                prep.setdefault("skipped_zones", []).append({
                    "zone_num": zone_num,
                    "zone_entity_id": zone_eid,
                    "enable_entity": enable_sw,
                })
                print(f"[MOISTURE] Schedule skip: zone {zone_num} saturated "
                      f"(mult={zone_result.get('multiplier')}) — disabled {enable_sw}")
            else:
                print(f"[MOISTURE] Schedule skip: FAILED to disable {enable_sw} for zone {zone_num}")
        else:
            print(f"[MOISTURE] Schedule skip: zone {zone_num} saturated but "
                  f"no enable_zone switch found")

        # Log moisture skip event to run history
        try:
            import run_log
            # Extract mid sensor reading from probe_details
            mid_pct = None
            probe_details = zone_result.get("probe_details", [])
            for pd in probe_details:
                dr = pd.get("depth_readings", {})
                mid_info = dr.get("mid", {})
                if mid_info.get("value") is not None:
                    mid_pct = round(mid_info["value"], 1)
                    break
            probe_num_match = re.search(r'(\d+)', probe_id)
            probe_num = probe_num_match.group(1) if probe_num_match else probe_id
            mult = zone_result.get("multiplier", 0)
            mid_text = f" (Mid: {mid_pct}%)" if mid_pct is not None else ""
            run_log.log_probe_event(
                probe_id=probe_id,
                event_type="moisture_skip",
                display_name=display_name,
                zone_entity_id=zone_eid,
                zone_name=f"Zone {zone_num}",
                details={
                    "mid_sensor_pct": mid_pct,
                    "moisture_multiplier": mult,
                    "reason": zone_result.get("reason", "saturated"),
                    "probe_num": probe_num,
                    "skip_text": f"Probe {probe_num} skipped Zone {zone_num}{mid_text}",
                },
            )
        except Exception as e:
            print(f"[MOISTURE] Failed to log moisture skip event: {e}")

        # Check if there's a next mapped zone in this schedule to prep for
        prep["state"] = "checking_next"
        await _prep_next_mapped_zone(probe_id, probe, zone_eid, prep, timeline)
    else:
        # NOT saturated — disable sleep to keep probe awake for the run
        await set_probe_sleep_disabled(probe_id, True)
        prep["state"] = "monitoring"
        mult = zone_result.get("multiplier", 1.0)
        print(f"[MOISTURE] Schedule wake: zone {zone_num} NOT saturated "
              f"(mult={mult:.2f}) — probe {display_name} sleep disabled for run")
        _save_schedule_timeline(timeline)


async def _prep_next_mapped_zone(
    probe_id: str, probe: dict, current_zone_eid: str,
    prep: dict, timeline: dict
):
    """After skipping a zone, check if there's another mapped zone to prepare for.

    Looks forward in the schedule to find the next zone mapped to this probe.
    If found, calculates the gap and either keeps the probe awake (short gap)
    or programs a sleep duration to wake before the next mapped zone.
    """
    data = _load_data()
    mapped_zones = set((data.get("probes", {}).get(probe_id) or {}).get("zone_mappings", []))
    if not mapped_zones:
        prep["state"] = "idle"
        _save_schedule_timeline(timeline)
        return

    # Find the active schedule to look up zone order
    sched_time = prep.get("active_schedule_start_time")
    active_sched = None
    for sched in timeline.get("schedules", []):
        if sched["start_time"] == sched_time:
            active_sched = sched
            break

    if not active_sched:
        prep["state"] = "idle"
        _save_schedule_timeline(timeline)
        return

    # Find current zone's position and look forward
    zones = active_sched["zones"]
    current_idx = None
    for i, z in enumerate(zones):
        if z["zone_entity_id"] == current_zone_eid:
            current_idx = i
            break

    if current_idx is None:
        prep["state"] = "idle"
        _save_schedule_timeline(timeline)
        return

    # Look forward for next mapped zone
    next_mapped = None
    gap_minutes = 0.0
    for i in range(current_idx + 1, len(zones)):
        gap_minutes += zones[i]["duration_minutes"]
        if zones[i]["zone_entity_id"] in mapped_zones:
            next_mapped = zones[i]
            # Gap is cumulative duration of zones BETWEEN current and next mapped
            # minus the next mapped zone's own duration (we just added it)
            gap_minutes -= zones[i]["duration_minutes"]
            break

    if not next_mapped:
        # No more mapped zones — finish up
        await _finish_probe_prep_cycle(probe_id, prep, timeline)
        return

    # There IS a next mapped zone
    next_zone_eid = next_mapped["zone_entity_id"]
    next_zone_num = next_mapped["zone_num"]

    if gap_minutes < 2:
        # Gap is very short — keep probe awake
        await set_probe_sleep_disabled(probe_id, True)
        prep["state"] = "monitoring"
        prep["active_zone_entity_id"] = next_zone_eid
        prep["active_zone_num"] = next_zone_num
        print(f"[MOISTURE] Next mapped zone {next_zone_num} in {gap_minutes:.1f} min — "
              f"keeping {probe_id} awake")
    else:
        # Program sleep to wake ~10 min before next mapped zone
        sleep_mins = max(1, gap_minutes - TARGET_WAKE_BEFORE_MINUTES)
        await _set_probe_sleep_duration(probe_id, sleep_mins)
        await set_probe_sleep_disabled(probe_id, False)
        prep["state"] = "prep_pending"
        prep["active_zone_entity_id"] = next_zone_eid
        prep["active_zone_num"] = next_zone_num
        print(f"[MOISTURE] Next mapped zone {next_zone_num} in {gap_minutes:.1f} min — "
              f"sleeping {probe_id} for {sleep_mins:.1f} min")

    _save_schedule_timeline(timeline)


async def _finish_probe_prep_cycle(probe_id: str, prep: dict, timeline: dict):
    """Finish the probe prep cycle: restore original sleep, re-enable skipped zones."""
    display_name = prep.get("display_name", probe_id)

    # Restore original sleep duration
    original = _original_sleep_durations.pop(probe_id, None)
    if original is not None:
        await _set_probe_sleep_duration(probe_id, original)
        print(f"[MOISTURE] Restored original sleep duration for {probe_id}: {original} min")

    # Re-enable sleep
    await set_probe_sleep_disabled(probe_id, False)

    # Re-enable any skipped zones
    for skipped in prep.get("skipped_zones", []):
        enable_entity = skipped.get("enable_entity")
        zone_num = skipped.get("zone_num")
        if enable_entity:
            success = await ha_client.call_service("switch", "turn_on", {
                "entity_id": enable_entity,
            })
            if success:
                print(f"[MOISTURE] Re-enabled zone {zone_num} ({enable_entity}) after schedule cycle")
            else:
                print(f"[MOISTURE] FAILED to re-enable zone {zone_num} ({enable_entity})")

    # Reset prep state
    prep["state"] = "idle"
    prep["skipped_zones"] = []
    prep["active_schedule_start_time"] = None
    prep["active_zone_entity_id"] = None
    prep["active_zone_num"] = None
    _save_schedule_timeline(timeline)
    print(f"[MOISTURE] Schedule prep cycle complete for {probe_id}")


def start_awake_poller():
    """Start the background awake-status polling task."""
    global _awake_poller_task
    if _awake_poller_task and not _awake_poller_task.done():
        return  # Already running
    _awake_poller_task = asyncio.create_task(_awake_poll_loop())
    print("[MOISTURE] Awake poller started (interval: 5s)")


def stop_awake_poller():
    """Stop the background awake-status polling task."""
    global _awake_poller_task
    if _awake_poller_task and not _awake_poller_task.done():
        _awake_poller_task.cancel()
        _awake_poller_task = None
        print("[MOISTURE] Awake poller stopped")


# --- Schedule Timeline ---
# Tracks when each zone will run per schedule, which zones have probes,
# and the prep timing so probes can be woken before their mapped zones.

def _minutes_to_hhmm(minutes: float) -> str:
    """Convert minutes-since-midnight to HH:MM string (handles >24h wrap)."""
    m = int(minutes) % 1440
    return f"{m // 60:02d}:{m % 60:02d}"


def _parse_time_to_minutes(val: str) -> int:
    """Parse a time string to minutes-since-midnight.

    Handles multiple formats:
      - 24-hour: "5:00", "17:30", "05:00"
      - 12-hour with AM/PM: "5:00 AM", "10:00 AM", "1:00 PM", "9:00 PM"
      - 12-hour lowercase: "5:00 am", "1:00 pm"

    Returns minutes since midnight (0-1439).
    Raises ValueError if the string can't be parsed.
    """
    cleaned = val.strip()

    # Check for AM/PM suffix
    am_pm = ""
    upper = cleaned.upper()
    if upper.endswith("AM") or upper.endswith("PM"):
        am_pm = upper[-2:]
        cleaned = cleaned[:-2].strip()
    elif upper.endswith("A") or upper.endswith("P"):
        # Handle "5:00A" or "5:00P" edge case
        am_pm = upper[-1] + "M"
        cleaned = cleaned[:-1].strip()

    parts = cleaned.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0

    if am_pm:
        # 12-hour format
        if am_pm == "AM":
            if hour == 12:
                hour = 0  # 12:00 AM = midnight = 0:00
        elif am_pm == "PM":
            if hour != 12:
                hour += 12  # 1:00 PM = 13:00, 12:00 PM stays 12:00

    return hour * 60 + minute


def _load_schedule_timeline() -> dict:
    """Load the calculated irrigation schedule timeline from disk."""
    if os.path.exists(SCHEDULE_TIMELINE_FILE):
        try:
            with open(SCHEDULE_TIMELINE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_schedule_timeline(timeline: dict):
    """Persist the schedule timeline to disk."""
    try:
        with open(SCHEDULE_TIMELINE_FILE, "w") as f:
            json.dump(timeline, f, indent=2)
    except IOError as e:
        print(f"[MOISTURE] Error saving schedule timeline: {e}")


async def calculate_irrigation_timeline() -> dict:
    """Build the irrigation schedule timeline with probe prep timing.

    Reads schedule start times and zone durations from HA entities,
    computes when each zone will run, cross-references with probe
    zone_mappings, and calculates the prep trigger time for each probe.

    The prep trigger time = mapped_zone_start - (current_sleep_duration + PREP_BUFFER_MINUTES)
    At that moment, we reprogram the probe's sleep duration so it wakes
    ~TARGET_WAKE_BEFORE_MINUTES before the zone starts.

    Persists the result to /data/irrigation_schedule.json.
    """
    config = get_config()
    data = _load_data()
    probes = data.get("probes", {})

    print(f"[MOISTURE] Timeline calc: {len(probes)} probe(s), "
          f"{len(config.allowed_control_entities)} control entities")

    # 1. Find start time entities
    start_time_eids = [
        eid for eid in config.allowed_control_entities
        if eid.startswith("text.") and "start_time" in eid.lower()
    ]
    start_time_eids.sort(
        key=lambda e: int(m.group(1))
        if (m := re.search(r'(\d+)', e.split("start_time")[-1])) else 99
    )

    if not start_time_eids:
        # Debug: show all text.* entities to understand what's available
        text_eids = [e for e in config.allowed_control_entities if e.startswith("text.")]
        print(f"[MOISTURE] Timeline: NO start_time entities found! "
              f"text.* entities in controls: {text_eids}")
    else:
        print(f"[MOISTURE] Timeline: found {len(start_time_eids)} start_time entities: "
              f"{start_time_eids}")

    # 2. Fetch start time values
    start_times = []
    if start_time_eids:
        states = await ha_client.get_entities_by_ids(start_time_eids)
        for s in states:
            val = s.get("state", "")
            eid = s.get("entity_id", "")
            if val and val not in ("unknown", "unavailable", ""):
                try:
                    mins = _parse_time_to_minutes(val)
                    start_times.append({
                        "entity_id": eid,
                        "time_str": val,
                        "start_minutes": mins,
                    })
                except (ValueError, IndexError):
                    print(f"[MOISTURE] Timeline: could not parse start time '{val}' for {eid}")
            else:
                print(f"[MOISTURE] Timeline: start time entity {eid} has no value (state='{val}')")

    print(f"[MOISTURE] Timeline: {len(start_times)} valid start time(s)")

    # 3. Get ordered enabled zones (with durations)
    ordered_zones = await _get_ordered_enabled_zones()
    print(f"[MOISTURE] Timeline: {len(ordered_zones)} enabled zone(s)")

    # 4. Build zone-to-probes mapping
    zone_probe_map = {}  # zone_entity_id -> [probe_id, ...]
    for pid, probe in probes.items():
        for z in probe.get("zone_mappings", []):
            zone_probe_map.setdefault(z, []).append(pid)

    # 5. Build schedules with zone timelines
    schedules = []
    for st in start_times:
        cumulative = 0.0
        zone_timeline = []
        for z in ordered_zones:
            zone_start = st["start_minutes"] + cumulative
            zone_end = zone_start + z["duration_minutes"]
            mapped_pids = zone_probe_map.get(z["zone_entity_id"], [])
            zone_timeline.append({
                "zone_num": z["zone_num"],
                "zone_entity_id": z["zone_entity_id"],
                "duration_minutes": z["duration_minutes"],
                "expected_start_minutes": zone_start,
                "expected_end_minutes": zone_end,
                "expected_start_time": _minutes_to_hhmm(zone_start),
                "expected_end_time": _minutes_to_hhmm(zone_end),
                "has_mapped_probes": len(mapped_pids) > 0,
                "mapped_probe_ids": mapped_pids,
            })
            cumulative += z["duration_minutes"]
        schedules.append({
            "start_time_entity": st["entity_id"],
            "start_time": st["time_str"],
            "start_minutes": st["start_minutes"],
            "total_duration_minutes": cumulative,
            "expected_end_time": _minutes_to_hhmm(st["start_minutes"] + cumulative),
            "zones": zone_timeline,
        })

    # 6. Build probe prep data — for each probe, find first mapped zone per schedule
    #    and calculate when to reprogram sleep duration
    probe_prep = {}
    for pid, probe in probes.items():
        mapped_zones = set(probe.get("zone_mappings", []))
        if not mapped_zones:
            print(f"[MOISTURE] Timeline: probe {pid} has no zone_mappings, skipping")
            continue
        print(f"[MOISTURE] Timeline: probe {pid} mapped to {len(mapped_zones)} zone(s): {mapped_zones}")

        # Read current sleep duration from sensor (or use cached/default)
        extra = probe.get("extra_sensors") or {}
        sleep_eid = extra.get("sleep_duration")
        current_sleep = 60  # default fallback (minutes)
        if sleep_eid:
            try:
                _load_sensor_cache()
                if sleep_eid in _sensor_cache:
                    current_sleep = float(_sensor_cache[sleep_eid].get("state", 60))
                else:
                    st_list = await ha_client.get_entities_by_ids([sleep_eid])
                    if st_list:
                        raw = st_list[0].get("state", "60")
                        if raw not in ("unavailable", "unknown"):
                            current_sleep = float(raw)
            except (ValueError, TypeError):
                pass

        # For each schedule, find ALL mapped zones (for display) and the
        # FIRST mapped zone (for prep timing — probe wakes before this one).
        first_mapped_per_schedule = []
        all_mapped_per_schedule = []  # grouped by schedule start_time
        for sched in schedules:
            found_first = False
            sched_mapped = []
            for zone in sched["zones"]:
                if zone["zone_entity_id"] in mapped_zones:
                    entry = {
                        "schedule_start_time": sched["start_time"],
                        "zone_num": zone["zone_num"],
                        "zone_entity_id": zone["zone_entity_id"],
                        "zone_start_minutes": zone["expected_start_minutes"],
                        "zone_end_minutes": zone["expected_end_minutes"],
                        "duration_minutes": zone["duration_minutes"],
                    }
                    sched_mapped.append(entry)
                    if not found_first:
                        first_mapped_per_schedule.append(entry)
                        found_first = True
            all_mapped_per_schedule.append(sched_mapped)

        # Calculate prep trigger time: zone_start - (current_sleep + PREP_BUFFER)
        # This is when we need to reprogram the probe's sleep duration
        prep_entries = []
        for fm in first_mapped_per_schedule:
            zone_start_min = fm["zone_start_minutes"]
            prep_trigger = zone_start_min - (current_sleep + PREP_BUFFER_MINUTES)
            target_wake = zone_start_min - TARGET_WAKE_BEFORE_MINUTES
            prep_entries.append({
                "schedule_start_time": fm["schedule_start_time"],
                "zone_num": fm["zone_num"],
                "zone_entity_id": fm["zone_entity_id"],
                "zone_start_minutes": zone_start_min,
                "prep_trigger_minutes": prep_trigger % 1440,
                "target_wake_minutes": target_wake % 1440,
            })

        # Build display entries for ALL mapped zones (wake schedule popup).
        # Determine action per zone: "wake" (probe sleeps then wakes) vs
        # "keep_awake" (probe stays awake from the previous mapped zone).
        # Keep awake when: zones are adjacent, or the gap between them is
        # shorter than the probe's sleep duration (sleeping+waking would
        # take longer than just staying awake).
        display_entries = []
        for sched_zones in all_mapped_per_schedule:
            for i, am in enumerate(sched_zones):
                zone_start_min = am["zone_start_minutes"]
                target_wake = zone_start_min - TARGET_WAKE_BEFORE_MINUTES
                if i == 0:
                    action = "wake"
                else:
                    prev = sched_zones[i - 1]
                    gap = zone_start_min - prev["zone_end_minutes"]
                    # Keep awake if gap is shorter than sleep duration
                    # (no point sleeping for less time than one sleep cycle)
                    if gap <= current_sleep:
                        action = "keep_awake"
                    else:
                        action = "wake"
                display_entries.append({
                    "schedule_start_time": am["schedule_start_time"],
                    "zone_num": am["zone_num"],
                    "zone_entity_id": am["zone_entity_id"],
                    "zone_start_minutes": zone_start_min,
                    "target_wake_minutes": target_wake % 1440,
                    "action": action,
                })

        probe_prep[pid] = {
            "original_sleep_duration": current_sleep,
            "current_sleep_duration": current_sleep,
            "prep_entries": prep_entries,
            "display_entries": display_entries,
            "state": "idle",
            "skipped_zones": [],
            "active_schedule_start_time": None,
        }

    timeline = {
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "schedules": schedules,
        "zone_probe_map": {k: v for k, v in zone_probe_map.items()},
        "probe_prep": probe_prep,
    }

    _save_schedule_timeline(timeline)
    probe_count = len(probe_prep)
    schedule_count = len(schedules)
    print(f"[MOISTURE] Schedule timeline calculated: {schedule_count} schedule(s), "
          f"{probe_count} probe(s) with mapped zones")
    return timeline


def _get_schedule_entity_ids() -> set:
    """Get the set of schedule-related entity IDs that trigger timeline recalculation.

    Includes start times, run durations, zone enables, and schedule enable.
    """
    try:
        config = get_config()
        entities = set()
        for eid in config.allowed_control_entities:
            eid_lower = eid.lower()
            # Start time text entities
            if eid.startswith("text.") and "start_time" in eid_lower:
                entities.add(eid)
            # Zone duration number entities
            if eid.startswith("number.") and re.search(r'zone.*duration|duration.*zone|run_duration', eid_lower):
                entities.add(eid)
            # Zone enable switches
            if eid.startswith("switch.") and "enable_zone" in eid_lower:
                entities.add(eid)
            # Schedule enable switch
            if eid.startswith("switch.") and "schedule" in eid_lower and "enable" in eid_lower:
                entities.add(eid)
        return entities
    except Exception:
        return set()


# --- Data Model ---

DEFAULT_DATA = {
    "version": 2,
    "enabled": False,
    "apply_factors_to_schedule": False,
    "schedule_sync_enabled": True,
    "multi_probe_mode": "conservative",  # "conservative", "average", "optimistic"
    "skip_disabled_zones": [],  # Zone enable switch entities disabled by moisture skip
    "stale_reading_threshold_minutes": 120,
    # Legacy depth_weights kept for migration — no longer used in algorithm
    "depth_weights": {"shallow": 0.2, "mid": 0.5, "deep": 0.3},
    "default_thresholds": {
        # Root zone (mid sensor) thresholds — the primary decision driver
        "root_zone_skip": 80,       # Mid ≥ this → skip watering entirely (soil is saturated)
        "root_zone_wet": 65,        # Mid ≥ this → reduce watering (soil is adequately moist)
        "root_zone_optimal": 45,    # Mid around this → normal watering (1.0x multiplier)
        "root_zone_dry": 30,        # Mid ≤ this → increase watering (soil needs water)
        # Multiplier bounds
        "max_increase_percent": 50,
        "max_decrease_percent": 50,
        # Rain detection — shallow sensor + weather integration
        "rain_boost_threshold": 15,  # Shallow-minus-mid delta that indicates recent rain
    },
    "probes": {},
    "base_durations": {},
    "duration_adjustment_active": False,
    "adjusted_durations": {},
    "last_evaluation": None,
    "last_evaluation_result": {},
}


# --- Persistence ---

def _load_data() -> dict:
    """Load moisture probe data from persistent storage."""
    if os.path.exists(MOISTURE_FILE):
        try:
            with open(MOISTURE_FILE, "r") as f:
                data = json.load(f)
                # Forward-compat: ensure all default keys exist
                for key, default in DEFAULT_DATA.items():
                    if key not in data:
                        data[key] = default
                return data
        except (json.JSONDecodeError, IOError):
            pass
    return json.loads(json.dumps(DEFAULT_DATA))  # deep copy


def _save_data(data: dict):
    """Save moisture probe data to persistent storage."""
    os.makedirs(os.path.dirname(MOISTURE_FILE), exist_ok=True)
    with open(MOISTURE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# --- Probe Discovery ---

async def discover_moisture_probes() -> list[dict]:
    """Scan all HA sensor entities for moisture probe candidates.

    Looks for sensor.* entities whose entity_id or friendly_name contains
    any of the probe keywords (gophr, moisture, soil).

    Returns a list of candidate entities with their current state.
    """
    all_states = await ha_client.get_all_states()
    candidates = []

    for s in all_states:
        eid = s.get("entity_id", "")
        if not eid.startswith("sensor."):
            continue

        attrs = s.get("attributes", {})
        friendly_name = attrs.get("friendly_name", "")
        searchable = f"{eid} {friendly_name}".lower()

        if any(kw in searchable for kw in PROBE_KEYWORDS):
            candidates.append({
                "entity_id": eid,
                "friendly_name": friendly_name,
                "state": s.get("state", "unknown"),
                "unit_of_measurement": attrs.get("unit_of_measurement", ""),
                "device_class": attrs.get("device_class", ""),
                "last_updated": s.get("last_updated", ""),
            })

    return candidates


# Keywords for filtering HA devices — show Gophr/moisture probe devices
DEVICE_KEYWORDS = ["gophr", "moisture"]


async def list_moisture_devices(show_all: bool = False) -> dict:
    """List HA devices, filtered to Gophr devices by default.

    Returns devices in the same format as admin device listing.
    """
    devices = await ha_client.get_device_registry()

    all_devices = []
    for device in devices:
        name = device.get("name_by_user") or device.get("name") or ""
        manufacturer = device.get("manufacturer") or ""
        model = device.get("model") or ""

        if not name:
            continue

        all_devices.append({
            "id": device.get("id", ""),
            "name": name,
            "manufacturer": manufacturer,
            "model": model,
            "area_id": device.get("area_id", ""),
        })

    if show_all:
        result = all_devices
    else:
        # Filter to Gophr devices only
        def _is_moisture_device(name: str, manufacturer: str, model: str) -> bool:
            searchable = f"{name} {manufacturer} {model}".lower()
            return any(kw in searchable for kw in DEVICE_KEYWORDS)

        result = [d for d in all_devices if _is_moisture_device(
            d["name"], d["manufacturer"], d["model"]
        )]

    result.sort(key=lambda d: d["name"].lower())
    return {"devices": result, "total_count": len(all_devices), "filtered": not show_all}


async def get_device_sensors(device_id: str) -> tuple[list[dict], list[str]]:
    """Get all sensor entities belonging to a specific device.

    Uses HA's built-in device_entities() template function — the same mechanism
    that powers auto-entities cards. This is the most reliable way to get entities
    for a device because HA resolves the device→entity mapping internally.

    Returns a tuple of:
      - sensor entities with their current state (works even when device is offline)
      - ALL entity IDs for the device (all domains, for Phase 2 control entity detection)
    """
    # Use HA's device_entities() — same as auto-entities card filter: device: "name"
    all_entity_ids = await ha_client.get_entities_for_device(device_id)
    print(f"[MOISTURE] get_device_sensors: device_entities({device_id}) returned {len(all_entity_ids)} entities")

    if all_entity_ids:
        print(f"[MOISTURE]   All entities: {all_entity_ids}")

    # Filter to sensor domain only
    sensor_ids = [eid for eid in all_entity_ids if eid.startswith("sensor.")]
    non_sensor_ids = [eid for eid in all_entity_ids if not eid.startswith("sensor.")]
    print(f"[MOISTURE]   Sensor entities: {len(sensor_ids)}, Non-sensor entities: {len(non_sensor_ids)}")
    if non_sensor_ids:
        print(f"[MOISTURE]   Non-sensor entities: {non_sensor_ids}")

    if not sensor_ids:
        print(f"[MOISTURE]   No sensor entities found for device {device_id}")
        return [], all_entity_ids

    # Fetch current states for the sensor entities
    states = await ha_client.get_entities_by_ids(sensor_ids)
    state_lookup = {s.get("entity_id", ""): s for s in states}

    sensors = []
    for eid in sensor_ids:
        state_data = state_lookup.get(eid, {})
        attrs = state_data.get("attributes", {})
        sensors.append({
            "entity_id": eid,
            "friendly_name": attrs.get("friendly_name", eid),
            "state": state_data.get("state", "unavailable"),
            "unit_of_measurement": attrs.get("unit_of_measurement", ""),
            "device_class": attrs.get("device_class", ""),
            "last_updated": state_data.get("last_updated", ""),
            "original_name": attrs.get("friendly_name", eid),
        })

    sensors.sort(key=lambda s: s["entity_id"])
    return sensors, all_entity_ids


# --- Sensor State Fetching ---

async def _get_probe_sensor_states(probes: dict) -> dict:
    """Fetch current states for all sensors across all probes.

    When a sensor is unavailable (device sleeping), the last-known-good
    cached value is returned instead so the multiplier doesn't reset to 1.0x.

    Returns:
        {entity_id: {state: float|None, last_updated: str, stale: bool, cached: bool}}
    """
    _load_sensor_cache()

    # Collect all unique sensor entity IDs
    sensor_ids = set()
    for probe in probes.values():
        for depth, eid in probe.get("sensors", {}).items():
            if eid:
                sensor_ids.add(eid)

    if not sensor_ids:
        return {}

    # Build set of depth sensor entity IDs belonging to sleeping probes.
    # During sleep transitions ESPHome may briefly report 0 before going
    # unavailable — protect the cache from those transient values.
    sleeping_sensor_eids = set()
    for probe_id, probe in probes.items():
        if not _probe_awake_cache.get(probe_id, True):
            for eid in probe.get("sensors", {}).values():
                if eid:
                    sleeping_sensor_eids.add(eid)

    all_states = await ha_client.get_entities_by_ids(list(sensor_ids))
    result = {}
    cache_dirty = False

    for s in all_states:
        eid = s.get("entity_id", "")
        state_val = s.get("state", "unknown")
        try:
            numeric_val = float(state_val)
        except (ValueError, TypeError):
            numeric_val = None

        # If the probe is sleeping and we have a cached value, always use cache
        if eid in sleeping_sensor_eids and eid in _sensor_cache:
            cached = _sensor_cache[eid]
            result[eid] = {
                "state": cached["state"],
                "raw_state": cached.get("raw_state", str(cached["state"])),
                "last_updated": cached.get("last_updated", ""),
                "friendly_name": cached.get("friendly_name", eid),
                "cached": True,
            }
        elif numeric_val is not None:
            # Good reading from awake probe — update the cache
            _sensor_cache[eid] = {
                "state": numeric_val,
                "raw_state": state_val,
                "last_updated": s.get("last_updated", ""),
                "friendly_name": s.get("attributes", {}).get("friendly_name", eid),
            }
            cache_dirty = True
            result[eid] = {
                "state": numeric_val,
                "raw_state": state_val,
                "last_updated": s.get("last_updated", ""),
                "friendly_name": s.get("attributes", {}).get("friendly_name", eid),
                "cached": False,
            }
        elif eid in _sensor_cache:
            # Device unavailable/unknown — use cached value
            cached = _sensor_cache[eid]
            result[eid] = {
                "state": cached["state"],
                "raw_state": cached.get("raw_state", str(cached["state"])),
                "last_updated": cached.get("last_updated", ""),
                "friendly_name": cached.get("friendly_name", eid),
                "cached": True,
            }
        else:
            # No cache available — pass through as None
            result[eid] = {
                "state": None,
                "raw_state": state_val,
                "last_updated": s.get("last_updated", ""),
                "friendly_name": s.get("attributes", {}).get("friendly_name", eid),
                "cached": False,
            }

    if cache_dirty:
        _save_sensor_cache()

    return result


def get_cached_sensor_states(probes: dict) -> dict:
    """Build sensor states from the in-memory/disk cache (sync, no HA calls).

    Used by run_log.py to compute moisture multipliers without async HA calls.
    Returns the same format as _get_probe_sensor_states() but sourced entirely
    from the sensor cache that is kept fresh by the async poller.
    """
    _load_sensor_cache()
    result = {}
    for probe in probes.values():
        for depth, eid in probe.get("sensors", {}).items():
            if not eid:
                continue
            if eid in _sensor_cache:
                cached = _sensor_cache[eid]
                result[eid] = {
                    "state": cached["state"],
                    "raw_state": cached.get("raw_state", str(cached["state"])),
                    "last_updated": cached.get("last_updated", ""),
                    "friendly_name": cached.get("friendly_name", eid),
                    "cached": True,
                }
            else:
                result[eid] = {
                    "state": None,
                    "raw_state": "unknown",
                    "last_updated": "",
                    "friendly_name": eid,
                    "cached": False,
                }
    return result


def _is_stale(last_updated: str, threshold_minutes: int) -> bool:
    """Check if a sensor reading is older than the stale threshold."""
    if not last_updated:
        return True
    try:
        updated_dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - updated_dt).total_seconds() / 60
        return age > threshold_minutes
    except (ValueError, TypeError):
        return True


# --- Weather Forecast Helper ---

def _get_precipitation_probability() -> float:
    """Get today's precipitation probability from the weather forecast.

    Returns the highest precipitation_probability from the first 2 forecast
    entries (roughly the next 24 hours), or 0 if unavailable.
    """
    try:
        from routes.weather import get_weather_data
        import asyncio

        # We can't await here from a sync function, so read saved weather data
        from routes.weather import _load_weather_rules
        rules_data = _load_weather_rules()
        last_data = rules_data.get("last_weather_data", {})

        # The weather condition can tell us if it's currently raining
        condition = last_data.get("condition", "")
        rain_conditions = {"rainy", "pouring", "lightning-rainy"}
        if condition in rain_conditions:
            return 100.0

        # For forecast probability, read from weather rules file
        # (the forecast isn't stored in last_weather_data, but
        #  the weather evaluation stores rain_forecast triggers)
        active = rules_data.get("active_adjustments", [])
        for adj in active:
            if adj.get("rule") == "rain_forecast":
                # Rain is forecasted — extract probability from reason string
                reason = adj.get("reason", "")
                # e.g. "Rain forecasted (75% probability)"
                import re
                match = re.search(r'(\d+)%', reason)
                if match:
                    return float(match.group(1))
                return 75.0  # default high if rain_forecast triggered

        return 0.0
    except Exception:
        return 0.0


def _get_weather_condition() -> str:
    """Get the current weather condition from saved weather data."""
    try:
        from routes.weather import _load_weather_rules
        rules_data = _load_weather_rules()
        return rules_data.get("last_weather_data", {}).get("condition", "")
    except Exception:
        return ""


# --- Moisture Multiplier Calculation ---

def _analyze_probe_gradient(
    depth_readings: dict,
    thresholds: dict,
    precip_probability: float,
    weather_condition: str,
) -> dict:
    """Analyze a single probe's depth readings using gradient-based logic.

    The algorithm treats each sensor depth as a distinct signal:
      - Mid (root zone): PRIMARY decision driver — where grass roots live
      - Shallow (surface): Rain detection signal — wet surface + rain = recently rained
      - Deep (reserve): Over-irrigation / reserve indicator

    The gradient between sensors reveals the soil moisture profile:
      - Shallow > Mid > Deep → wetting front moving down (recent rain/irrigation)
      - Shallow < Mid → surface drying out, root zone still moist (normal)
      - Mid very low, Deep still moist → root zone depleted, deep reserves remain
      - All high → saturated, skip watering

    Returns:
        {
            "multiplier": float,
            "skip": bool,
            "reason": str,
            "profile": str (descriptive label),
            "mid_value": float or None,
        }
    """
    shallow_val = depth_readings.get("shallow", {}).get("value")
    mid_val = depth_readings.get("mid", {}).get("value")
    deep_val = depth_readings.get("deep", {}).get("value")

    shallow_ok = shallow_val is not None and not depth_readings.get("shallow", {}).get("stale", True)
    mid_ok = mid_val is not None and not depth_readings.get("mid", {}).get("stale", True)
    deep_ok = deep_val is not None and not depth_readings.get("deep", {}).get("stale", True)

    # Thresholds — root zone focused
    root_skip = thresholds.get("root_zone_skip", 80)
    root_wet = thresholds.get("root_zone_wet", 65)
    root_optimal = thresholds.get("root_zone_optimal", 45)
    root_dry = thresholds.get("root_zone_dry", 30)
    max_increase = thresholds.get("max_increase_percent", 50) / 100
    max_decrease = thresholds.get("max_decrease_percent", 50) / 100
    rain_boost = thresholds.get("rain_boost_threshold", 15)

    # Legacy threshold support — if old keys exist, map them to new ones
    if "skip_threshold" in thresholds and "root_zone_skip" not in thresholds:
        root_skip = thresholds.get("skip_threshold", 80)
        root_wet = thresholds.get("scale_wet", 65)
        root_dry = thresholds.get("scale_dry", 30)
        root_optimal = root_dry + (root_wet - root_dry) * 0.4  # ~40% into the range

    # --- Mid sensor is the PRIMARY driver ---
    # If mid is unavailable, fall back to shallow, then deep
    primary_val = None
    primary_source = "none"
    if mid_ok:
        primary_val = mid_val
        primary_source = "mid"
    elif shallow_ok:
        primary_val = shallow_val
        primary_source = "shallow (fallback)"
    elif deep_ok:
        primary_val = deep_val
        primary_source = "deep (fallback)"

    if primary_val is None:
        return {
            "multiplier": 1.0,
            "skip": False,
            "reason": "All readings stale or unavailable",
            "profile": "unknown",
            "mid_value": None,
        }

    # --- Rain Detection from Shallow Sensor ---
    # If shallow is significantly wetter than mid, it likely rained recently
    rain_detected = False
    rain_confidence = "none"
    if shallow_ok and mid_ok:
        shallow_mid_delta = shallow_val - mid_val
        if shallow_mid_delta >= rain_boost:
            # Surface is much wetter than root zone — wetting front
            rain_detected = True
            rain_confidence = "high" if precip_probability >= 50 else "moderate"
        elif shallow_mid_delta > 5 and precip_probability >= 40:
            # Modest surface excess + weather says rain likely
            rain_detected = True
            rain_confidence = "moderate"

    # Also detect rain from weather condition alone
    rain_conditions = {"rainy", "pouring", "lightning-rainy"}
    if weather_condition in rain_conditions:
        rain_detected = True
        rain_confidence = "high"

    # --- Profile Classification ---
    profile = "unknown"
    if mid_ok:
        if shallow_ok and deep_ok:
            if shallow_val > mid_val > deep_val:
                profile = "wetting_front"  # Rain/irrigation moving down
            elif shallow_val < mid_val and mid_val > deep_val:
                profile = "subsurface_moist"  # Mid zone holding water well
            elif shallow_val < mid_val < deep_val:
                profile = "deep_reserve"  # Deeper soil holding more moisture
            elif shallow_val > mid_val and mid_val < deep_val:
                profile = "root_zone_depleted"  # Mid dried out, surface wet from dew/rain
            else:
                profile = "uniform"  # Relatively even distribution
        elif shallow_ok:
            if shallow_val > mid_val + 10:
                profile = "surface_wet"
            elif shallow_val < mid_val - 10:
                profile = "surface_dry"
            else:
                profile = "surface_even"
        else:
            profile = "mid_only"

    # --- Multiplier Calculation ---
    # Base decision on the mid (root zone) sensor
    multiplier = 1.0
    skip = False
    reasons = []

    if primary_val >= root_skip:
        # Soil is saturated at the root zone — skip entirely
        multiplier = 0.0
        skip = True
        reasons.append(f"Root zone (mid) {primary_val:.0f}% ≥ skip threshold {root_skip}%")

    elif primary_val >= root_wet:
        # Root zone is adequately moist — reduce watering
        range_span = root_skip - root_wet
        if range_span > 0:
            # Linear from (1-max_decrease) at root_wet to 0 at root_skip
            fraction = (primary_val - root_wet) / range_span
            multiplier = (1 - max_decrease) * (1 - fraction)
        else:
            multiplier = 1 - max_decrease
        reasons.append(f"Root zone (mid) {primary_val:.0f}% ≥ wet threshold {root_wet}%")

    elif primary_val >= root_optimal:
        # Root zone is in the optimal-to-wet range — slight reduction
        range_span = root_wet - root_optimal
        if range_span > 0:
            fraction = (primary_val - root_optimal) / range_span
            multiplier = 1.0 - (max_decrease * fraction)
        else:
            multiplier = 1.0
        if multiplier < 1.0:
            reasons.append(f"Root zone (mid) {primary_val:.0f}% approaching wet threshold")
        else:
            reasons.append(f"Root zone (mid) {primary_val:.0f}% in optimal range")

    elif primary_val >= root_dry:
        # Root zone between dry and optimal — increase slightly
        range_span = root_optimal - root_dry
        if range_span > 0:
            fraction = (root_optimal - primary_val) / range_span
            multiplier = 1.0 + (max_increase * fraction * 0.5)  # Up to half max increase
        else:
            multiplier = 1.0
        reasons.append(f"Root zone (mid) {primary_val:.0f}% below optimal, slightly increasing")

    else:
        # Root zone is critically dry — maximum increase
        multiplier = 1 + max_increase
        reasons.append(f"Root zone (mid) {primary_val:.0f}% < dry threshold {root_dry}%, max increase")

    # --- Rain Detection Adjustment ---
    # If we detected recent rain and the root zone is already being watered at root_wet,
    # reduce further because the wetting front hasn't reached mid yet
    if rain_detected and not skip and multiplier > 0:
        if rain_confidence == "high":
            # High confidence rain — reduce multiplier significantly
            rain_reduction = 0.4
            multiplier *= (1 - rain_reduction)
            reasons.append(f"Rain detected (high confidence) — reducing {rain_reduction*100:.0f}%")
        elif rain_confidence == "moderate":
            rain_reduction = 0.2
            multiplier *= (1 - rain_reduction)
            reasons.append(f"Rain detected (moderate confidence) — reducing {rain_reduction*100:.0f}%")

        # If mid is at or near the wet threshold with rain detected, consider skipping
        if mid_ok and mid_val >= root_wet - 5 and rain_confidence == "high":
            multiplier = 0.0
            skip = True
            reasons.append(f"Root zone (mid) {mid_val:.0f}% near wet threshold + rain → skipping")

    # --- Deep Sensor Guard ---
    # If deep sensor is very wet, the soil is saturated below the root zone
    # This suggests we might be over-irrigating even if mid looks normal
    if deep_ok and not skip:
        if deep_val >= root_skip:
            # Deep zone saturated — cap multiplier at reduced level
            multiplier = min(multiplier, 1 - max_decrease)
            reasons.append(f"Deep sensor {deep_val:.0f}% saturated — capping reduction")
        elif deep_ok and mid_ok and deep_val > mid_val + 15:
            # Deep significantly wetter than mid — water pooling below
            overwater_reduction = 0.15
            multiplier *= (1 - overwater_reduction)
            reasons.append(f"Deep {deep_val:.0f}% > mid {mid_val:.0f}% — slight over-irrigation reduction")

    # Clamp multiplier
    multiplier = round(max(multiplier, 0.0), 3)
    multiplier = min(multiplier, 1 + max_increase)

    return {
        "multiplier": multiplier,
        "skip": skip,
        "reason": "; ".join(reasons),
        "profile": profile,
        "mid_value": mid_val if mid_ok else None,
        "rain_detected": rain_detected,
        "rain_confidence": rain_confidence,
    }


def calculate_zone_moisture_multiplier(
    zone_entity_id: str,
    data: dict,
    sensor_states: dict,
) -> dict:
    """Calculate the moisture multiplier for a specific zone.

    Uses a gradient-based algorithm that treats each sensor depth as a
    distinct signal rather than computing a simple weighted average:
      - Mid (root zone): PRIMARY decision driver
      - Shallow (surface): Rain detection signal
      - Deep (reserve): Over-irrigation / reserve guard

    Args:
        zone_entity_id: The zone's HA entity_id (e.g., switch.irrigator_zone_1)
        data: The full moisture probes JSON data
        sensor_states: Dict of {entity_id: {state, last_updated, ...}}

    Returns:
        {
            "multiplier": float (0.0 to ~1.5),
            "avg_moisture": float or None,
            "skip": bool,
            "probe_count": int,
            "probe_details": [...],
            "reason": str,
        }
    """
    stale_threshold = data.get("stale_reading_threshold_minutes", 120)
    default_thresholds = data.get("default_thresholds", DEFAULT_DATA["default_thresholds"])

    # Find all probes mapped to this zone
    mapped_probes = []
    for probe_id, probe in data.get("probes", {}).items():
        if zone_entity_id in probe.get("zone_mappings", []):
            mapped_probes.append((probe_id, probe))

    if not mapped_probes:
        return {
            "multiplier": 1.0,
            "avg_moisture": None,
            "skip": False,
            "probe_count": 0,
            "probe_details": [],
            "reason": "No probes mapped to this zone",
        }

    # Get weather context for rain detection
    precip_probability = _get_precipitation_probability()
    weather_condition = _get_weather_condition()

    # Analyze each probe using gradient-based logic
    probe_details = []
    probe_multipliers = []
    any_skip = False
    all_reasons = []

    for probe_id, probe in mapped_probes:
        sensors = probe.get("sensors", {})
        thresholds = probe.get("thresholds") or default_thresholds

        # Build depth readings dict
        depth_readings = {}
        for depth in ("shallow", "mid", "deep"):
            sensor_eid = sensors.get(depth)
            if not sensor_eid:
                continue

            sensor_data = sensor_states.get(sensor_eid, {})
            value = sensor_data.get("state")
            last_updated = sensor_data.get("last_updated", "")
            stale = _is_stale(last_updated, stale_threshold)

            if value is not None and not stale:
                depth_readings[depth] = {
                    "value": value,
                    "stale": False,
                    "entity_id": sensor_eid,
                }
            else:
                depth_readings[depth] = {
                    "value": value,
                    "stale": stale,
                    "entity_id": sensor_eid,
                    "reason": "stale" if stale else "unavailable",
                }

        # Run gradient analysis
        result = _analyze_probe_gradient(
            depth_readings, thresholds, precip_probability, weather_condition,
        )

        if result["skip"]:
            any_skip = True
        if result["multiplier"] is not None:
            probe_multipliers.append(result["multiplier"])

        # Compute a representative moisture value for display (mid preferred)
        mid_reading = depth_readings.get("mid", {})
        shallow_reading = depth_readings.get("shallow", {})
        deep_reading = depth_readings.get("deep", {})
        display_moisture = None
        if mid_reading.get("value") is not None and not mid_reading.get("stale"):
            display_moisture = mid_reading["value"]
        elif shallow_reading.get("value") is not None and not shallow_reading.get("stale"):
            display_moisture = shallow_reading["value"]
        elif deep_reading.get("value") is not None and not deep_reading.get("stale"):
            display_moisture = deep_reading["value"]

        probe_details.append({
            "probe_id": probe_id,
            "display_name": probe.get("display_name", probe_id),
            "effective_moisture": round(display_moisture, 1) if display_moisture is not None else None,
            "depth_readings": depth_readings,
            "all_stale": all(
                depth_readings.get(d, {}).get("stale", True)
                for d in ("shallow", "mid", "deep")
                if d in depth_readings
            ),
            "profile": result.get("profile", "unknown"),
            "rain_detected": result.get("rain_detected", False),
        })
        all_reasons.append(f"{probe.get('display_name', probe_id)}: {result['reason']}")

    if not probe_multipliers:
        return {
            "multiplier": 1.0,
            "avg_moisture": None,
            "skip": False,
            "probe_count": len(mapped_probes),
            "probe_details": probe_details,
            "reason": "All probe readings are stale or unavailable",
        }

    # Multi-probe aggregation mode
    multi_probe_mode = data.get("multi_probe_mode", "conservative")

    if multi_probe_mode == "optimistic":
        # Only skip if ALL non-stale probes say skip; use MAX multiplier (driest reading wins)
        non_stale_details = [pd for pd in probe_details if not pd.get("all_stale")]
        all_skip = non_stale_details and all(
            pd.get("profile") == "saturated" for pd in non_stale_details
        )
        if any_skip and all_skip:
            final_multiplier = 0.0
            skip = True
        elif probe_multipliers:
            final_multiplier = max(probe_multipliers)
            skip = False
        else:
            final_multiplier = 0.0
            skip = True
    elif multi_probe_mode == "average":
        # Skip if majority of non-stale probes say skip; use AVERAGE multiplier
        skip_count = sum(
            1 for pd in probe_details
            if pd.get("profile") == "saturated" and not pd.get("all_stale")
        )
        valid_count = sum(1 for pd in probe_details if not pd.get("all_stale"))
        if valid_count > 0 and skip_count > valid_count / 2:
            final_multiplier = 0.0
            skip = True
        elif probe_multipliers:
            final_multiplier = sum(probe_multipliers) / len(probe_multipliers)
            skip = False
        else:
            final_multiplier = 0.0
            skip = True
    else:
        # Conservative (default): ANY probe skip → skip; use MIN multiplier
        if any_skip:
            final_multiplier = 0.0
            skip = True
        else:
            final_multiplier = min(probe_multipliers)
            skip = False

    # Display moisture: use mid sensor average across probes
    mid_values = [
        pd["effective_moisture"]
        for pd in probe_details
        if pd["effective_moisture"] is not None
    ]
    avg_moisture = sum(mid_values) / len(mid_values) if mid_values else None

    return {
        "multiplier": round(max(final_multiplier, 0.0), 3),
        "avg_moisture": round(avg_moisture, 1) if avg_moisture is not None else None,
        "skip": skip,
        "probe_count": len(mapped_probes),
        "probe_details": probe_details,
        "reason": "; ".join(all_reasons),
        "multi_probe_mode": multi_probe_mode,
    }


def get_weather_multiplier() -> float:
    """Get the current weather watering multiplier from weather rules data."""
    try:
        from routes.weather import _load_weather_rules
        rules_data = _load_weather_rules()
        return rules_data.get("watering_multiplier", 1.0)
    except Exception:
        return 1.0


async def get_combined_multiplier(zone_entity_id: str) -> dict:
    """Get the combined weather × moisture multiplier for a specific zone.

    Uses per-zone moisture multiplier — only probes mapped to this zone
    contribute to the moisture factor.  Zones without mapped probes get
    weather-only (moisture_multiplier = 1.0).

    Returns:
        {
            "combined_multiplier": float,
            "weather_multiplier": float,
            "moisture_multiplier": float,
            "moisture_skip": bool,
            "moisture_reason": str,
        }
    """
    data = _load_data()

    weather_mult = get_weather_multiplier()

    if not data.get("enabled"):
        return {
            "combined_multiplier": weather_mult,
            "weather_multiplier": weather_mult,
            "moisture_multiplier": 1.0,
            "moisture_skip": False,
            "moisture_reason": "Moisture probes not enabled",
        }

    sensor_states = await _get_probe_sensor_states(data.get("probes", {}))
    zone_result = calculate_zone_moisture_multiplier(
        zone_entity_id, data, sensor_states,
    )
    moisture_mult = zone_result.get("multiplier", 1.0)
    skip = zone_result.get("skip", False)

    combined = weather_mult * moisture_mult if not skip else 0.0

    return {
        "combined_multiplier": round(combined, 3),
        "weather_multiplier": weather_mult,
        "moisture_multiplier": moisture_mult,
        "moisture_skip": skip,
        "moisture_reason": zone_result.get("reason", ""),
    }


# --- Duration Adjustment for ESPHome Scheduled Runs ---

def _find_duration_entities(control_entities: list[str]) -> list[str]:
    """Identify duration entities from control entity list.

    ESPHome sprinkler controllers use various naming conventions:
      - number.*_run_duration     (e.g., number.irrigator_zone_1_run_duration)
      - number.*_duration_zone_*  (e.g., number.duration_zone_1)
      - number.*_zone_*           (e.g., number.irrigation_system_zone_1)

    Strategy: find all number.* entities that correspond to zone controls.
    Excludes repeat_cycle, multiplier, and mode entities.
    """
    import re
    # Match any number.* entity that contains "zone" followed by a digit
    zone_pattern = re.compile(r"^number\..*zone[_\s]?\d", re.IGNORECASE)
    # Also match entities with "duration" anywhere
    duration_pattern = re.compile(r"^number\..*duration", re.IGNORECASE)
    # Exclude non-duration number entities (repeat cycles, etc.)
    exclude_pattern = re.compile(r"repeat|cycle|multiplier|mode", re.IGNORECASE)

    matches = []
    for eid in control_entities:
        if not eid.startswith("number."):
            continue
        if exclude_pattern.search(eid):
            continue
        if zone_pattern.match(eid) or duration_pattern.match(eid):
            matches.append(eid)
    return matches


async def capture_base_durations() -> dict:
    """Read current zone duration number entities and save as base durations.

    Identifies duration entities from the device's control entities using
    pattern matching (zone number or 'duration' keyword), reads their current
    value from HA, and stores them as the baseline for factor adjustments.

    If config entities are empty (e.g. startup race), falls back to querying
    the device entity registry directly.

    Returns the captured durations dict.
    """
    config = get_config()
    data = _load_data()

    # Find duration entities from control entities
    duration_entities = _find_duration_entities(config.allowed_control_entities)

    # Fallback: if config has no control entities, re-resolve from device
    if not duration_entities and config.irrigation_device_id:
        print(f"[MOISTURE] No duration entities in config "
              f"({len(config.allowed_control_entities)} control entities). "
              f"Re-resolving device entities...")
        device_entities = await ha_client.get_device_entities(
            config.irrigation_device_id
        )
        other = device_entities.get("other", [])
        all_eids = [e["entity_id"] for e in other]
        duration_entities = _find_duration_entities(all_eids)
        # Update config so future calls work
        if all_eids:
            config.allowed_control_entities = all_eids
            print(f"[MOISTURE] Re-resolved: {len(all_eids)} control entities, "
                  f"{len(duration_entities)} duration entities")

    # Filter by detected zone count (expansion board limit)
    max_zones = config.detected_zone_count if hasattr(config, "detected_zone_count") else 0
    if max_zones > 0:
        filtered = []
        for eid in duration_entities:
            zn = _extract_zone_num_from_duration(eid)
            if zn > 0 and zn <= max_zones:
                filtered.append(eid)
        if filtered:
            print(f"[MOISTURE] capture_base_durations: filtered {len(duration_entities)} "
                  f"→ {len(filtered)} (max_zones={max_zones})")
            duration_entities = filtered

    print(f"[MOISTURE] capture_base_durations: "
          f"{len(duration_entities)} duration entities: {duration_entities}")
    if not duration_entities:
        print(f"[MOISTURE] All control entities: "
              f"{config.allowed_control_entities}")
        return {"captured": 0, "base_durations": {},
                "control_entities": config.allowed_control_entities}

    states = await ha_client.get_entities_by_ids(duration_entities)
    base_durations = {}

    for s in states:
        eid = s.get("entity_id", "")
        state_val = s.get("state", "")
        try:
            value = float(state_val)
        except (ValueError, TypeError):
            continue

        base_durations[eid] = {
            "entity_id": eid,
            "base_value": value,
            "friendly_name": s.get("attributes", {}).get("friendly_name", eid),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }

    data["base_durations"] = base_durations
    _save_data(data)

    print(f"[MOISTURE] Captured base durations for {len(base_durations)} entities")
    return {"captured": len(base_durations), "base_durations": base_durations}


_ZONE_NUMBER_RE = re.compile(r'zone[_]?(\d+)', re.IGNORECASE)


def _extract_zone_num_from_duration(dur_eid: str) -> int:
    """Extract zone number from a duration entity_id.

    Examples:
        number.irrigator_zone_3_run_duration → 3
        number.duration_zone_1 → 1
        number.irrigation_system_zone_12 → 12
    """
    m = _ZONE_NUMBER_RE.search(dur_eid)
    return int(m.group(1)) if m else 0


def _find_zone_entity(zone_num: int, config) -> str:
    """Find the zone switch/valve entity_id matching a zone number.

    Searches config.allowed_zone_entities for switch.*zone_N or valve.*zone_N.
    Returns the matching entity_id, or an empty string if not found.
    """
    if not zone_num:
        return ""
    for eid in config.allowed_zone_entities:
        m = _ZONE_NUMBER_RE.search(eid)
        if m and int(m.group(1)) == zone_num:
            return eid
    return ""


def _find_enable_zone_switch(zone_num: int, config) -> str:
    """Find the enable_zone switch entity for a zone number.

    Searches config.allowed_control_entities for switch.*enable_zone_N.
    Returns the matching entity_id, or an empty string if not found.
    """
    if not zone_num:
        return ""
    for eid in config.allowed_control_entities:
        if not eid.startswith("switch."):
            continue
        if "enable_zone" not in eid.lower():
            continue
        m = _ZONE_NUMBER_RE.search(eid)
        if m and int(m.group(1)) == zone_num:
            return eid
    return ""


async def _get_ordered_enabled_zones() -> list[dict]:
    """Get the ordered list of enabled zones matching ESPHome execution order.

    Returns a list of dicts, each containing:
        zone_num: int           - zone number (1-based)
        zone_entity_id: str     - e.g., "switch.zone_3"
        duration_entity_id: str - e.g., "number.irrigator_zone_3_run_duration"
        duration_minutes: float - current run duration in minutes
        mode: str               - zone mode (e.g., "Standard", "Pump Start Relay")
        is_special: bool        - True if mode is pump/master/relay

    Sort order: normal zones by zone_num ascending, special zones last.
    Only includes zones where enable_zone switch is ON.
    """
    config = get_config()

    # 1. Find all enable_zone switches
    enable_entities = [
        eid for eid in config.allowed_control_entities
        if eid.startswith("switch.") and "enable_zone" in eid.lower()
    ]

    # 2. Find all zone mode selects
    mode_entities = [
        eid for eid in config.allowed_control_entities
        if eid.startswith("select.") and re.search(r'zone_\d+_mode', eid.lower())
    ]

    # 3. Find all duration entities
    duration_entities = _find_duration_entities(config.allowed_control_entities)

    # 4. Batch-fetch all states
    all_eids = enable_entities + mode_entities + duration_entities
    if not all_eids:
        return []
    states = await ha_client.get_entities_by_ids(all_eids)
    state_map = {s["entity_id"]: s for s in states}

    # 5. Build zone info by zone number
    zone_info: dict[int, dict] = {}

    for eid in enable_entities:
        m = _ZONE_NUMBER_RE.search(eid)
        if not m:
            continue
        zn = int(m.group(1))
        if zn not in zone_info:
            zone_info[zn] = {}
        zone_info[zn]["enable_state"] = state_map.get(eid, {}).get("state", "off")

    for eid in mode_entities:
        m = _ZONE_NUMBER_RE.search(eid)
        if not m:
            continue
        zn = int(m.group(1))
        if zn not in zone_info:
            zone_info[zn] = {}
        zone_info[zn]["mode"] = state_map.get(eid, {}).get("state", "Standard")

    for eid in duration_entities:
        zn = _extract_zone_num_from_duration(eid)
        if not zn:
            continue
        try:
            dur = float(state_map.get(eid, {}).get("state", "0"))
        except (ValueError, TypeError):
            dur = 0.0
        if zn not in zone_info:
            zone_info[zn] = {}
        zone_info[zn]["duration_eid"] = eid
        zone_info[zn]["duration_minutes"] = dur

    # 6. Filter expansion board zone count
    max_zones = config.detected_zone_count if hasattr(config, "detected_zone_count") else 0

    # 7. Filter to enabled zones only, build result list
    result = []
    for zn, info in zone_info.items():
        if info.get("enable_state") != "on":
            continue
        if max_zones > 0 and zn > max_zones:
            continue
        mode = info.get("mode", "Standard")
        is_special = bool(re.search(r'pump|master|relay', mode, re.IGNORECASE))
        zone_eid = _find_zone_entity(zn, config)
        if not zone_eid:
            continue

        result.append({
            "zone_num": zn,
            "zone_entity_id": zone_eid,
            "duration_entity_id": info.get("duration_eid", ""),
            "duration_minutes": info.get("duration_minutes", 0.0),
            "mode": mode,
            "is_special": is_special,
        })

    # 8. Sort: normal zones by zone_num ascending, special zones last
    result.sort(key=lambda z: (1 if z["is_special"] else 0, z["zone_num"]))
    return result


async def _calculate_sleep_until_next_mapped_zone(
    probe_id: str,
    current_zone_entity_id: str,
) -> Optional[dict]:
    """Calculate how long a probe should sleep until the next mapped zone starts.

    After a mapped zone finishes, determine if there are more mapped zones
    remaining in this schedule cycle. If so, calculate the time gap by summing
    the adjusted durations of all enabled zones between them.

    Args:
        probe_id: The probe identifier
        current_zone_entity_id: The zone that just finished (turned OFF)

    Returns:
        dict with:
            next_zone_entity_id: str - the next mapped zone to wake for
            sleep_seconds: int       - how long to sleep (0 = keep awake)
            gap_minutes: float       - minutes gap between zones
        or None if there are no more mapped zones in this cycle.
    """
    data = _load_data()
    probe = data.get("probes", {}).get(probe_id)
    if not probe:
        return None

    mapped_zones = set(probe.get("zone_mappings", []))
    if len(mapped_zones) <= 1:
        # Only one mapped zone (or none) — no mid-run sleep needed
        return None

    # Get the ordered zone execution sequence
    ordered_zones = await _get_ordered_enabled_zones()
    if not ordered_zones:
        return None

    # Find the current zone's position in the sequence
    current_idx = None
    for i, z in enumerate(ordered_zones):
        if z["zone_entity_id"] == current_zone_entity_id:
            current_idx = i
            break

    if current_idx is None:
        print(f"[MOISTURE] _calculate_sleep: current zone {current_zone_entity_id} "
              f"not found in ordered zone list")
        return None

    # Look FORWARD from the current zone for the next mapped zone
    next_mapped_idx = None
    for i in range(current_idx + 1, len(ordered_zones)):
        if ordered_zones[i]["zone_entity_id"] in mapped_zones:
            next_mapped_idx = i
            break

    if next_mapped_idx is None:
        # No more mapped zones after this one in the cycle
        return None

    # Calculate gap: sum durations of all zones BETWEEN current and next mapped
    gap_minutes = 0.0
    for i in range(current_idx + 1, next_mapped_idx):
        gap_minutes += ordered_zones[i]["duration_minutes"]

    # Subtract a 0.5 min buffer so the probe wakes slightly before the next zone
    sleep_minutes = max(0, int(gap_minutes - 0.5))

    # If the gap is very short (< 2 minutes), don't bother sleeping
    if sleep_minutes < 2:
        return {
            "next_zone_entity_id": ordered_zones[next_mapped_idx]["zone_entity_id"],
            "sleep_minutes": 0,  # Signal: keep awake
            "gap_minutes": gap_minutes,
        }

    return {
        "next_zone_entity_id": ordered_zones[next_mapped_idx]["zone_entity_id"],
        "sleep_minutes": sleep_minutes,
        "gap_minutes": gap_minutes,
    }


async def _set_probe_sleep_duration(probe_id: str, minutes: float) -> bool:
    """Write a sleep duration (in minutes) to the Gophr's writable number entity.

    The Gophr ESPHome device expects the sleep_duration value in MINUTES.

    Args:
        probe_id: The probe identifier
        minutes: Sleep duration in minutes (supports decimals, e.g. 1.5)

    Returns True if the service call succeeded.
    """
    data = _load_data()
    probe = data.get("probes", {}).get(probe_id)
    if not probe:
        print(f"[MOISTURE] _set_probe_sleep_duration: probe {probe_id} not found")
        return False

    extra = probe.get("extra_sensors") or {}
    # Prefer the writable number entity
    sleep_number_eid = extra.get("sleep_duration_number")
    if not sleep_number_eid:
        # Fallback: derive from the sensor entity name
        sleep_sensor_eid = extra.get("sleep_duration", "")
        if sleep_sensor_eid:
            sleep_number_eid = sleep_sensor_eid.replace("sensor.", "number.", 1)
        else:
            print(f"[MOISTURE] _set_probe_sleep_duration: no sleep_duration entity "
                  f"for {probe_id}")
            return False

    success = await ha_client.call_service("number", "set_value", {
        "entity_id": sleep_number_eid,
        "value": minutes,
    })
    print(f"[MOISTURE] Set sleep duration for {probe_id}: {minutes} min via "
          f"{sleep_number_eid}: {'OK' if success else 'FAILED'}")
    return success


async def apply_adjusted_durations() -> dict:
    """Compute and write adjusted durations to HA number entities.

    For each zone's run_duration entity:
    1. Compute the per-zone moisture multiplier (only zones with mapped probes
       get moisture adjustment; unmapped zones get weather-only)
    2. Calculate adjusted duration = base × weather × moisture
    3. Write the adjusted value to the HA number entity

    Returns summary of applied adjustments.
    """
    data = _load_data()
    config = get_config()

    if not data.get("apply_factors_to_schedule"):
        return {"success": False, "reason": "Apply factors to schedule is not enabled"}

    base_durations = data.get("base_durations", {})
    if not base_durations:
        # Auto-capture base durations
        capture_result = await capture_base_durations()
        if capture_result.get("captured", 0) == 0:
            return {"success": False, "reason": "No run_duration entities found to adjust"}
        data = _load_data()  # Reload after capture
        base_durations = data.get("base_durations", {})

    # Check if any zones are currently running — defer if so
    global _deferred_factor_apply
    zones = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    running = [z for z in zones if z.get("state") in ("on", "open")]
    if running:
        _deferred_factor_apply = True
        print(f"[MOISTURE] {len(running)} zone(s) running — deferring factor re-application "
              f"until all zones stop")
        return {
            "success": False,
            "deferred": True,
            "reason": f"{len(running)} zone(s) currently running. Factors will be applied when all zones stop.",
        }

    sensor_states = await _get_probe_sensor_states(data.get("probes", {}))
    weather_mult = get_weather_multiplier()

    # Filter base_durations by detected zone count (expansion board limit)
    max_zones = config.detected_zone_count if hasattr(config, "detected_zone_count") else 0
    if max_zones > 0:
        base_durations = {
            eid: d for eid, d in base_durations.items()
            if _extract_zone_num_from_duration(eid) <= max_zones
        }

    adjusted = {}
    applied_count = 0
    failed = []
    skip_disabled = list(data.get("skip_disabled_zones", []))  # Track zones disabled by skip

    print(f"[MOISTURE] Applying per-zone factors: {len(base_durations)} duration entities, "
          f"weather_mult={weather_mult}")

    for dur_eid, dur_data in base_durations.items():
        base = dur_data["base_value"]

        # Extract zone number from duration entity → find matching zone entity
        zone_num = _extract_zone_num_from_duration(dur_eid)
        zone_entity_id = _find_zone_entity(zone_num, config)

        # Get per-zone moisture multiplier (only zones with mapped probes are affected)
        zone_result = calculate_zone_moisture_multiplier(
            zone_entity_id, data, sensor_states,
        )
        moisture_mult = zone_result.get("multiplier", 1.0)
        skip = zone_result.get("skip", False)

        if skip:
            # Disable the zone's enable switch instead of setting duration to 0.
            # This lets ESPHome skip the zone cleanly without blocking the schedule.
            enable_eid = _find_enable_zone_switch(zone_num, config)
            if enable_eid:
                disable_ok = await ha_client.call_service("switch", "turn_off", {
                    "entity_id": enable_eid,
                })
                if disable_ok and enable_eid not in skip_disabled:
                    skip_disabled.append(enable_eid)
                print(f"[MOISTURE] Skip zone {zone_num}: disabled {enable_eid} "
                      f"(success={disable_ok})")
            # Still write the adjusted duration using the base value (zone is disabled,
            # but keep duration intact for when it's re-enabled)
            combined = weather_mult * moisture_mult
            adjusted_value = float(max(1, round(base * combined))) if combined > 0 else base
        else:
            # If this zone was previously skip-disabled, re-enable it
            enable_eid = _find_enable_zone_switch(zone_num, config)
            if enable_eid and enable_eid in skip_disabled:
                enable_ok = await ha_client.call_service("switch", "turn_on", {
                    "entity_id": enable_eid,
                })
                if enable_ok:
                    skip_disabled.remove(enable_eid)
                print(f"[MOISTURE] Re-enabled zone {zone_num}: {enable_eid} "
                      f"(success={enable_ok})")
            combined = weather_mult * moisture_mult
            adjusted_value = float(max(1, round(base * combined)))

        # Write adjusted duration to HA
        print(f"[MOISTURE] Setting {dur_eid}: base={base} → adjusted={adjusted_value} "
              f"(weather={weather_mult}, moisture={moisture_mult:.3f}, "
              f"zone={zone_entity_id or 'unknown'}, skip={skip})")
        success = await ha_client.call_service("number", "set_value", {
            "entity_id": dur_eid,
            "value": adjusted_value,
        })

        if success:
            applied_count += 1
            adj_entry = {
                "entity_id": dur_eid,
                "original": base,
                "adjusted": adjusted_value,
                "weather_multiplier": weather_mult,
                "moisture_multiplier": moisture_mult,
                "combined_multiplier": round(weather_mult * moisture_mult, 3),
                "skip": skip,
                "zone_entity_id": zone_entity_id,
                "applied_at": datetime.now(timezone.utc).isoformat(),
            }
            # Capture per-zone probe context for run history
            if zone_result.get("avg_moisture") is not None:
                adj_entry["profile"] = zone_result.get("profile", "unknown")
                adj_entry["reason"] = zone_result.get("reason", "")
                # Capture sensor readings for run log display
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
                            adj_entry["sensor_readings"] = sr
                        break  # Use first probe's readings
            elif zone_result.get("probe_count", 0) == 0:
                adj_entry["reason"] = "No probes mapped — weather only"
            adjusted[dur_eid] = adj_entry
        else:
            failed.append(dur_eid)
            print(f"[MOISTURE] FAILED to set {dur_eid} to {adjusted_value}")

    data["skip_disabled_zones"] = skip_disabled
    data["duration_adjustment_active"] = applied_count > 0
    data["adjusted_durations"] = adjusted
    data["last_evaluation"] = datetime.now(timezone.utc).isoformat()
    data["last_evaluation_result"] = {
        "weather_multiplier": weather_mult,
        "zones_adjusted": applied_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _save_data(data)

    # Clear deferred flag — we just successfully applied factors
    _deferred_factor_apply = False

    result = {
        "success": applied_count > 0,
        "applied": applied_count,
        "adjustments": adjusted,
    }
    if failed:
        result["failed"] = failed
        result["reason"] = f"HA service call failed for {len(failed)} entity(ies)"
    return result


async def restore_base_durations() -> dict:
    """Restore all run_duration entities to their captured base values.

    Called after zone runs complete, on add-on restart (crash recovery),
    or manually by the user.
    """
    data = _load_data()
    config = get_config()
    base_durations = data.get("base_durations", {})

    if not base_durations:
        return {"success": True, "restored": 0, "reason": "No base durations to restore"}

    # Filter by detected zone count (expansion board limit)
    max_zones = config.detected_zone_count if hasattr(config, "detected_zone_count") else 0
    if max_zones > 0:
        base_durations = {
            eid: d for eid, d in base_durations.items()
            if _extract_zone_num_from_duration(eid) <= max_zones
        }

    # Re-enable any zones that were disabled by moisture skip
    skip_disabled = data.get("skip_disabled_zones", [])
    for enable_eid in skip_disabled:
        enable_ok = await ha_client.call_service("switch", "turn_on", {
            "entity_id": enable_eid,
        })
        print(f"[MOISTURE] Restore: re-enabled {enable_eid} (success={enable_ok})")

    restored_count = 0
    for dur_eid, dur_data in base_durations.items():
        base_value = float(dur_data["base_value"])
        success = await ha_client.call_service("number", "set_value", {
            "entity_id": dur_eid,
            "value": base_value,
        })
        if success:
            restored_count += 1
            print(f"[MOISTURE] Restored {dur_eid} to base value {base_value}")
        else:
            print(f"[MOISTURE] Failed to restore {dur_eid} to {base_value}")

    data["duration_adjustment_active"] = False
    data["adjusted_durations"] = {}
    data["skip_disabled_zones"] = []
    _save_data(data)

    return {"success": True, "restored": restored_count}


async def run_moisture_evaluation() -> dict:
    """Run a full moisture evaluation cycle.

    Called periodically by the background task and after weather evaluation.
    If apply_factors_to_schedule is enabled, re-applies adjusted durations.
    """
    data = _load_data()

    if not data.get("apply_factors_to_schedule"):
        return {"skipped": True, "reason": "Apply factors to schedule not enabled"}

    # Apply adjusted durations (handles running zone check internally)
    result = await apply_adjusted_durations()
    return result


# --- Pydantic Models for API ---

class ProbeCreateRequest(BaseModel):
    probe_id: str = Field(..., description="Unique identifier for the probe")
    display_name: str = Field("", description="Human-readable display name")
    device_id: Optional[str] = Field(None, description="HA device ID for fetching device-level sensors (WiFi, battery, etc.)")
    sensors: dict = Field(
        default_factory=dict,
        description='Sensor entity IDs by depth: {"shallow": "sensor.xxx", "mid": "sensor.yyy", "deep": "sensor.zzz"}',
    )
    extra_sensors: Optional[dict] = Field(
        None,
        description='Auto-detected device-level sensor entity IDs: {"wifi": "sensor.xxx", "battery": "sensor.yyy", "sleep_duration": "sensor.zzz"}',
    )
    zone_mappings: list[str] = Field(
        default_factory=list,
        description="List of zone entity_ids this probe is mapped to",
    )
    thresholds: Optional[dict] = Field(
        None,
        description="Per-probe thresholds (uses defaults if not set)",
    )


class ProbeUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    device_id: Optional[str] = None
    sensors: Optional[dict] = None
    extra_sensors: Optional[dict] = None
    zone_mappings: Optional[list[str]] = None
    thresholds: Optional[dict] = None


class MoistureSettingsRequest(BaseModel):
    enabled: Optional[bool] = None
    apply_factors_to_schedule: Optional[bool] = None
    schedule_sync_enabled: Optional[bool] = None
    multi_probe_mode: Optional[str] = None  # "conservative", "average", "optimistic"
    stale_reading_threshold_minutes: Optional[int] = Field(None, ge=5, le=1440)
    depth_weights: Optional[dict] = None
    default_thresholds: Optional[dict] = None


class CalibrateRequest(BaseModel):
    action: str  # "dry" or "wet"


# --- API Endpoints ---

@router.get("/probes/discover", summary="Discover moisture probe candidates")
async def api_discover_probes():
    """Scan all HA sensors for entities that look like moisture probes."""
    candidates = await discover_moisture_probes()
    return {"candidates": candidates, "total": len(candidates)}


@router.get("/devices", summary="List devices for moisture probe selection")
async def api_list_devices(show_all: bool = False):
    """List HA devices, filtered to Gophr devices by default.

    By default filters to devices with 'gophr' in the name.
    Pass ?show_all=true to return every device.
    """
    return await list_moisture_devices(show_all=show_all)


@router.get("/devices/{device_id}/sensors", summary="Get sensor entities for a device")
async def api_get_device_sensors(device_id: str):
    """Get all sensor entities belonging to a specific device.

    Returns sensors that can be mapped as probe depth readings.
    """
    sensors, _all_eids = await get_device_sensors(device_id)
    return {"device_id": device_id, "sensors": sensors, "total": len(sensors)}


@router.get("/devices/{device_id}/autodetect", summary="Auto-detect sensor assignments for a Gophr device")
async def api_autodetect_device_sensors(device_id: str):
    """Auto-detect moisture depth sensors and device status sensors from entity names.

    Gophr ESPHome devices expose both raw voltage and percentage entities for
    each moisture channel and for battery. We ONLY use percentage entities
    (raw voltages are skipped entirely).

    Mapping:
      - moisture_3_percentage → shallow (shallowest depth)
      - moisture_2_percentage → mid (root zone)
      - moisture_1_percentage → deep (deepest)
      - battery_percentage → battery (NOT battery_voltage)
      - wifi_signal_strength → wifi
      - sleep_duration → sleep_duration
      - AHT20 humidity/temperature sensors are excluded from moisture detection
    """
    sensors, all_device_entity_ids = await get_device_sensors(device_id)

    depth_map = {"shallow": None, "mid": None, "deep": None}
    extra_map = {"wifi": None, "battery": None, "sleep_duration": None}
    disabled_sensor_entities = []  # Track disabled sensors for diagnostic

    print(f"[MOISTURE] autodetect: {len(sensors)} sensors from get_device_sensors, {len(all_device_entity_ids)} total entities for device {device_id}")

    if not sensors:
        print(f"[MOISTURE] autodetect: 0 sensors — device_entities() returned nothing for this device")
    for s in sensors:
        print(f"[MOISTURE]   entity={s['entity_id']}  friendly={s.get('friendly_name','')}  class={s.get('device_class','')}  unit={s.get('unit_of_measurement','')}")

    # --- Pre-filter: skip raw voltage entities entirely ---
    # Gophr devices have both _raw_voltage (V) and _percentage (%) entities.
    # We only want the percentage versions.
    filtered_sensors = []
    for s in sensors:
        eid = s["entity_id"].lower()
        unit = s.get("unit_of_measurement", "")
        # Skip any raw voltage entity (unit V or entity name contains raw_voltage)
        if "raw_voltage" in eid or (unit == "V" and "voltage" in eid):
            print(f"[MOISTURE]   SKIP voltage: {s['entity_id']}")
            continue
        # Skip solar voltage
        if "solar" in eid and "voltage" in eid:
            print(f"[MOISTURE]   SKIP solar: {s['entity_id']}")
            continue
        filtered_sensors.append(s)

    for s in filtered_sensors:
        eid = s["entity_id"].lower()
        fname = (s.get("friendly_name") or "").lower()
        oname = (s.get("original_name") or "").lower()
        searchable = f"{eid} {fname} {oname}"
        device_class = s.get("device_class", "")

        # WiFi signal detection
        if device_class == "signal_strength" or any(
            kw in searchable for kw in ("wifi", "signal_strength", "rssi")
        ):
            if not extra_map["wifi"]:
                extra_map["wifi"] = s["entity_id"]
                print(f"[MOISTURE]   MATCH wifi: {s['entity_id']}")
            continue

        # Battery detection — prefer _percentage over _voltage
        if device_class == "battery" or "battery" in searchable:
            # Only accept percentage entities for battery
            if "percentage" in eid or "percent" in eid or s.get("unit_of_measurement") == "%":
                if not extra_map["battery"]:
                    extra_map["battery"] = s["entity_id"]
                    print(f"[MOISTURE]   MATCH battery: {s['entity_id']}")
            continue

        # Sleep duration detection
        if "sleep" in searchable:
            if not extra_map["sleep_duration"]:
                extra_map["sleep_duration"] = s["entity_id"]
                print(f"[MOISTURE]   MATCH sleep: {s['entity_id']}")
            continue

        # Skip non-moisture environmental sensors (AHT20 temperature, humidity, etc.)
        # These are ambient sensors, not soil moisture sensors.
        if any(kw in searchable for kw in ("temperature", "humidity", "aht")):
            if "moisture" not in searchable:
                print(f"[MOISTURE]   SKIP ambient: {s['entity_id']}")
                continue

        # Skip uptime, time_awake, minutes_to_next_wake — not moisture sensors
        if any(kw in searchable for kw in ("uptime", "time_awake", "minutes_to_next", "next_wake")):
            print(f"[MOISTURE]   SKIP timing: {s['entity_id']}")
            continue

        # Moisture depth detection
        # Priority 1: numbered sensors (sensor_3=shallow, sensor_2=mid, sensor_1=deep)
        # Matches: moisture_1_percentage, moisture_sensor_1, moisture_1, etc.
        num_match = re.search(r'(?:moisture|sensor|channel|probe)[_\s]*(\d+)', searchable)
        if num_match:
            num = int(num_match.group(1))
            if num == 3 and not depth_map["shallow"]:
                depth_map["shallow"] = s["entity_id"]
                print(f"[MOISTURE]   MATCH shallow (num 3): {s['entity_id']}")
                continue
            elif num == 2 and not depth_map["mid"]:
                depth_map["mid"] = s["entity_id"]
                print(f"[MOISTURE]   MATCH mid (num 2): {s['entity_id']}")
                continue
            elif num == 1 and not depth_map["deep"]:
                depth_map["deep"] = s["entity_id"]
                print(f"[MOISTURE]   MATCH deep (num 1): {s['entity_id']}")
                continue

        # Priority 2: keyword matching
        if any(kw in searchable for kw in ("shallow", "surface", "top")):
            if not depth_map["shallow"]:
                depth_map["shallow"] = s["entity_id"]
                print(f"[MOISTURE]   MATCH shallow (keyword): {s['entity_id']}")
        elif any(kw in searchable for kw in ("mid", "middle", "root")):
            if not depth_map["mid"]:
                depth_map["mid"] = s["entity_id"]
                print(f"[MOISTURE]   MATCH mid (keyword): {s['entity_id']}")
        elif any(kw in searchable for kw in ("deep", "bottom", "reserve")):
            if not depth_map["deep"]:
                depth_map["deep"] = s["entity_id"]
                print(f"[MOISTURE]   MATCH deep (keyword): {s['entity_id']}")

    # Priority 3: If we still have unmatched moisture sensors, try remaining
    # percentage sensors that contain 'moisture' in name
    if not all(depth_map.values()):
        unmatched_moisture = []
        matched_eids = set(v for v in list(depth_map.values()) + list(extra_map.values()) if v)
        for s in filtered_sensors:
            if s["entity_id"] in matched_eids:
                continue
            eid_lower = s["entity_id"].lower()
            fname_lower = (s.get("friendly_name") or "").lower()
            unit = s.get("unit_of_measurement", "")
            dc = s.get("device_class", "")
            # Must contain 'moisture' in name AND be a percentage entity
            # Excludes AHT20 humidity which doesn't contain 'moisture'
            if "moisture" in eid_lower or "moisture" in fname_lower:
                if unit == "%" or dc in ("humidity", "moisture"):
                    unmatched_moisture.append(s)

        # Try to extract numbers from unmatched moisture sensors
        for s in unmatched_moisture:
            eid_lower = s["entity_id"].lower()
            fname_lower = (s.get("friendly_name") or "").lower()
            combined = f"{eid_lower} {fname_lower}"
            # Look for any number after 'moisture'
            num_match = re.search(r'(\d+)', combined.split("moisture")[-1] if "moisture" in combined else "")
            if num_match:
                num = int(num_match.group(1))
                if num == 3 and not depth_map["shallow"]:
                    depth_map["shallow"] = s["entity_id"]
                elif num == 2 and not depth_map["mid"]:
                    depth_map["mid"] = s["entity_id"]
                elif num == 1 and not depth_map["deep"]:
                    depth_map["deep"] = s["entity_id"]

        # Last resort: if we found exactly 3 unmatched moisture sensors and
        # none were assigned, assign in order (1=deep, 2=mid, 3=shallow)
        if not any(depth_map.values()) and len(unmatched_moisture) == 3:
            depth_map["deep"] = unmatched_moisture[0]["entity_id"]
            depth_map["mid"] = unmatched_moisture[1]["entity_id"]
            depth_map["shallow"] = unmatched_moisture[2]["entity_id"]

    # --- Detect Gophr sleep/schedule/control entities ---
    # Use the SAME entity list from Phase 1 (already fetched via device_entities()),
    # then classify the non-sensor entities (switches, lights, numbers, text, binary_sensor).
    # If device_entities() returned no non-sensor entities, fall back to searching all_states
    # by the device name slug extracted from known sensor entity IDs.
    schedule_times = []
    sleep_disabled_switch = None
    sleep_duration_number = None
    min_awake_entity = None
    max_awake_entity = None
    status_led_entity = None
    solar_charging_entity = None
    sleep_now_entity = None
    calibrate_dry_buttons = []
    calibrate_wet_buttons = []

    # Reuse all_device_entity_ids from get_device_sensors() — no second HTTP call needed
    non_sensor_eids = [e for e in all_device_entity_ids if not e.startswith("sensor.")]
    print(f"[MOISTURE]   Phase 2: {len(all_device_entity_ids)} total entities, {len(non_sensor_eids)} non-sensor: {non_sensor_eids}")

    # Fallback: if device_entities() returned only sensors (no switches/lights/numbers/buttons),
    # extract the device slug from known sensor entity IDs and search all_states by pattern.
    # This handles cases where HA's device_entities() doesn't return all domain types.
    if not non_sensor_eids and sensors:
        # Extract device slug from a known sensor entity_id
        # e.g., "sensor.gophr_2ac860_moisture_3_percentage" → "gophr_2ac860"
        sample_eid = sensors[0]["entity_id"]  # e.g., "sensor.gophr_2ac860_..."
        slug_part = sample_eid.split(".", 1)[1] if "." in sample_eid else sample_eid
        # Find the device slug: everything before the first sensor-specific part
        # For "gophr_2ac860_moisture_3_percentage", we want "gophr_2ac860"
        # Strategy: find the common prefix among all sensor entity_ids
        all_sensor_eids = [s["entity_id"].split(".", 1)[1] for s in sensors if "." in s["entity_id"]]
        if len(all_sensor_eids) >= 2:
            # Find common prefix of all sensor slugs
            prefix = all_sensor_eids[0]
            for other in all_sensor_eids[1:]:
                while not other.startswith(prefix):
                    prefix = prefix[:-1]
                    if not prefix:
                        break
            # Clean up: remove trailing underscore
            device_slug = prefix.rstrip("_")
        else:
            # Single sensor — take everything before the last few segments
            # "gophr_2ac860_moisture_3_percentage" → try "gophr_2ac860"
            parts = slug_part.split("_")
            # Heuristic: device slug is the first 2-3 parts (before sensor-specific names)
            device_slug = "_".join(parts[:2]) if len(parts) > 2 else slug_part

        if device_slug and len(device_slug) >= 4:
            print(f"[MOISTURE]   Phase 2 fallback: searching all_states for slug '{device_slug}'")
            try:
                all_states = await ha_client.get_all_states()
                for state_obj in all_states:
                    eid = state_obj.get("entity_id", "")
                    if device_slug in eid and not eid.startswith("sensor."):
                        if eid not in all_device_entity_ids:
                            all_device_entity_ids.append(eid)
                fallback_non_sensor = [e for e in all_device_entity_ids if not e.startswith("sensor.")]
                print(f"[MOISTURE]   Phase 2 fallback found {len(fallback_non_sensor)} non-sensor entities: {fallback_non_sensor}")
            except Exception as e:
                print(f"[MOISTURE]   Phase 2 fallback failed: {e}")
        else:
            print(f"[MOISTURE]   Phase 2 fallback: could not extract device slug from sensor entities")

    for eid in all_device_entity_ids:
        eid_lower = eid.lower()
        domain = eid.split(".")[0] if "." in eid else ""

        # Schedule time text entities (text.gophr_*_schedule_time_1..4)
        if domain == "text" and "schedule_time" in eid_lower:
            if eid not in schedule_times:
                schedule_times.append(eid)
                print(f"[MOISTURE]   MATCH schedule_time: {eid}")

        # Sleep disabled switch (switch.gophr_*_sleep_disabled or *_disable_sleep)
        if domain == "switch" and ("sleep_disabled" in eid_lower or "disable_sleep" in eid_lower):
            if not sleep_disabled_switch:
                sleep_disabled_switch = eid
                print(f"[MOISTURE]   MATCH sleep_disabled: {eid}")

        # Status LED light entity (light.*_status_led) — ON=awake, OFF=sleeping
        if domain == "light" and "status_led" in eid_lower:
            if not status_led_entity:
                status_led_entity = eid
                print(f"[MOISTURE]   MATCH status_led: {eid}")

        # Solar charging binary sensor (binary_sensor.*_solar_charging)
        if domain == "binary_sensor" and "solar_charging" in eid_lower:
            if not solar_charging_entity:
                solar_charging_entity = eid
                print(f"[MOISTURE]   MATCH solar_charging: {eid}")

        # Min/max awake minutes, sleep duration (number domain)
        if domain == "number":
            if "min_awake" in eid_lower and not min_awake_entity:
                min_awake_entity = eid
                print(f"[MOISTURE]   MATCH min_awake: {eid}")
            elif "max_awake" in eid_lower and not max_awake_entity:
                max_awake_entity = eid
                print(f"[MOISTURE]   MATCH max_awake: {eid}")
            elif "sleep_duration" in eid_lower and not sleep_duration_number:
                sleep_duration_number = eid
                print(f"[MOISTURE]   MATCH sleep_duration_number: {eid}")

        # Sleep Now button (button.gophr_*_sleep_now) — forces the device to sleep immediately
        if domain == "button" and "sleep_now" in eid_lower:
            if not sleep_now_entity:
                sleep_now_entity = eid
                print(f"[MOISTURE]   MATCH sleep_now: {eid}")

        # Calibration buttons (button.gophr_*_calibrate_moisture_X_dry / _wet)
        if domain == "button" and "calibrate_moisture" in eid_lower:
            if "_dry" in eid_lower:
                if eid not in calibrate_dry_buttons:
                    calibrate_dry_buttons.append(eid)
                    print(f"[MOISTURE]   MATCH calibrate_dry: {eid}")
            elif "_wet" in eid_lower:
                if eid not in calibrate_wet_buttons:
                    calibrate_wet_buttons.append(eid)
                    print(f"[MOISTURE]   MATCH calibrate_wet: {eid}")

    # Sort schedule times by number suffix (schedule_time_1, _2, _3, _4)
    schedule_times.sort(key=lambda e: int(re.search(r'(\d+)$', e).group(1)) if re.search(r'(\d+)$', e) else 99)

    if schedule_times:
        extra_map["schedule_times"] = schedule_times
    if sleep_disabled_switch:
        extra_map["sleep_disabled"] = sleep_disabled_switch
    if status_led_entity:
        extra_map["status_led"] = status_led_entity
    if min_awake_entity:
        extra_map["min_awake_minutes"] = min_awake_entity
    if max_awake_entity:
        extra_map["max_awake_minutes"] = max_awake_entity
    if sleep_duration_number:
        extra_map["sleep_duration_number"] = sleep_duration_number
    if solar_charging_entity:
        extra_map["solar_charging"] = solar_charging_entity
    if sleep_now_entity:
        extra_map["sleep_now"] = sleep_now_entity

    # Sort calibration buttons by moisture number (moisture_1, _2, _3)
    def _cal_sort_key(eid):
        m = re.search(r'moisture[_]?(\d+)', eid.lower())
        return int(m.group(1)) if m else 99

    if calibrate_dry_buttons:
        calibrate_dry_buttons.sort(key=_cal_sort_key)
        extra_map["calibrate_dry"] = calibrate_dry_buttons
    if calibrate_wet_buttons:
        calibrate_wet_buttons.sort(key=_cal_sort_key)
        extra_map["calibrate_wet"] = calibrate_wet_buttons

    print(f"[MOISTURE] autodetect result: depths={depth_map}, extras={extra_map}")

    # Build diagnostic info when detection fails
    diagnostic = {}
    if not any(depth_map.values()):
        diagnostic["error"] = "No depth sensors detected"
        diagnostic["device_id"] = device_id
        diagnostic["sensor_count"] = len(sensors)
        diagnostic["filtered_sensor_count"] = len(filtered_sensors)
        diagnostic["device_entities_count"] = len(all_device_entity_ids) if all_device_entity_ids else 0
        if disabled_sensor_entities:
            diagnostic["disabled_sensors"] = disabled_sensor_entities
            diagnostic["hint"] = (
                f"Found {len(disabled_sensor_entities)} sensor entities that are DISABLED in "
                f"Home Assistant. Go to the ESPHome device page in HA, enable these entities, "
                f"then try again."
            )
        elif not sensors:
            diagnostic["hint"] = (
                "No sensor entities found for this device_id. "
                "The device may have a different internal ID than expected. "
                "Try selecting 'Show all devices' and re-selecting the device."
            )
        elif not filtered_sensors:
            diagnostic["hint"] = (
                f"Found {len(sensors)} sensor(s) but all were filtered out "
                f"(voltage/solar entities). Check entity names."
            )
        else:
            diagnostic["hint"] = (
                f"Found {len(filtered_sensors)} sensor(s) but none matched depth patterns. "
                f"Expected entity names containing 'moisture_1', 'moisture_2', 'moisture_3' "
                f"or keywords like 'shallow', 'mid', 'deep'."
            )
            diagnostic["sensor_entities"] = [s["entity_id"] for s in filtered_sensors]

    return {
        "device_id": device_id,
        "sensors": depth_map,
        "extra_sensors": {k: v for k, v in extra_map.items() if v is not None},
        "all_sensors": sensors,
        "all_entity_ids": all_device_entity_ids,
        "total": len(sensors),
        "total_all_domains": len(all_device_entity_ids),
        **({"diagnostic": diagnostic} if diagnostic else {}),
    }


@router.get("/probes", summary="Get probe configuration and live readings")
async def api_get_probes():
    """Get all configured probes with their current sensor readings."""
    data = _load_data()
    probes = data.get("probes", {})

    if not probes:
        return {
            "enabled": data.get("enabled", False),
            "probes": {},
            "total": 0,
        }

    # Collect ALL entity IDs we need to fetch — depth sensors + extra sensors
    all_sensor_ids = set()
    for probe in probes.values():
        for eid in probe.get("sensors", {}).values():
            if eid:
                all_sensor_ids.add(eid)
        for key, val in probe.get("extra_sensors", {}).items():
            if isinstance(val, list):
                for eid in val:
                    if eid:
                        all_sensor_ids.add(eid)
            elif val:
                all_sensor_ids.add(val)

    # Single batch fetch for all sensor states
    all_states = await ha_client.get_entities_by_ids(list(all_sensor_ids)) if all_sensor_ids else []

    # Use sensor cache to retain last-known-good values when device is sleeping
    _load_sensor_cache()
    cache_dirty = False

    # Build set of depth sensor entity IDs belonging to sleeping probes.
    # During sleep transitions ESPHome may briefly report 0 before going
    # unavailable — we must NOT let those transient values corrupt the cache.
    sleeping_sensor_eids = set()
    for probe_id, probe in probes.items():
        if not _probe_awake_cache.get(probe_id, True):
            # Probe is known to be sleeping — protect its depth sensors
            for eid in probe.get("sensors", {}).values():
                if eid:
                    sleeping_sensor_eids.add(eid)

    state_lookup = {}
    for s in all_states:
        eid = s.get("entity_id", "")
        raw = s.get("state", "unknown")
        try:
            numeric = float(raw)
        except (ValueError, TypeError):
            numeric = None

        # Determine if this is a valid (non-unavailable) state.
        # Binary sensors and switches report "on"/"off" which aren't numeric
        # but are still valid states that should be cached (e.g. solar_charging,
        # sleep_disabled).
        is_valid = raw not in ("unavailable", "unknown")
        is_binary = numeric is None and is_valid

        # If the probe is sleeping and we have a cached value, always use cache
        # This prevents transient 0-values during sleep transitions from
        # overwriting good cached readings
        if eid in sleeping_sensor_eids and eid in _sensor_cache:
            cached = _sensor_cache[eid]
            state_lookup[eid] = {
                "state": cached["state"],
                "raw_state": cached.get("raw_state", str(cached["state"])),
                "last_updated": cached.get("last_updated", ""),
                "friendly_name": cached.get("friendly_name", eid),
                "unit": cached.get("unit", ""),
                "cached": True,
            }
        elif numeric is not None and is_valid:
            # Good numeric reading from awake probe — update the cache
            _sensor_cache[eid] = {
                "state": numeric,
                "raw_state": raw,
                "last_updated": s.get("last_updated", ""),
                "friendly_name": s.get("attributes", {}).get("friendly_name", eid),
                "unit": s.get("attributes", {}).get("unit_of_measurement", ""),
            }
            cache_dirty = True
            state_lookup[eid] = {
                "state": numeric,
                "raw_state": raw,
                "last_updated": s.get("last_updated", ""),
                "friendly_name": s.get("attributes", {}).get("friendly_name", eid),
                "unit": s.get("attributes", {}).get("unit_of_measurement", ""),
                "cached": False,
            }
        elif is_binary:
            # Valid non-numeric state (binary_sensor on/off, switch on/off)
            # Cache so we retain it when the device goes to sleep
            _sensor_cache[eid] = {
                "state": raw,
                "raw_state": raw,
                "last_updated": s.get("last_updated", ""),
                "friendly_name": s.get("attributes", {}).get("friendly_name", eid),
                "unit": "",
            }
            cache_dirty = True
            state_lookup[eid] = {
                "state": None,
                "raw_state": raw,
                "last_updated": s.get("last_updated", ""),
                "friendly_name": s.get("attributes", {}).get("friendly_name", eid),
                "unit": "",
                "cached": False,
            }
        elif raw in ("unavailable", "unknown") and eid in _sensor_cache:
            # Device sleeping — use last-known-good cached value
            cached = _sensor_cache[eid]
            state_lookup[eid] = {
                "state": cached["state"],
                "raw_state": cached.get("raw_state", str(cached["state"])),
                "last_updated": cached.get("last_updated", ""),
                "friendly_name": cached.get("friendly_name", eid),
                "unit": cached.get("unit", ""),
                "cached": True,
            }
        else:
            # No cache available — pass through as-is
            state_lookup[eid] = {
                "state": numeric,
                "raw_state": raw,
                "last_updated": s.get("last_updated", ""),
                "friendly_name": s.get("attributes", {}).get("friendly_name", eid),
                "unit": s.get("attributes", {}).get("unit_of_measurement", ""),
                "cached": False,
            }

    if cache_dirty:
        _save_sensor_cache()

    stale_threshold = data.get("stale_reading_threshold_minutes", 120)

    # We need the REAL HA raw states for determining awake/sleeping,
    # separate from the cache-augmented state_lookup.
    live_raw_states = {}
    for s in all_states:
        live_raw_states[s.get("entity_id", "")] = s.get("state", "unknown")

    # Enrich probe data with live readings
    enriched = {}
    for probe_id, probe in probes.items():
        # Depth sensor readings
        sensors_with_readings = {}
        for depth, eid in probe.get("sensors", {}).items():
            sd = state_lookup.get(eid, {})
            sensors_with_readings[depth] = {
                "entity_id": eid,
                "value": sd.get("state"),
                "raw_state": sd.get("raw_state", "unknown"),
                "friendly_name": sd.get("friendly_name", eid),
                "last_updated": sd.get("last_updated", ""),
                "stale": _is_stale(sd.get("last_updated", ""), stale_threshold),
                "cached": sd.get("cached", False),
            }

        # Device-level sensors from stored extra_sensors entity IDs
        device_sensors = {}
        extra = probe.get("extra_sensors") or {}

        for key in ("wifi", "battery", "sleep_duration"):
            eid = extra.get(key)
            if not eid:
                continue
            sd = state_lookup.get(eid, {})
            default_unit = "dBm" if key == "wifi" else "%" if key == "battery" else "s"
            sensor_entry = {
                "value": sd.get("state"),
                "raw_state": sd.get("raw_state", "unknown"),
                "unit": sd.get("unit") or default_unit,
                "entity_id": eid,
                "friendly_name": sd.get("friendly_name", eid),
                "cached": sd.get("cached", False),
            }
            # For sleep_duration: the UI needs the REAL HA state to determine
            # awake vs sleeping, even when we provide a cached numeric value.
            if key == "sleep_duration":
                sensor_entry["live_raw_state"] = live_raw_states.get(eid, "unknown")
            device_sensors[key] = sensor_entry

        # Gophr schedule/sleep entities
        schedule_time_eids = extra.get("schedule_times", [])
        if schedule_time_eids:
            sched_list = []
            for st_eid in schedule_time_eids:
                sd = state_lookup.get(st_eid, {})
                sched_list.append({
                    "entity_id": st_eid,
                    "value": sd.get("raw_state", "unknown"),
                    "friendly_name": sd.get("friendly_name", st_eid),
                })
            device_sensors["schedule_times"] = sched_list

        for skey in ("sleep_disabled", "min_awake_minutes", "max_awake_minutes", "solar_charging"):
            s_eid = extra.get(skey)
            if not s_eid:
                continue
            sd = state_lookup.get(s_eid, {})
            entry = {
                "entity_id": s_eid,
                "value": sd.get("raw_state", "unknown"),
                "friendly_name": sd.get("friendly_name", s_eid),
                "live_raw_state": live_raw_states.get(s_eid, "unknown"),
            }
            device_sensors[skey] = entry

        # Awake status: use the live status LED state we already fetched
        status_led_eid = extra.get("status_led")
        if status_led_eid and status_led_eid in live_raw_states:
            led_raw = live_raw_states[status_led_eid].lower()
            awake = led_raw == "on"
            _probe_awake_cache[probe_id] = awake
        elif probe_id not in _probe_awake_cache:
            awake = await _check_probe_awake(probe_id)
        else:
            awake = _probe_awake_cache[probe_id]

        # Add status_led data to device_sensors for next-wake calculation.
        # The UI uses last_changed (when the LED flipped OFF = fell asleep)
        # plus sleep_duration to project the next wake time.
        if status_led_eid:
            # Find the raw HA state object for last_changed
            led_ha_state = None
            for s in all_states:
                if s.get("entity_id") == status_led_eid:
                    led_ha_state = s
                    break
            led_entry = {
                "entity_id": status_led_eid,
                "value": live_raw_states.get(status_led_eid, "unknown"),
                "friendly_name": (led_ha_state or {}).get("attributes", {}).get("friendly_name", status_led_eid),
            }
            if led_ha_state:
                led_entry["last_changed"] = led_ha_state.get("last_changed", "")
                led_entry["last_updated"] = led_ha_state.get("last_updated", "")
            device_sensors["status_led"] = led_entry

        enriched[probe_id] = {
            **probe,
            "sensors_live": sensors_with_readings,
            "device_sensors": device_sensors,
            "is_awake": awake,
        }

    return {
        "enabled": data.get("enabled", False),
        "probes": enriched,
        "total": len(enriched),
    }


@router.post("/probes", summary="Add a new moisture probe")
async def api_add_probe(body: ProbeCreateRequest, request: Request):
    """Add a new moisture probe with sensor mappings and zone assignments."""
    data = _load_data()

    if body.probe_id in data.get("probes", {}):
        raise HTTPException(status_code=409, detail=f"Probe '{body.probe_id}' already exists")

    # Validate sensor entity IDs exist
    sensor_ids = [eid for eid in body.sensors.values() if eid]
    if sensor_ids:
        states = await ha_client.get_entities_by_ids(sensor_ids)
        found_ids = {s["entity_id"] for s in states}
        missing = [eid for eid in sensor_ids if eid not in found_ids]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Sensor entities not found: {missing}",
            )

    probe = {
        "probe_id": body.probe_id,
        "display_name": body.display_name or body.probe_id,
        "device_id": body.device_id,
        "sensors": body.sensors,
        "extra_sensors": body.extra_sensors or {},
        "zone_mappings": body.zone_mappings,
        "thresholds": body.thresholds,
    }

    data.setdefault("probes", {})[body.probe_id] = probe
    _save_data(data)

    log_change(get_actor(request), "Moisture Probes",
               f"Added probe: {probe['display_name']}")

    # Recalculate schedule timeline immediately (new probe may have zone mappings)
    if probe.get("zone_mappings"):
        try:
            await calculate_irrigation_timeline()
        except Exception as e:
            print(f"[MOISTURE] Timeline recalc after probe create failed: {e}")

    return {"success": True, "probe": probe}


@router.put("/probes/{probe_id}", summary="Update a moisture probe")
async def api_update_probe(probe_id: str, body: ProbeUpdateRequest, request: Request):
    """Update display name, thresholds, sensor mappings, or zone assignments."""
    data = _load_data()

    if probe_id not in data.get("probes", {}):
        raise HTTPException(status_code=404, detail=f"Probe '{probe_id}' not found")

    probe = data["probes"][probe_id]
    changes = []
    display = probe.get("display_name", probe_id)
    if body.display_name is not None:
        if probe.get("display_name") != body.display_name:
            changes.append(f"Name: {probe.get('display_name', '')} -> {body.display_name}")
        probe["display_name"] = body.display_name
        display = body.display_name
    if body.device_id is not None:
        probe["device_id"] = body.device_id
    if body.extra_sensors is not None:
        probe["extra_sensors"] = body.extra_sensors
    if body.sensors is not None:
        old_sensors = probe.get("sensors", {})
        if old_sensors != body.sensors:
            for depth in ("shallow", "mid", "deep"):
                ov = old_sensors.get(depth, "")
                nv = body.sensors.get(depth, "")
                if ov != nv:
                    changes.append(f"{depth.title()} sensor: {ov or '(none)'} -> {nv or '(none)'}")
        probe["sensors"] = body.sensors
    zone_mappings_changed = False
    if body.zone_mappings is not None:
        old_zones = set(probe.get("zone_mappings", []))
        new_zones = set(body.zone_mappings)
        added = new_zones - old_zones
        removed = old_zones - new_zones
        if added:
            changes.append(f"Added zones: {', '.join(sorted(added))}")
        if removed:
            changes.append(f"Removed zones: {', '.join(sorted(removed))}")
        if added or removed:
            zone_mappings_changed = True
        probe["zone_mappings"] = body.zone_mappings
    if body.thresholds is not None:
        probe["thresholds"] = body.thresholds

    _save_data(data)
    actor = get_actor(request)
    if changes:
        for change in changes:
            log_change(actor, "Moisture Probes", f"{display} — {change}")
    else:
        log_change(actor, "Moisture Probes", f"Updated probe: {display}")

    # When zone mappings change: recalculate timeline + re-apply durations
    if zone_mappings_changed:
        try:
            await calculate_irrigation_timeline()
        except Exception as e:
            print(f"[MOISTURE] Timeline recalc after zone mapping change failed: {e}")

        # Re-apply adjusted durations so stale skip/factor badges clear immediately.
        # If apply_factors is enabled, this recalculates everything from current mappings.
        # If not enabled, clean up stale adjusted_durations entries for unmapped zones.
        try:
            if data.get("apply_factors_to_schedule"):
                await apply_adjusted_durations()
            else:
                # Clear stale adjusted_durations entries for zones no longer mapped
                # to ANY probe (not just this one — another probe may still map them)
                all_mapped = set()
                for p in data.get("probes", {}).values():
                    for z in p.get("zone_mappings", []):
                        all_mapped.add(z)
                adj = data.get("adjusted_durations", {})
                stale_keys = []
                for dur_eid, adj_entry in adj.items():
                    # Match duration entity to zone entity
                    zm = re.search(r'zone[_]?(\d+)', dur_eid)
                    if zm:
                        zn = int(zm.group(1))
                        # Check if any zone entity with this number is still mapped
                        still_mapped = any(
                            re.search(r'zone[_]?(\d+)', z) and
                            int(re.search(r'zone[_]?(\d+)', z).group(1)) == zn
                            for z in all_mapped
                        )
                        if not still_mapped:
                            stale_keys.append(dur_eid)
                if stale_keys:
                    for k in stale_keys:
                        del adj[k]
                    data["adjusted_durations"] = adj
                    _save_data(data)
                    print(f"[MOISTURE] Cleared stale adjusted_durations for unmapped zones: {stale_keys}")
        except Exception as e:
            print(f"[MOISTURE] Duration re-apply after zone mapping change failed: {e}")

    return {"success": True, "probe": probe}


@router.post("/probes/{probe_id}/update-entities", summary="Re-detect and update probe entities")
async def api_update_probe_entities(probe_id: str, request: Request):
    """Re-run autodetect for an existing probe and update its sensor/extra_sensor mappings.

    This is useful when:
    - New entities are enabled in Home Assistant
    - The device was re-adopted in ESPHome
    - Entities weren't detected during initial setup (device was sleeping)
    """
    data = _load_data()

    if probe_id not in data.get("probes", {}):
        raise HTTPException(status_code=404, detail=f"Probe '{probe_id}' not found")

    probe = data["probes"][probe_id]
    device_id = probe.get("device_id")
    if not device_id:
        raise HTTPException(status_code=400, detail="Probe has no device_id — cannot re-detect entities")

    # Run autodetect for this device
    autodetect_result = await api_autodetect_device_sensors(device_id)
    new_sensors = autodetect_result.get("sensors", {})
    new_extra = autodetect_result.get("extra_sensors", {})

    changes = []
    old_sensors = probe.get("sensors", {})
    old_extra = probe.get("extra_sensors", {})

    # Update depth sensors (only if newly detected — don't clear existing ones)
    for depth in ("shallow", "mid", "deep"):
        new_eid = new_sensors.get(depth)
        old_eid = old_sensors.get(depth)
        if new_eid and new_eid != old_eid:
            old_sensors[depth] = new_eid
            changes.append(f"{depth.title()}: {old_eid or '(none)'} -> {new_eid}")
    probe["sensors"] = old_sensors

    # Update extra sensors (merge — don't overwrite existing with None)
    for key, new_val in new_extra.items():
        if new_val and new_val != old_extra.get(key):
            changes.append(f"Extra {key}: {old_extra.get(key, '(none)')} -> {new_val}")
            old_extra[key] = new_val
    probe["extra_sensors"] = old_extra

    _save_data(data)

    display_name = probe.get("display_name", probe_id)
    actor = get_actor(request)
    if changes:
        log_change(actor, "Moisture Probes", f"{display_name} — entities updated: {', '.join(changes)}")
    else:
        log_change(actor, "Moisture Probes", f"{display_name} — entity update (no changes)")

    return {
        "success": True,
        "changes": changes,
        "sensors": probe["sensors"],
        "extra_sensors": probe["extra_sensors"],
        "diagnostic": autodetect_result.get("diagnostic"),
    }


@router.delete("/probes/{probe_id}", summary="Remove a moisture probe")
async def api_delete_probe(probe_id: str, request: Request):
    """Remove a moisture probe configuration."""
    data = _load_data()

    if probe_id not in data.get("probes", {}):
        raise HTTPException(status_code=404, detail=f"Probe '{probe_id}' not found")

    display_name = data["probes"][probe_id].get("display_name", probe_id)
    had_mappings = bool(data["probes"][probe_id].get("zone_mappings"))
    del data["probes"][probe_id]
    _save_data(data)

    log_change(get_actor(request), "Moisture Probes",
               f"Removed probe: {display_name}")

    # Recalculate schedule timeline and re-apply durations (removed probe's mappings are gone)
    if had_mappings:
        try:
            await calculate_irrigation_timeline()
        except Exception as e:
            print(f"[MOISTURE] Timeline recalc after probe delete failed: {e}")
        try:
            if data.get("apply_factors_to_schedule"):
                await apply_adjusted_durations()
            else:
                # Clear stale adjusted_durations entries for zones no longer mapped
                all_mapped = set()
                for p in data.get("probes", {}).values():
                    for z in p.get("zone_mappings", []):
                        all_mapped.add(z)
                adj = data.get("adjusted_durations", {})
                stale_keys = []
                for dur_eid, adj_entry in adj.items():
                    zm = re.search(r'zone[_]?(\d+)', dur_eid)
                    if zm:
                        zn = int(zm.group(1))
                        still_mapped = any(
                            re.search(r'zone[_]?(\d+)', z) and
                            int(re.search(r'zone[_]?(\d+)', z).group(1)) == zn
                            for z in all_mapped
                        )
                        if not still_mapped:
                            stale_keys.append(dur_eid)
                if stale_keys:
                    for k in stale_keys:
                        del adj[k]
                    data["adjusted_durations"] = adj
                    _save_data(data)
                    print(f"[MOISTURE] Cleared stale adjusted_durations for unmapped zones: {stale_keys}")
        except Exception as e:
            print(f"[MOISTURE] Duration cleanup after probe delete failed: {e}")

    return {"success": True, "message": f"Probe '{probe_id}' removed"}


class SleepDurationRequest(BaseModel):
    minutes: float = Field(..., ge=0.5, le=120, description="Sleep duration in minutes (0.5-120)")


@router.put("/probes/{probe_id}/sleep-duration", summary="Set probe sleep duration")
async def api_set_sleep_duration(probe_id: str, body: SleepDurationRequest, request: Request):
    """Set the sleep duration for a Gophr probe.

    If the probe is currently awake, the value is written immediately.
    If the probe is asleep, the value is stored as pending
    and will be applied automatically when the probe next wakes up.
    """
    data = _load_data()
    probe = data.get("probes", {}).get(probe_id)
    if not probe:
        raise HTTPException(status_code=404, detail=f"Probe '{probe_id}' not found")

    display_name = probe.get("display_name", probe_id)

    # Check status LED to determine if device is reachable
    is_awake = await _check_probe_awake(probe_id)

    if is_awake:
        # Write immediately (device expects minutes)
        success = await _set_probe_sleep_duration(probe_id, body.minutes)
        if success:
            # Clear any pending value
            probe["pending_sleep_duration"] = None
            # Update sensor cache so UI shows the new value immediately
            sleep_sensor_eid = (probe.get("extra_sensors") or {}).get("sleep_duration")
            if sleep_sensor_eid:
                _load_sensor_cache()
                _sensor_cache[sleep_sensor_eid] = {
                    "state": float(body.minutes),
                    "raw_state": str(body.minutes),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "friendly_name": sleep_sensor_eid,
                }
                _save_sensor_cache()
            _save_data(data)
            log_change(get_actor(request), "Moisture Probes",
                       f"Set sleep duration for {display_name}: {body.minutes} min (applied immediately)")
            # Recalculate timeline (prep timing depends on sleep duration)
            if probe.get("zone_mappings"):
                try:
                    await calculate_irrigation_timeline()
                except Exception:
                    pass
            return {
                "success": True,
                "status": "applied",
                "message": f"Sleep duration set to {body.minutes} min",
                "minutes": body.minutes,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to write sleep duration to device")
    else:
        # Store as pending (in minutes — same unit as device)
        probe["pending_sleep_duration"] = body.minutes
        _save_data(data)
        log_change(get_actor(request), "Moisture Probes",
                   f"Queued sleep duration for {display_name}: {body.minutes} min (pending wake)")
        # Recalculate timeline with pending value (prep timing depends on sleep duration)
        if probe.get("zone_mappings"):
            try:
                await calculate_irrigation_timeline()
            except Exception:
                pass
        return {
            "success": True,
            "status": "pending",
            "message": f"Sleep duration {body.minutes} min queued — will apply when probe wakes",
            "minutes": body.minutes,
        }


class SleepDisabledRequest(BaseModel):
    disabled: bool = Field(..., description="True to disable sleep (keep probe awake), False to allow sleeping")


@router.put("/probes/{probe_id}/sleep-disabled", summary="Toggle probe sleep disabled")
async def api_set_sleep_disabled(probe_id: str, body: SleepDisabledRequest, request: Request):
    """Enable or disable sleep on a Gophr probe.

    If the probe is currently awake, the toggle is applied immediately.
    If the probe is asleep (unavailable), the value is stored as pending
    and will be applied automatically when the probe next wakes up.
    """
    data = _load_data()
    probe = data.get("probes", {}).get(probe_id)
    if not probe:
        raise HTTPException(status_code=404, detail=f"Probe '{probe_id}' not found")

    display_name = probe.get("display_name", probe_id)

    # Check status LED to determine if device is reachable
    is_awake = await _check_probe_awake(probe_id)

    if is_awake:
        success = await set_probe_sleep_disabled(probe_id, body.disabled)
        if success:
            probe["pending_sleep_disabled"] = None
            _save_data(data)
            action = "disabled" if body.disabled else "enabled"
            log_change(get_actor(request), "Moisture Probes",
                       f"Sleep {action} for {display_name} (applied immediately)")
            return {
                "success": True,
                "status": "applied",
                "message": f"Sleep {action} for {display_name}",
                "disabled": body.disabled,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to toggle sleep disabled on device")
    else:
        probe["pending_sleep_disabled"] = body.disabled
        _save_data(data)
        action = "disable" if body.disabled else "enable"
        log_change(get_actor(request), "Moisture Probes",
                   f"Queued sleep {action} for {display_name} (pending wake)")
        return {
            "success": True,
            "status": "pending",
            "message": f"Sleep {action} queued — will apply when probe wakes",
            "disabled": body.disabled,
        }


@router.post("/probes/{probe_id}/sleep-now", summary="Force probe to sleep immediately")
async def api_press_sleep_now(probe_id: str, request: Request):
    """Press the sleep_now button on a Gophr probe to force it to sleep immediately.

    Useful for precise wake timing — set the desired sleep_duration first,
    then press sleep_now to start the countdown immediately.
    The probe must be awake for this to work.
    """
    data = _load_data()
    probe = data.get("probes", {}).get(probe_id)
    if not probe:
        raise HTTPException(status_code=404, detail=f"Probe '{probe_id}' not found")

    sleep_now_eid = (probe.get("extra_sensors") or {}).get("sleep_now")
    if not sleep_now_eid:
        raise HTTPException(status_code=400, detail="No sleep_now button entity detected for this probe")

    display_name = probe.get("display_name", probe_id)

    success = await press_probe_sleep_now(probe_id)
    if success:
        # Immediately mark probe as sleeping in cache so UI updates instantly
        _probe_awake_cache[probe_id] = False
        log_change(get_actor(request), "Moisture Probes",
                   f"Sleep Now pressed for {display_name}")
        return {
            "success": True,
            "message": f"Sleep Now pressed for {display_name} — probe will sleep immediately",
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to press sleep_now button on device")


@router.post("/probes/{probe_id}/calibrate", summary="Press calibration buttons on probe")
async def api_calibrate_probe(probe_id: str, body: CalibrateRequest, request: Request):
    """Press all 3 calibrate dry or calibrate wet buttons on a Gophr probe.

    The probe must be awake and sleep must be disabled for calibration to work.
    action: "dry" presses all 3 dry calibration buttons simultaneously.
    action: "wet" presses all 3 wet calibration buttons simultaneously.
    """
    if body.action not in ("dry", "wet"):
        raise HTTPException(status_code=400, detail="action must be 'dry' or 'wet'")

    data = _load_data()
    probe = data.get("probes", {}).get(probe_id)
    if not probe:
        raise HTTPException(status_code=404, detail=f"Probe '{probe_id}' not found")

    extra = probe.get("extra_sensors") or {}
    key = f"calibrate_{body.action}"
    button_eids = extra.get(key, [])

    if not button_eids:
        raise HTTPException(
            status_code=400,
            detail=f"No {body.action} calibration buttons detected for this probe"
        )

    # Press all calibration buttons for the requested action
    results = []
    for eid in button_eids:
        success = await ha_client.call_service("button", "press", {
            "entity_id": eid,
        })
        results.append({"entity_id": eid, "success": success})
        print(f"[MOISTURE] Calibrate {body.action} pressed: {eid} -> "
              f"{'OK' if success else 'FAILED'}")

    all_ok = all(r["success"] for r in results)
    display_name = probe.get("display_name", probe_id)

    if all_ok:
        log_change(get_actor(request), "Moisture Probes",
                   f"Calibrate {body.action} pressed for {display_name} "
                   f"({len(button_eids)} sensors)")
        return {
            "success": True,
            "action": body.action,
            "message": f"Calibrate {body.action} pressed for all "
                       f"{len(button_eids)} sensors on {display_name}",
            "buttons_pressed": len(button_eids),
        }
    else:
        failed = [r["entity_id"] for r in results if not r["success"]]
        raise HTTPException(
            status_code=500,
            detail=f"Some calibration buttons failed: {failed}"
        )


@router.get("/settings", summary="Get moisture probe settings")
async def api_get_settings():
    """Get global moisture probe settings."""
    data = _load_data()
    return {
        "enabled": data.get("enabled", False),
        "apply_factors_to_schedule": data.get("apply_factors_to_schedule", False),
        "schedule_sync_enabled": data.get("schedule_sync_enabled", True),
        "multi_probe_mode": data.get("multi_probe_mode", "conservative"),
        "stale_reading_threshold_minutes": data.get("stale_reading_threshold_minutes", 120),
        "depth_weights": data.get("depth_weights", DEFAULT_DATA["depth_weights"]),
        "default_thresholds": data.get("default_thresholds", DEFAULT_DATA["default_thresholds"]),
    }


@router.put("/settings", summary="Update moisture probe settings")
async def api_update_settings(body: MoistureSettingsRequest, request: Request):
    """Update global moisture settings (enable/disable, stale threshold, weights, defaults)."""
    data = _load_data()

    # Build changelog description with old → new values
    changes = []
    if body.enabled is not None:
        old = data.get("enabled", False)
        data["enabled"] = body.enabled
        if old != body.enabled:
            changes.append(f"Moisture probes: {'Disabled' if old else 'Enabled'} -> {'Enabled' if body.enabled else 'Disabled'}")
    if body.stale_reading_threshold_minutes is not None:
        old = data.get("stale_reading_threshold_minutes", 120)
        if old != body.stale_reading_threshold_minutes:
            changes.append(f"Stale reading threshold: {old} -> {body.stale_reading_threshold_minutes} min")
        data["stale_reading_threshold_minutes"] = body.stale_reading_threshold_minutes
    if body.depth_weights is not None:
        old = data.get("depth_weights", DEFAULT_DATA["depth_weights"])
        if old != body.depth_weights:
            for wk in ("shallow", "mid", "deep"):
                ov = old.get(wk)
                nv = body.depth_weights.get(wk)
                if ov != nv:
                    changes.append(f"Depth weight {wk}: {ov} -> {nv}")
        data["depth_weights"] = body.depth_weights
    if body.default_thresholds is not None:
        old_thresh = data.get("default_thresholds", DEFAULT_DATA["default_thresholds"])
        thresh_labels = {
            "root_zone_skip": "Root Zone Skip (%)",
            "root_zone_wet": "Root Zone Wet (%)",
            "root_zone_optimal": "Root Zone Optimal (%)",
            "root_zone_dry": "Root Zone Dry (%)",
            "max_increase_percent": "Max Increase (%)",
            "max_decrease_percent": "Max Decrease (%)",
            "rain_boost_threshold": "Rain Boost Threshold",
        }
        for tk in set(list(old_thresh.keys()) + list(body.default_thresholds.keys())):
            ov = old_thresh.get(tk)
            nv = body.default_thresholds.get(tk)
            if ov != nv:
                label = thresh_labels.get(tk, tk.replace("_", " ").title())
                changes.append(f"{label}: {ov} -> {nv}")
        data["default_thresholds"] = body.default_thresholds

    # Handle apply_factors_to_schedule toggle
    if body.apply_factors_to_schedule is not None:
        was_enabled = data.get("apply_factors_to_schedule", False)
        currently_active = data.get("duration_adjustment_active", False)
        data["apply_factors_to_schedule"] = body.apply_factors_to_schedule
        _save_data(data)

        if body.apply_factors_to_schedule != was_enabled:
            changes.append(f"Apply Factors to Schedule: {'Enabled' if was_enabled else 'Disabled'} -> {'Enabled' if body.apply_factors_to_schedule else 'Disabled'}")

        if changes:
            actor = get_actor(request)
            for change in changes:
                log_change(actor, "Moisture Probes", change)

        # Re-apply if enabling (or re-enabling after a failed attempt)
        if body.apply_factors_to_schedule and (not was_enabled or not currently_active):
            # Toggling ON: always re-capture base durations for fresh values
            capture_result = await capture_base_durations()
            captured = capture_result.get("captured", 0)
            print(f"[MOISTURE] Toggle ON: captured {captured} base durations")
            if captured == 0:
                # No duration entities found — report with diagnostic details
                config = get_config()
                all_ctrl = config.allowed_control_entities
                number_ents = [e for e in all_ctrl if e.startswith("number.")]
                print(f"[MOISTURE] Toggle ON FAILED: "
                      f"control_entities={all_ctrl}, number_ents={number_ents}")
                detail = ""
                if not all_ctrl:
                    detail = " — no control entities configured (device may need re-selection)"
                elif not number_ents:
                    detail = f" — {len(all_ctrl)} control entities but none are number.* entities"
                else:
                    detail = f" — number.* entities found: {number_ents}"
                return {
                    "success": False,
                    "message": f"No duration entities found{detail}",
                    "applied": 0,
                }
            result = await apply_adjusted_durations()
            applied = result.get("applied", 0)
            reason = result.get("reason", "")
            msg = f"Factors applied to {applied} zone(s)"
            if applied == 0 and reason:
                msg = f"Apply failed: {reason}"
            print(f"[MOISTURE] Toggle ON: apply result: applied={applied}, reason={reason}")
            return {
                "success": applied > 0,
                "message": msg,
                "applied": applied,
            }
        elif not body.apply_factors_to_schedule and (was_enabled or currently_active):
            # Toggling OFF: restore base durations
            result = await restore_base_durations()
            restored = result.get("restored", 0)
            return {
                "success": True,
                "message": f"Original durations restored for {restored} zone(s)",
                "restored": restored,
            }

    # Handle multi_probe_mode
    VALID_MULTI_PROBE_MODES = ("conservative", "average", "optimistic")
    if body.multi_probe_mode is not None:
        mode = body.multi_probe_mode.lower().strip()
        if mode in VALID_MULTI_PROBE_MODES:
            old_mode = data.get("multi_probe_mode", "conservative")
            if old_mode != mode:
                labels = {
                    "conservative": "Conservative (wettest)",
                    "average": "Average",
                    "optimistic": "Optimistic (driest)",
                }
                changes.append(
                    f"Multi-probe mode: {labels.get(old_mode, old_mode)} -> {labels.get(mode, mode)}"
                )
            data["multi_probe_mode"] = mode

    # Handle schedule_sync_enabled toggle
    if body.schedule_sync_enabled is not None:
        old_sync = data.get("schedule_sync_enabled", True)
        data["schedule_sync_enabled"] = body.schedule_sync_enabled
        if old_sync != body.schedule_sync_enabled:
            changes.append(
                f"Schedule sync: {'Enabled' if body.schedule_sync_enabled else 'Disabled'}"
            )

    _save_data(data)
    if changes:
        actor = get_actor(request)
        for change in changes:
            log_change(actor, "Moisture Probes", change)
    return {"success": True, "message": "Moisture settings updated"}


async def calculate_overall_moisture_multiplier() -> dict:
    """Calculate an overall moisture multiplier across all configured probes.

    Uses the same gradient-based algorithm as zone-level calculations:
      - Mid (root zone): PRIMARY decision driver
      - Shallow (surface): Rain detection signal
      - Deep (reserve): Over-irrigation / reserve guard

    Returns:
        {
            "moisture_multiplier": float,
            "avg_moisture": float or None,
            "probe_count": int,
            "reason": str,
            "profile": str,
            "rain_detected": bool,
        }
    """
    data = _load_data()

    if not data.get("enabled"):
        return {
            "moisture_multiplier": 1.0,
            "avg_moisture": None,
            "probe_count": 0,
            "reason": "Moisture probes not enabled",
        }

    probes = data.get("probes", {})
    if not probes:
        return {
            "moisture_multiplier": 1.0,
            "avg_moisture": None,
            "probe_count": 0,
            "reason": "No probes configured",
        }

    sensor_states = await _get_probe_sensor_states(probes)
    stale_threshold = data.get("stale_reading_threshold_minutes", 120)
    default_thresholds = data.get("default_thresholds", DEFAULT_DATA["default_thresholds"])

    # Get weather context for rain detection
    precip_probability = _get_precipitation_probability()
    weather_condition = _get_weather_condition()

    probe_multipliers = []
    mid_values = []
    any_skip = False
    all_reasons = []
    profiles = []
    rain_detected = False

    for probe_id, probe in probes.items():
        sensors = probe.get("sensors", {})
        thresholds = probe.get("thresholds") or default_thresholds

        # Build depth readings dict
        depth_readings = {}
        for depth in ("shallow", "mid", "deep"):
            sensor_eid = sensors.get(depth)
            if not sensor_eid:
                continue
            sensor_data = sensor_states.get(sensor_eid, {})
            value = sensor_data.get("state")
            last_updated = sensor_data.get("last_updated", "")
            stale = _is_stale(last_updated, stale_threshold)

            if value is not None and not stale:
                depth_readings[depth] = {
                    "value": value,
                    "stale": False,
                    "entity_id": sensor_eid,
                }
            else:
                depth_readings[depth] = {
                    "value": value,
                    "stale": stale,
                    "entity_id": sensor_eid,
                    "reason": "stale" if stale else "unavailable",
                }

        # Run gradient analysis
        result = _analyze_probe_gradient(
            depth_readings, thresholds, precip_probability, weather_condition,
        )

        if result["skip"]:
            any_skip = True
        if result["multiplier"] is not None:
            probe_multipliers.append(result["multiplier"])
        if result.get("mid_value") is not None:
            mid_values.append(result["mid_value"])
        if result.get("rain_detected"):
            rain_detected = True

        profiles.append(result.get("profile", "unknown"))
        all_reasons.append(f"{probe.get('display_name', probe_id)}: {result['reason']}")

    if not probe_multipliers:
        return {
            "moisture_multiplier": 1.0,
            "avg_moisture": None,
            "probe_count": len(probes),
            "reason": "All probe readings are stale or unavailable",
        }

    # Use minimum multiplier across probes (most conservative)
    if any_skip:
        final_multiplier = 0.0
    else:
        final_multiplier = min(probe_multipliers)

    # Display moisture: mid sensor average
    avg_moisture = sum(mid_values) / len(mid_values) if mid_values else None

    return {
        "moisture_multiplier": round(max(final_multiplier, 0.0), 3),
        "avg_moisture": round(avg_moisture, 1) if avg_moisture is not None else None,
        "probe_count": len(probes),
        "reason": "; ".join(all_reasons),
        "profile": profiles[0] if len(profiles) == 1 else "multi-probe",
        "rain_detected": rain_detected,
    }


@router.get("/multiplier", summary="Get per-zone moisture multipliers")
async def api_overall_multiplier():
    """Get moisture multipliers for all zones with mapped probes.

    Returns weather multiplier (system-wide) and per-zone moisture
    multipliers.  Zones without mapped probes are not listed in
    per_zone — the frontend should default them to weather-only.
    """
    data = _load_data()
    config = get_config()
    weather_mult = get_weather_multiplier()

    if not data.get("enabled"):
        return {
            "weather_multiplier": weather_mult,
            "moisture_enabled": False,
            "per_zone": {},
        }

    probes = data.get("probes", {})
    sensor_states = await _get_probe_sensor_states(probes)

    # Build per-zone multipliers for all zones that have mapped probes
    per_zone = {}
    mapped_zone_eids = set()
    for probe_id, probe in probes.items():
        for zone_eid in probe.get("zone_mappings", []):
            mapped_zone_eids.add(zone_eid)

    for zone_eid in mapped_zone_eids:
        zone_result = calculate_zone_moisture_multiplier(
            zone_eid, data, sensor_states,
        )
        moisture_mult = zone_result.get("multiplier", 1.0)
        skip = zone_result.get("skip", False)
        combined = round(weather_mult * moisture_mult, 3) if not skip else 0.0
        per_zone[zone_eid] = {
            "moisture_multiplier": moisture_mult,
            "combined": combined,
            "skip": skip,
            "reason": zone_result.get("reason", ""),
        }

    return {
        "weather_multiplier": weather_mult,
        "moisture_enabled": True,
        "per_zone": per_zone,
    }


@router.post("/zones/{zone_id}/multiplier", summary="Preview zone moisture multiplier")
async def api_zone_multiplier(zone_id: str):
    """Preview the moisture multiplier for a zone (no side effects).

    Returns both the moisture-only and combined (weather × moisture) multipliers.
    """
    result = await get_combined_multiplier(zone_id)
    return result


@router.post("/durations/capture", summary="Capture base durations")
async def api_capture_durations():
    """Read current number.*_run_duration entity values and save as base durations.

    These base values are what the user considers their intended run times.
    Adjusted durations are calculated relative to these base values.
    """
    result = await capture_base_durations()
    return result


@router.post("/durations/apply", summary="Apply adjusted durations")
async def api_apply_durations():
    """Compute and write adjusted durations to HA number entities.

    Uses base_duration × weather_multiplier × moisture_multiplier for each zone.
    Will not apply if zones are currently running.
    """
    result = await apply_adjusted_durations()
    if not result.get("success"):
        raise HTTPException(status_code=409, detail=result.get("reason", "Failed"))
    return result


@router.post("/durations/restore", summary="Restore base durations")
async def api_restore_durations():
    """Restore all run_duration entities to their captured base values."""
    result = await restore_base_durations()
    return result


@router.get("/durations", summary="Get duration adjustment status")
async def api_get_durations():
    """Get the current state of base vs. adjusted durations."""
    data = _load_data()
    return {
        "duration_adjustment_active": data.get("duration_adjustment_active", False),
        "base_durations": data.get("base_durations", {}),
        "adjusted_durations": data.get("adjusted_durations", {}),
        "last_evaluation": data.get("last_evaluation"),
        "last_evaluation_result": data.get("last_evaluation_result", {}),
    }


# --- Gophr Sleep/Wake Schedule Sync ---

# Track active mid-run moisture monitoring tasks
_active_moisture_monitors: dict[str, asyncio.Task] = {}

# Track original sleep durations for restoration after last mapped zone
_original_sleep_durations: dict[str, int] = {}  # probe_id -> original minutes

# Deferred factor re-application: set when apply_adjusted_durations() is blocked
# by running zones.  When the last zone turns off, on_zone_state_change() picks
# this up and re-applies.
_deferred_factor_apply: bool = False


async def sync_schedule_times_to_probes() -> dict:
    """Sync irrigation controller start times to Gophr schedule_time entities.

    Reads the irrigation controller's text.*_start_time_* entities,
    then writes matching values to each Gophr probe's schedule_time text
    entities so the device wakes before irrigation runs.

    Returns summary of sync operations.
    """
    data = _load_data()

    if not data.get("schedule_sync_enabled", True):
        return {"success": True, "synced": 0, "reason": "Schedule sync disabled"}

    config = get_config()
    probes = data.get("probes", {})

    if not probes:
        return {"success": True, "synced": 0, "reason": "No probes configured"}

    # Find probes with schedule_times in extra_sensors
    probes_with_schedules = {}
    for probe_id, probe in probes.items():
        sched_eids = (probe.get("extra_sensors") or {}).get("schedule_times", [])
        if sched_eids:
            probes_with_schedules[probe_id] = sched_eids

    if not probes_with_schedules:
        return {"success": True, "synced": 0, "reason": "No probes with schedule_time entities"}

    # Get irrigation controller start times
    start_time_eids = [
        eid for eid in config.allowed_control_entities
        if eid.startswith("text.") and "start_time" in eid.lower()
    ]
    start_time_eids.sort(key=lambda e: int(m.group(1)) if (m := re.search(r'(\d+)', e.split("start_time")[-1])) else 99)

    # Fetch current start time values
    irrigation_times = []
    if start_time_eids:
        states = await ha_client.get_entities_by_ids(start_time_eids)
        for s in states:
            val = s.get("state", "")
            if val and val not in ("unknown", "unavailable"):
                irrigation_times.append(val)

    print(f"[MOISTURE] Schedule sync: {len(irrigation_times)} irrigation start times, "
          f"{len(probes_with_schedules)} probes with schedule entities")

    synced_count = 0
    details = []

    for probe_id, gophr_sched_eids in probes_with_schedules.items():
        probe_synced = []
        for i, gophr_eid in enumerate(gophr_sched_eids):
            # Map irrigation start time to Gophr schedule slot
            new_val = irrigation_times[i] if i < len(irrigation_times) else "00:00"
            success = await ha_client.call_service("text", "set_value", {
                "entity_id": gophr_eid,
                "value": str(new_val),
            })
            if success:
                probe_synced.append(f"{gophr_eid} = {new_val}")
                synced_count += 1
            else:
                probe_synced.append(f"{gophr_eid} FAILED")

        details.append({
            "probe_id": probe_id,
            "synced": probe_synced,
        })
        print(f"[MOISTURE] Schedule sync for {probe_id}: {probe_synced}")

    # Store last sync time
    data["last_schedule_sync"] = datetime.now(timezone.utc).isoformat()
    _save_data(data)

    return {
        "success": synced_count > 0,
        "synced": synced_count,
        "irrigation_times": irrigation_times,
        "details": details,
    }


async def set_probe_sleep_disabled(probe_id: str, disabled: bool) -> bool:
    """Enable or disable sleep on a Gophr probe.

    Args:
        probe_id: The probe identifier
        disabled: True to disable sleep (keep awake), False to re-enable sleep

    Returns True if the service call succeeded.
    """
    data = _load_data()
    probe = data.get("probes", {}).get(probe_id)
    if not probe:
        print(f"[MOISTURE] set_probe_sleep_disabled: probe {probe_id} not found")
        return False

    sleep_switch_eid = (probe.get("extra_sensors") or {}).get("sleep_disabled")
    if not sleep_switch_eid:
        print(f"[MOISTURE] set_probe_sleep_disabled: no sleep_disabled switch for {probe_id}")
        return False

    svc = "turn_on" if disabled else "turn_off"
    success = await ha_client.call_service("switch", svc, {
        "entity_id": sleep_switch_eid,
    })
    print(f"[MOISTURE] Sleep {'disabled' if disabled else 'enabled'} for {probe_id} "
          f"({sleep_switch_eid}): {'OK' if success else 'FAILED'}")
    return success


async def press_probe_sleep_now(probe_id: str) -> bool:
    """Press the sleep_now button on a Gophr probe to force it to sleep immediately.

    Useful for precise wake timing control — set the desired sleep_duration first,
    then press sleep_now to start the countdown immediately instead of waiting for
    the device's natural sleep cycle.

    Returns True if the service call succeeded.
    """
    data = _load_data()
    probe = data.get("probes", {}).get(probe_id)
    if not probe:
        print(f"[MOISTURE] press_probe_sleep_now: probe {probe_id} not found")
        return False

    sleep_now_eid = (probe.get("extra_sensors") or {}).get("sleep_now")
    if not sleep_now_eid:
        print(f"[MOISTURE] press_probe_sleep_now: no sleep_now button for {probe_id}")
        return False

    success = await ha_client.call_service("button", "press", {
        "entity_id": sleep_now_eid,
    })
    print(f"[MOISTURE] Sleep Now pressed for {probe_id} ({sleep_now_eid}): "
          f"{'OK' if success else 'FAILED'}")
    return success


async def monitor_zone_moisture(zone_entity_id: str, probe_id: str):
    """Monitor moisture during an active zone run.

    Polls the probe's sensor readings every 30 seconds while the zone is running.
    If moisture exceeds the skip threshold:
    1. Turns off the current zone
    2. Finds the next enabled zone in execution order
    3. Enables auto advance
    4. Starts the next zone so the cycle continues
    """
    import run_log

    data = _load_data()
    probe = data.get("probes", {}).get(probe_id)
    if not probe:
        return

    zone_name = zone_entity_id  # Fallback, will be resolved later

    print(f"[MOISTURE] Starting mid-run monitor: zone={zone_entity_id}, probe={probe_id}")

    try:
        while True:
            await asyncio.sleep(30)

            # Check if zone is still running
            zone_states = await ha_client.get_entities_by_ids([zone_entity_id])
            if not zone_states or zone_states[0].get("state") not in ("on", "open"):
                print(f"[MOISTURE] Mid-run monitor: zone {zone_entity_id} no longer running")
                break

            # Get fresh sensor readings (bypass cache for real-time)
            fresh_data = _load_data()
            fresh_probe = fresh_data.get("probes", {}).get(probe_id)
            if not fresh_probe:
                break

            sensor_states = await _get_probe_sensor_states({probe_id: fresh_probe})

            # Check moisture level using zone-specific multiplier
            zone_result = calculate_zone_moisture_multiplier(
                zone_entity_id, fresh_data, sensor_states,
            )

            if zone_result.get("skip"):
                # Moisture exceeded threshold — shut off zone and advance
                domain = zone_entity_id.split(".")[0] if "." in zone_entity_id else "switch"
                svc = "close" if domain == "valve" else "turn_off"
                await ha_client.call_service(domain, svc, {"entity_id": zone_entity_id})

                # Resolve zone name for logging
                attrs = zone_states[0].get("attributes", {}) if zone_states else {}
                zone_name = attrs.get("friendly_name", zone_entity_id)

                run_log.log_zone_event(
                    entity_id=zone_entity_id,
                    state="off",
                    source="moisture_cutoff",
                    zone_name=zone_name,
                )
                print(f"[MOISTURE] Mid-run cutoff: {zone_entity_id} — moisture exceeded threshold "
                      f"(mult={zone_result.get('multiplier')}, reason={zone_result.get('reason')})")

                # --- Skip-and-Advance: start the next zone ---
                await _advance_to_next_zone(zone_entity_id)
                break
            else:
                mult = zone_result.get("multiplier", 1.0)
                print(f"[MOISTURE] Mid-run check: {zone_entity_id} moisture OK (mult={mult:.2f})")

    except asyncio.CancelledError:
        print(f"[MOISTURE] Mid-run monitor cancelled: {zone_entity_id}")
    except Exception as e:
        print(f"[MOISTURE] Mid-run monitor error: {zone_entity_id}: {e}")
    finally:
        # Clean up from active monitors dict
        _active_moisture_monitors.pop(zone_entity_id, None)
        # NOTE: Sleep re-enable is handled by on_zone_state_change()
        # which runs the dynamic mid-run sleep calculation
        print(f"[MOISTURE] Mid-run monitor ended: {zone_entity_id}")


async def _advance_to_next_zone(current_zone_eid: str):
    """Find the next enabled zone and start it with auto advance enabled.

    Called when a zone is shut off early due to saturation. Enables auto advance
    so the remaining zones continue running after the next zone finishes.
    """
    import run_log

    config = get_config()

    # Get the ordered zone execution sequence
    ordered_zones = await _get_ordered_enabled_zones()
    if not ordered_zones:
        print(f"[MOISTURE] Advance: no ordered zones found")
        return

    # Find current zone's position
    current_idx = None
    for i, z in enumerate(ordered_zones):
        if z["zone_entity_id"] == current_zone_eid:
            current_idx = i
            break

    if current_idx is None or current_idx + 1 >= len(ordered_zones):
        print(f"[MOISTURE] Advance: {current_zone_eid} is last zone — no advance needed")
        return

    next_zone = ordered_zones[current_idx + 1]
    next_eid = next_zone["zone_entity_id"]
    next_num = next_zone["zone_num"]

    # Enable auto advance so remaining zones continue automatically
    auto_advance_entities = [
        eid for eid in config.allowed_control_entities
        if "auto_advance" in eid.lower() and eid.startswith("switch.")
    ]
    for aa_eid in auto_advance_entities:
        await ha_client.call_service("switch", "turn_on", {"entity_id": aa_eid})
        print(f"[MOISTURE] Advance: enabled auto_advance ({aa_eid})")

    # Start the next zone
    next_domain = next_eid.split(".")[0] if "." in next_eid else "switch"
    next_svc = "open" if next_domain == "valve" else "turn_on"
    success = await ha_client.call_service(next_domain, next_svc, {"entity_id": next_eid})

    if success:
        run_log.log_zone_event(
            entity_id=next_eid,
            state="on",
            source="moisture_advance",
            zone_name=f"Zone {next_num}",
        )
        print(f"[MOISTURE] Advance: started zone {next_num} ({next_eid}), auto_advance ON")
    else:
        print(f"[MOISTURE] Advance: FAILED to start zone {next_num} ({next_eid})")


async def on_zone_state_change(zone_entity_id: str, new_state: str):
    """Called by run_log when a zone state changes.

    Handles probe sleep/wake management around irrigation runs:

    Zone ON:
        - Disable sleep on mapped probes (keep awake for moisture readings)
        - Save original sleep duration on first mapped zone activation
        - Start mid-run moisture monitoring task
        - If probe was prepped by schedule-aware logic, it's already awake

    Zone OFF:
        - Cancel moisture monitoring task
        - Check if next zone is also mapped to the same probe:
            - YES → keep probe awake (don't cycle sleep)
            - NO → calculate gap and program sleep to wake before next mapped zone
        - If no more mapped zones → restore original sleep, re-enable skipped zones,
          finish the probe prep cycle
    """
    data = _load_data()
    if not data.get("enabled"):
        return

    is_on = new_state in ("on", "open")
    is_off = new_state in ("off", "closed")

    if not (is_on or is_off):
        return

    # Load timeline for probe prep state
    timeline = _load_schedule_timeline()
    probe_prep = timeline.get("probe_prep", {}) if timeline else {}

    # Find probes mapped to this zone that have sleep control
    for probe_id, probe in data.get("probes", {}).items():
        if zone_entity_id not in probe.get("zone_mappings", []):
            continue
        sleep_switch = (probe.get("extra_sensors") or {}).get("sleep_disabled")
        if not sleep_switch:
            continue

        prep = probe_prep.get(probe_id, {})

        if is_on:
            # Zone turned on — disable sleep and start monitoring
            await set_probe_sleep_disabled(probe_id, True)

            # Save original sleep duration on FIRST mapped zone activation
            if probe_id not in _original_sleep_durations:
                extra = probe.get("extra_sensors") or {}
                sleep_sensor_eid = extra.get("sleep_duration")
                if sleep_sensor_eid:
                    try:
                        states = await ha_client.get_entities_by_ids(
                            [sleep_sensor_eid]
                        )
                        if states:
                            raw = states[0].get("state", "0")
                            if raw not in ("unavailable", "unknown"):
                                orig_val = float(raw)
                                _original_sleep_durations[probe_id] = orig_val
                                print(f"[MOISTURE] Saved original sleep duration "
                                      f"for {probe_id}: {orig_val} min")
                    except (ValueError, TypeError):
                        pass

            # Update prep state if timeline is tracking this
            if prep.get("state") in ("prep_pending", "monitoring", "sleeping_between"):
                prep["state"] = "monitoring"
                prep["active_zone_entity_id"] = zone_entity_id
                if timeline:
                    _save_schedule_timeline(timeline)

            # Start mid-run moisture monitoring
            if zone_entity_id not in _active_moisture_monitors:
                task = asyncio.create_task(
                    monitor_zone_moisture(zone_entity_id, probe_id)
                )
                _active_moisture_monitors[zone_entity_id] = task
                print(f"[MOISTURE] Zone ON → sleep disabled, monitoring started: "
                      f"{zone_entity_id} → {probe_id}")

        elif is_off:
            # Zone turned off — cancel monitoring
            task = _active_moisture_monitors.get(zone_entity_id)
            if task and not task.done():
                task.cancel()
                print(f"[MOISTURE] Zone OFF → cancelling monitor: "
                      f"{zone_entity_id}")

            # Check if the next zone is also mapped to this probe
            sleep_info = await _calculate_sleep_until_next_mapped_zone(
                probe_id, zone_entity_id
            )

            if sleep_info and sleep_info["sleep_minutes"] == 0:
                # Gap is too short or next zone is consecutive — keep awake
                print(
                    f"[MOISTURE] Zone OFF → gap too short "
                    f"({sleep_info['gap_minutes']:.1f} min), "
                    f"keeping {probe_id} awake for "
                    f"{sleep_info['next_zone_entity_id']}"
                )
                # sleep_disabled stays ON (probe stays awake)
                if prep:
                    prep["state"] = "monitoring"
                    if timeline:
                        _save_schedule_timeline(timeline)

            elif sleep_info and sleep_info["sleep_minutes"] > 0:
                # There IS a next mapped zone with a gap — sleep until ~10 min before
                sleep_mins = max(1, sleep_info["sleep_minutes"] - TARGET_WAKE_BEFORE_MINUTES)
                await _set_probe_sleep_duration(probe_id, sleep_mins)
                await set_probe_sleep_disabled(probe_id, False)
                print(
                    f"[MOISTURE] Zone OFF → mid-run sleep: {probe_id} "
                    f"will sleep {sleep_mins} min "
                    f"(wake ~{TARGET_WAKE_BEFORE_MINUTES} min before "
                    f"{sleep_info['next_zone_entity_id']}, "
                    f"gap={sleep_info['gap_minutes']:.1f} min)"
                )
                if prep:
                    prep["state"] = "prep_pending"
                    prep["active_zone_entity_id"] = sleep_info["next_zone_entity_id"]
                    if timeline:
                        _save_schedule_timeline(timeline)

            else:
                # No more mapped zones — finish the cycle
                if prep and timeline:
                    await _finish_probe_prep_cycle(probe_id, prep, timeline)
                else:
                    # No timeline tracking — simple restore
                    original = _original_sleep_durations.pop(probe_id, None)
                    if original is not None:
                        await _set_probe_sleep_duration(probe_id, original)
                        print(
                            f"[MOISTURE] Zone OFF → last mapped zone, "
                            f"restored sleep duration: {probe_id} = "
                            f"{original} min"
                        )
                    await set_probe_sleep_disabled(probe_id, False)
                    print(f"[MOISTURE] Zone OFF → sleep re-enabled: "
                          f"{probe_id}")

    # Deferred factor re-application: if apply_adjusted_durations() was blocked
    # by running zones (e.g. weather factor changed mid-run), check whether
    # ALL zones are now off after this zone-off event and re-apply.
    if is_off and _deferred_factor_apply:
        try:
            config = get_config()
            all_zones = await ha_client.get_entities_by_ids(
                config.allowed_zone_entities
            )
            still_running = [
                z for z in all_zones
                if z.get("state") in ("on", "open")
            ]
            if not still_running:
                print("[MOISTURE] All zones stopped — applying deferred "
                      "factor re-evaluation")
                await apply_adjusted_durations()
        except Exception as e:
            print(f"[MOISTURE] Deferred factor re-apply error: {e}")


async def check_skip_factor_transition(entity_id: str, new_state: str, old_state: str) -> bool:
    """Check if a probe sensor reading change causes a skip↔factor transition.

    Called by run_log when a moisture probe sensor state changes.
    Returns True if factors need to be re-evaluated (a zone went from
    skip → non-skip or non-skip → skip).
    """
    data = _load_data()
    if not data.get("enabled") or not data.get("apply_factors_to_schedule"):
        return False

    # If the NEW state is unavailable/unknown, we can't evaluate — skip
    # But if only the OLD state was unavailable (probe waking up), we MUST check
    # because the new reading may cross the skip threshold
    if new_state in ("unavailable", "unknown"):
        return False

    # Try to parse as numeric — moisture sensor values
    try:
        float(new_state)
    except (ValueError, TypeError):
        return False

    # Find which probe(s) own this sensor entity
    probes = data.get("probes", {})
    affected_zones = set()
    for probe_id, probe in probes.items():
        for depth in ("shallow", "mid", "deep"):
            if probe.get("sensors", {}).get(depth) == entity_id:
                # This probe's sensor changed — check all mapped zones
                for zone_eid in probe.get("zone_mappings", []):
                    affected_zones.add(zone_eid)
                break

    if not affected_zones:
        return False

    # Compare current vs new factor state for affected zones
    # Check if any zone's skip status would change
    adjusted = data.get("adjusted_durations", {})
    sensor_states = await _get_probe_sensor_states(probes)

    for zone_eid in affected_zones:
        # Get new factor with current sensor readings
        zone_result = calculate_zone_moisture_multiplier(
            zone_eid, data, sensor_states,
        )
        new_skip = zone_result.get("skip", False)

        # Check what the current applied state is
        was_skip = False
        for dur_eid, adj_data in adjusted.items():
            if adj_data.get("zone_entity_id") == zone_eid:
                was_skip = adj_data.get("skip", False)
                break

        if new_skip != was_skip:
            print(f"[MOISTURE] Skip↔factor transition detected: {zone_eid} "
                  f"was_skip={was_skip} → new_skip={new_skip} "
                  f"(triggered by {entity_id}: {old_state} → {new_state})")
            return True

    return False


async def on_probe_wake(probe_id: str):
    """Called when a probe's status LED transitions from OFF to ON (sleeping → awake).

    Updates the awake cache, then checks for pending sleep duration and
    sleep_disabled writes and applies them.
    Waits a few seconds after wake to ensure writable entities are ready.
    """
    data = _load_data()
    probe = data.get("probes", {}).get(probe_id)
    if not probe:
        return

    # Mark probe as awake in the cache
    _probe_awake_cache[probe_id] = True

    display_name = probe.get("display_name", probe_id)

    # Log probe wake event to run history
    try:
        import run_log
        mapped_zones = probe.get("zone_mappings", [])
        # Build zone names list for the log entry
        zone_names = []
        for zeid in mapped_zones:
            znum_match = re.search(r'zone[_]?(\d+)', zeid, re.IGNORECASE)
            zone_names.append(f"Zone {znum_match.group(1)}" if znum_match else zeid)
        zones_text = ", ".join(zone_names) if zone_names else "no mapped zones"
        # Extract probe number from probe_id (e.g. "gophr_1" → "1")
        probe_num_match = re.search(r'(\d+)', probe_id)
        probe_num = probe_num_match.group(1) if probe_num_match else probe_id
        run_log.log_probe_event(
            probe_id=probe_id,
            event_type="probe_wake",
            display_name=display_name,
            zone_name=f"Probe {probe_num} woke — mapped to {zones_text}",
            details={"mapped_zones": mapped_zones},
        )
    except Exception as e:
        print(f"[MOISTURE] Failed to log probe wake event: {e}")

    pending_duration = probe.get("pending_sleep_duration")
    pending_disabled = probe.get("pending_sleep_disabled")
    has_pending = pending_duration is not None or pending_disabled is not None

    if has_pending:
        print(f"[MOISTURE] Probe {display_name} woke up — "
              f"waiting 3s then applying pending writes "
              f"(duration={pending_duration}, disabled={pending_disabled})")
        # Wait for writable entities to become available
        await asyncio.sleep(3)

        # Verify device is still awake before attempting writes
        still_awake = await _check_probe_awake(probe_id)
        if not still_awake:
            print(f"[MOISTURE] Probe {display_name} went back to sleep before "
                  f"pending writes could be applied — will retry on next wake")
            return  # Don't clear pending — retry on next wake

        # Re-load data in case anything changed during the wait
        data = _load_data()
        probe = data.get("probes", {}).get(probe_id)
        if not probe:
            return

        # Apply pending sleep duration
        pending_duration = probe.get("pending_sleep_duration")
        if pending_duration is not None:
            success = await _set_probe_sleep_duration(probe_id, pending_duration)
            if success:
                probe["pending_sleep_duration"] = None
                # Update sensor cache so UI shows the new value immediately
                sleep_sensor_eid = (probe.get("extra_sensors") or {}).get("sleep_duration")
                if sleep_sensor_eid:
                    _load_sensor_cache()
                    _sensor_cache[sleep_sensor_eid] = {
                        "state": float(pending_duration),
                        "raw_state": str(pending_duration),
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                        "friendly_name": sleep_sensor_eid,
                    }
                    _save_sensor_cache()
                print(f"[MOISTURE] Pending sleep duration {pending_duration} min applied to {display_name}")
            else:
                print(f"[MOISTURE] Failed to apply pending sleep duration to {display_name} — "
                      f"will retry on next wake")

        # Apply pending sleep_disabled toggle
        pending_disabled = probe.get("pending_sleep_disabled")
        if pending_disabled is not None:
            success = await set_probe_sleep_disabled(probe_id, pending_disabled)
            if success:
                probe["pending_sleep_disabled"] = None
                action = "disabled" if pending_disabled else "enabled"
                print(f"[MOISTURE] Pending sleep {action} applied to {display_name}")
            else:
                print(f"[MOISTURE] Failed to apply pending sleep toggle to {display_name} — "
                      f"will retry on next wake")

        _save_data(data)
    else:
        print(f"[MOISTURE] Probe {display_name} woke up (no pending writes)")

    # Late-start monitoring: if any mapped zone is currently running and
    # we don't have an active monitor for it, start one now.
    # This handles the case where a probe wakes up DURING a zone run.
    mapped_zones = probe.get("zone_mappings", [])
    if mapped_zones:
        try:
            zone_states_list = await ha_client.get_entities_by_ids(mapped_zones)
            for zs in (zone_states_list or []):
                zeid = zs.get("entity_id", "")
                zstate = zs.get("state", "")
                if zstate in ("on", "open") and zeid not in _active_moisture_monitors:
                    task = asyncio.create_task(
                        monitor_zone_moisture(zeid, probe_id)
                    )
                    _active_moisture_monitors[zeid] = task
                    print(f"[MOISTURE] Late-start monitor: {display_name} woke "
                          f"while {zeid} is running — started monitoring")
        except Exception as e:
            print(f"[MOISTURE] Late-start monitor check error: {e}")


@router.post("/probes/sync-schedules", summary="Sync irrigation schedules to moisture probes")
async def api_sync_schedules():
    """DEPRECATED: Sync irrigation controller start times to Gophr schedule_time entities.

    This is the legacy approach that writes start times to Gophr schedule slots.
    Replaced by the probe-aware irrigation timeline system which actively manages
    probe sleep/wake cycles around scheduled runs.
    """
    print("[MOISTURE] WARNING: sync-schedules is deprecated — use schedule-timeline instead")
    result = await sync_schedule_times_to_probes()
    return result


@router.get("/schedule-timeline", summary="Get the irrigation schedule timeline")
async def api_get_schedule_timeline():
    """Return the calculated irrigation schedule timeline.

    Shows when each zone will run per schedule, which zones have probes,
    and the probe prep timing (when sleep will be reprogrammed so probes
    wake before their mapped zones).
    """
    timeline = _load_schedule_timeline()
    if not timeline:
        return {"success": True, "message": "No timeline calculated yet", "schedules": [], "probe_prep": {}}
    return {"success": True, **timeline}


@router.post("/schedule-timeline/recalculate", summary="Force recalculate the schedule timeline")
async def api_recalculate_timeline():
    """Force a recalculation of the irrigation schedule timeline.

    Recalculates when each zone will run, which probes need to wake before
    their mapped zones, and the optimal sleep reprogramming times.
    """
    timeline = await calculate_irrigation_timeline()
    return {"success": True, "message": "Timeline recalculated", **timeline}
