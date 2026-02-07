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
from datetime import datetime, timedelta, timezone
from typing import Optional

RUN_LOG_FILE = "/data/run_history.jsonl"

# Cache of last-known zone states for the background watcher
_zone_states: dict[str, str] = {}
# Cache of zone start times for duration calculation
_zone_start_times: dict[str, str] = {}


def log_zone_event(
    entity_id: str,
    state: str,
    source: str = "api",
    zone_name: str = "",
    duration_seconds: Optional[float] = None,
):
    """Log a zone on/off event with current weather context.

    Args:
        entity_id: The HA entity_id (e.g. switch.zone_1)
        state: "on" or "off"
        source: Where this event originated (api, dashboard, timed_shutoff,
                weather_pause, system_pause, stop_all, schedule, unknown)
        zone_name: Human-readable zone name
        duration_seconds: For "off" events, how long the zone ran
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

    try:
        os.makedirs(os.path.dirname(RUN_LOG_FILE), exist_ok=True)
        with open(RUN_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[RUN_LOG] Failed to write: {e}")


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
                    if zone_id and entry.get("entity_id") != zone_id:
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


async def watch_zone_states():
    """Background task: poll zone states and log transitions.

    This catches zone runs triggered by ESPHome schedules, HA automations,
    or any other source that bypasses our API (since we don't have HA
    event listeners, polling is the fallback).

    Also enforces system pause: if the system is paused and a zone turns on
    (e.g., ESPHome schedule bypassed our disable), immediately turn it off.
    """
    import asyncio
    import ha_client
    from config import get_config

    global _zone_states

    while True:
        try:
            config = get_config()
            if not config.allowed_zone_entities:
                await asyncio.sleep(30)
                continue

            # Check if system is currently paused
            system_paused = False
            try:
                from routes.schedule import _load_schedules
                schedule_data = _load_schedules()
                system_paused = schedule_data.get("system_paused", False)
            except Exception:
                pass

            entities = await ha_client.get_entities_by_ids(config.allowed_zone_entities)

            # Build a set of entity IDs we received from HA for gap detection
            received_ids = {e["entity_id"] for e in entities}
            for expected_id in config.allowed_zone_entities:
                if expected_id not in received_ids:
                    print(f"[RUN_LOG] Warning: expected entity {expected_id} not returned by HA")

            for entity in entities:
                entity_id = entity["entity_id"]
                current_state = entity.get("state", "unknown")
                prev_state = _zone_states.get(entity_id)

                # Enforce pause: if system is paused and a zone just turned on,
                # immediately turn it off (safety net for ESPHome schedule bypass)
                if system_paused and current_state in ("on", "open"):
                    if prev_state not in ("on", "open"):
                        # Zone just came on while paused — suppress it
                        domain = entity_id.split(".")[0] if "." in entity_id else "switch"
                        if domain == "valve":
                            await ha_client.call_service("valve", "close", {"entity_id": entity_id})
                        else:
                            await ha_client.call_service("switch", "turn_off", {"entity_id": entity_id})
                        attrs = entity.get("attributes", {})
                        zone_name = attrs.get("friendly_name", entity_id)
                        log_zone_event(
                            entity_id=entity_id,
                            state="off",
                            source="pause_enforced",
                            zone_name=zone_name,
                        )
                        print(f"[RUN_LOG] Pause enforced: turned off {entity_id} "
                              f"(zone started while system paused)")
                        _zone_states[entity_id] = "off"
                        continue

                # Detect transitions — also log initial "on" state on first poll
                if current_state != prev_state:
                    is_on = current_state in ("on", "open")
                    is_off = current_state in ("off", "closed")

                    if is_on or is_off:
                        attrs = entity.get("attributes", {})
                        zone_name = attrs.get("friendly_name", entity_id)

                        if prev_state is None and is_on:
                            # First poll and zone is already on — log it so we
                            # don't silently miss runs that started before the
                            # watcher (e.g., pump relay, firmware-triggered zones)
                            log_zone_event(
                                entity_id=entity_id,
                                state=current_state,
                                source="schedule",
                                zone_name=zone_name,
                            )
                            print(f"[RUN_LOG] Initial on state detected: {entity_id} ({zone_name})")
                        elif prev_state is not None:
                            # Normal transition — only log as "schedule" source
                            # if we don't already have a recent entry (to avoid
                            # duplicating API-triggered events)
                            recent = get_run_history(hours=1, zone_id=entity_id, limit=1)
                            already_logged = False
                            if recent:
                                last_ts = recent[0].get("timestamp", "")
                                last_state = recent[0].get("state", "")
                                try:
                                    last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                                    age = (datetime.now(timezone.utc) - last_dt).total_seconds()
                                    if age < 15 and last_state == current_state:
                                        already_logged = True
                                except (ValueError, TypeError):
                                    pass

                            if not already_logged:
                                log_zone_event(
                                    entity_id=entity_id,
                                    state=current_state,
                                    source="schedule",
                                    zone_name=zone_name,
                                )

                _zone_states[entity_id] = current_state

        except Exception as e:
            print(f"[RUN_LOG] State watcher error: {e}")

        await asyncio.sleep(10)  # Poll every 10 seconds
