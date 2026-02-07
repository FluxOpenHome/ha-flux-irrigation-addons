"""
Flux Open Home - Weather-Based Irrigation Control
===================================================
Weather data fetching, rules engine, and API endpoints.
Uses existing HA weather entities (NWS, Weather Underground, etc.)
for intelligent irrigation scheduling adjustments.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from config import get_config
import ha_client


router = APIRouter(prefix="/admin/api", tags=["Weather Control"])

WEATHER_RULES_FILE = "/data/weather_rules.json"
WEATHER_LOG_FILE = "/data/weather_log.jsonl"


# --- Weather Event Log ---

def _log_weather_event(event_type: str, details: dict):
    """Append a weather event to the persistent weather log."""
    try:
        os.makedirs(os.path.dirname(WEATHER_LOG_FILE), exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            **details,
        }
        with open(WEATHER_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[WEATHER] Failed to write log: {e}")


def get_weather_log(limit: int = 200, hours: int = 0) -> list[dict]:
    """Read weather log entries. If hours > 0, filter to that window."""
    if not os.path.exists(WEATHER_LOG_FILE):
        return []
    cutoff = None
    if hours > 0:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    entries = []
    try:
        with open(WEATHER_LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if cutoff and entry.get("timestamp", "") < cutoff:
                        continue
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []
    return entries[-limit:]


def cleanup_weather_log(retention_days: int = 30):
    """Remove weather log entries older than retention period."""
    if not os.path.exists(WEATHER_LOG_FILE):
        return
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    kept = []
    try:
        with open(WEATHER_LOG_FILE, "r") as f:
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
        with open(WEATHER_LOG_FILE, "w") as f:
            for line in kept:
                f.write(line + "\n")
    except Exception as e:
        print(f"[WEATHER] Failed to cleanup log: {e}")

def get_weather_context_for_events(events: list[dict]) -> dict:
    """Build a weather context lookup from the weather log.

    Returns a dict of approximate weather snapshots keyed by hour bucket
    (YYYY-MM-DDTHH) so run events can look up the closest weather state.
    Also returns the current weather state from weather_rules.json.
    """
    log_entries = get_weather_log(limit=10000)
    if not log_entries:
        return {"snapshots": {}, "current": _get_current_weather_snapshot()}

    # Build hourly snapshots from weather log (evaluation events have the most data)
    snapshots = {}
    for entry in log_entries:
        ts = entry.get("timestamp", "")
        if len(ts) < 13:
            continue
        hour_key = ts[:13]  # YYYY-MM-DDTHH
        snapshots[hour_key] = {
            "condition": entry.get("condition", ""),
            "temperature": entry.get("temperature"),
            "humidity": entry.get("humidity"),
            "wind_speed": entry.get("wind_speed"),
            "watering_multiplier": entry.get("watering_multiplier"),
            "event": entry.get("event", ""),
            "rules_triggered": entry.get("triggered_rules", []),
            "reason": entry.get("reason", ""),
        }

    return {"snapshots": snapshots, "current": _get_current_weather_snapshot()}


def _get_current_weather_snapshot() -> dict:
    """Get the current weather state from the saved rules data."""
    rules_data = _load_weather_rules()
    last_data = rules_data.get("last_weather_data", {})
    return {
        "condition": last_data.get("condition", ""),
        "temperature": last_data.get("temperature"),
        "humidity": last_data.get("humidity"),
        "wind_speed": last_data.get("wind_speed"),
        "watering_multiplier": rules_data.get("watering_multiplier", 1.0),
        "active_adjustments": rules_data.get("active_adjustments", []),
        "last_evaluation": rules_data.get("last_evaluation"),
    }


def lookup_weather_at(snapshots: dict, timestamp: str) -> dict:
    """Find the closest weather snapshot for a given event timestamp."""
    if not timestamp or len(timestamp) < 13:
        return {}
    hour_key = timestamp[:13]
    # Exact hour match
    if hour_key in snapshots:
        return snapshots[hour_key]
    # Try previous hour
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        prev_hour = (dt - timedelta(hours=1)).isoformat()[:13]
        if prev_hour in snapshots:
            return snapshots[prev_hour]
    except (ValueError, TypeError):
        pass
    return {}


DEFAULT_RULES = {
    "rules_version": 1,
    "last_evaluation": None,
    "last_weather_data": {},
    "active_adjustments": [],
    "watering_multiplier": 1.0,
    "rules": {
        "rain_detection": {
            "enabled": True,
            "resume_delay_hours": 2,
        },
        "rain_forecast": {
            "enabled": True,
            "lookahead_hours": 24,
            "probability_threshold": 60,
        },
        "precipitation_threshold": {
            "enabled": True,
            "skip_if_rain_above_mm": 6.0,
        },
        "temperature_freeze": {
            "enabled": True,
            "freeze_threshold_f": 35,
            "freeze_threshold_c": 2,
        },
        "temperature_cool": {
            "enabled": True,
            "cool_threshold_f": 60,
            "cool_threshold_c": 15,
            "reduction_percent": 25,
        },
        "temperature_hot": {
            "enabled": True,
            "hot_threshold_f": 95,
            "hot_threshold_c": 35,
            "increase_percent": 25,
        },
        "wind_speed": {
            "enabled": True,
            "max_wind_speed_mph": 20,
            "max_wind_speed_kmh": 32,
        },
        "humidity": {
            "enabled": True,
            "high_humidity_threshold": 80,
            "reduction_percent": 20,
        },
        "seasonal_adjustment": {
            "enabled": False,
            "monthly_multipliers": {
                "1": 0.0, "2": 0.0, "3": 0.5, "4": 0.7,
                "5": 0.9, "6": 1.0, "7": 1.2, "8": 1.2,
                "9": 1.0, "10": 0.7, "11": 0.4, "12": 0.0,
            },
        },
    },
}


# --- Persistence ---

def _load_weather_rules() -> dict:
    """Load weather rules from persistent storage."""
    if os.path.exists(WEATHER_RULES_FILE):
        try:
            with open(WEATHER_RULES_FILE, "r") as f:
                data = json.load(f)
                # Ensure all default rules exist (forward-compat)
                for key, default in DEFAULT_RULES["rules"].items():
                    if key not in data.get("rules", {}):
                        data.setdefault("rules", {})[key] = default
                return data
        except (json.JSONDecodeError, IOError):
            pass
    return json.loads(json.dumps(DEFAULT_RULES))  # deep copy


def _save_weather_rules(data: dict):
    """Save weather rules to persistent storage."""
    os.makedirs(os.path.dirname(WEATHER_RULES_FILE), exist_ok=True)
    with open(WEATHER_RULES_FILE, "w") as f:
        json.dump(data, f, indent=2)


# --- Weather Data Fetching ---

async def get_weather_data() -> dict:
    """Fetch current weather and forecast from the configured HA weather entity."""
    config = get_config()
    if not config.weather_entity_id:
        return {"error": "No weather entity configured"}

    state = await ha_client.get_entity_state(config.weather_entity_id)
    if state is None:
        return {"error": f"Weather entity {config.weather_entity_id} not found"}

    attrs = state.get("attributes", {})
    forecast = attrs.get("forecast", [])

    return {
        "entity_id": config.weather_entity_id,
        "condition": state.get("state", "unknown"),
        "temperature": attrs.get("temperature"),
        "temperature_unit": attrs.get("temperature_unit", "°F"),
        "humidity": attrs.get("humidity"),
        "wind_speed": attrs.get("wind_speed"),
        "wind_speed_unit": attrs.get("wind_speed_unit", "mph"),
        "wind_bearing": attrs.get("wind_bearing"),
        "pressure": attrs.get("pressure"),
        "forecast": forecast[:7],
        "last_updated": state.get("last_updated"),
    }


# --- Rules Engine ---

async def run_weather_evaluation() -> dict:
    """Evaluate all enabled weather rules against current conditions.

    Returns a summary of triggered rules and actions taken.
    """
    config = get_config()
    if not config.weather_enabled or not config.weather_entity_id:
        return {"skipped": True, "reason": "Weather control disabled or no entity configured"}

    weather = await get_weather_data()
    if "error" in weather:
        return {"skipped": True, "reason": weather["error"]}

    rules_data = _load_weather_rules()
    rules = rules_data.get("rules", {})

    triggered = []
    new_adjustments = []
    multiplier = 1.0
    should_pause = False
    pause_reason = ""

    # Rule 1: Rain Detection
    rule = rules.get("rain_detection", {})
    if rule.get("enabled"):
        rain_conditions = {"rainy", "pouring", "lightning-rainy"}
        if weather["condition"] in rain_conditions:
            delay_hours = rule.get("resume_delay_hours", 2)
            should_pause = True
            pause_reason = f"Currently raining ({weather['condition']})"
            triggered.append({"rule": "rain_detection", "action": "pause", "reason": pause_reason})
            new_adjustments.append({
                "rule": "rain_detection", "action": "pause",
                "reason": pause_reason,
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=delay_hours)).isoformat(),
            })

    # Rule 2: Rain Forecast
    rule = rules.get("rain_forecast", {})
    if rule.get("enabled") and not should_pause:
        forecast = weather.get("forecast", [])
        prob_threshold = rule.get("probability_threshold", 60)
        for f in forecast:
            precip_prob = f.get("precipitation_probability", 0) or 0
            if precip_prob >= prob_threshold:
                reason = f"Rain forecasted ({precip_prob}% probability)"
                should_pause = True
                pause_reason = pause_reason or reason
                triggered.append({"rule": "rain_forecast", "action": "skip", "reason": reason})
                new_adjustments.append({
                    "rule": "rain_forecast", "action": "skip",
                    "reason": reason,
                    "applied_at": datetime.now(timezone.utc).isoformat(),
                })
                break

    # Rule 3: Precipitation Threshold
    rule = rules.get("precipitation_threshold", {})
    if rule.get("enabled") and not should_pause:
        threshold_mm = rule.get("skip_if_rain_above_mm", 6.0)
        forecast = weather.get("forecast", [])
        total_precip = sum((f.get("precipitation", 0) or 0) for f in forecast[:2])
        if total_precip >= threshold_mm:
            reason = f"Expected rainfall {total_precip:.1f}mm exceeds {threshold_mm}mm threshold"
            should_pause = True
            pause_reason = pause_reason or reason
            triggered.append({"rule": "precipitation_threshold", "action": "skip", "reason": reason})

    # Rule 4: Temperature Freeze
    rule = rules.get("temperature_freeze", {})
    if rule.get("enabled") and not should_pause:
        temp = weather.get("temperature")
        temp_unit = weather.get("temperature_unit", "°F")
        threshold = rule.get("freeze_threshold_c", 2) if "C" in temp_unit else rule.get("freeze_threshold_f", 35)
        if temp is not None and temp <= threshold:
            reason = f"Temperature {temp}{temp_unit} at or below freeze threshold ({threshold}{temp_unit})"
            should_pause = True
            pause_reason = pause_reason or reason
            triggered.append({"rule": "temperature_freeze", "action": "skip", "reason": reason})

    # Rule 5: Temperature Cool (reduce watering)
    rule = rules.get("temperature_cool", {})
    if rule.get("enabled") and not should_pause:
        temp = weather.get("temperature")
        temp_unit = weather.get("temperature_unit", "°F")
        threshold = rule.get("cool_threshold_c", 15) if "C" in temp_unit else rule.get("cool_threshold_f", 60)
        reduction = rule.get("reduction_percent", 25)
        if temp is not None and temp < threshold:
            multiplier *= (1 - reduction / 100)
            reason = f"Cool temperature {temp}{temp_unit}, reducing watering {reduction}%"
            triggered.append({"rule": "temperature_cool", "action": "reduce", "reason": reason})
            new_adjustments.append({
                "rule": "temperature_cool", "action": "reduce",
                "reason": reason,
                "applied_at": datetime.now(timezone.utc).isoformat(),
            })

    # Rule 6: Temperature Hot (increase watering)
    rule = rules.get("temperature_hot", {})
    if rule.get("enabled") and not should_pause:
        temp = weather.get("temperature")
        temp_unit = weather.get("temperature_unit", "°F")
        threshold = rule.get("hot_threshold_c", 35) if "C" in temp_unit else rule.get("hot_threshold_f", 95)
        increase = rule.get("increase_percent", 25)
        if temp is not None and temp > threshold:
            multiplier *= (1 + increase / 100)
            reason = f"Hot temperature {temp}{temp_unit}, increasing watering {increase}%"
            triggered.append({"rule": "temperature_hot", "action": "increase", "reason": reason})
            new_adjustments.append({
                "rule": "temperature_hot", "action": "increase",
                "reason": reason,
                "applied_at": datetime.now(timezone.utc).isoformat(),
            })

    # Rule 7: Wind Speed
    rule = rules.get("wind_speed", {})
    if rule.get("enabled") and not should_pause:
        wind = weather.get("wind_speed")
        wind_unit = weather.get("wind_speed_unit", "mph")
        threshold = rule.get("max_wind_speed_kmh", 32) if "km" in wind_unit.lower() else rule.get("max_wind_speed_mph", 20)
        if wind is not None and wind > threshold:
            reason = f"Wind speed {wind} {wind_unit} exceeds {threshold} {wind_unit} threshold"
            should_pause = True
            pause_reason = pause_reason or reason
            triggered.append({"rule": "wind_speed", "action": "skip", "reason": reason})

    # Rule 8: Humidity
    rule = rules.get("humidity", {})
    if rule.get("enabled") and not should_pause:
        humidity = weather.get("humidity")
        threshold = rule.get("high_humidity_threshold", 80)
        reduction = rule.get("reduction_percent", 20)
        if humidity is not None and humidity > threshold:
            multiplier *= (1 - reduction / 100)
            reason = f"High humidity {humidity}%, reducing watering {reduction}%"
            triggered.append({"rule": "humidity", "action": "reduce", "reason": reason})
            new_adjustments.append({
                "rule": "humidity", "action": "reduce",
                "reason": reason,
                "applied_at": datetime.now(timezone.utc).isoformat(),
            })

    # Rule 9: Seasonal Adjustment
    rule = rules.get("seasonal_adjustment", {})
    if rule.get("enabled"):
        month = str(datetime.now().month)
        monthly = rule.get("monthly_multipliers", {})
        season_mult = float(monthly.get(month, 1.0))
        multiplier *= season_mult
        triggered.append({
            "rule": "seasonal_adjustment", "action": "multiply",
            "reason": f"Seasonal adjustment for month {month}: {season_mult}x",
        })

    # --- Apply Actions ---

    from routes.schedule import _load_schedules, _save_schedules

    if should_pause:
        schedule_data = _load_schedules()
        if not schedule_data.get("system_paused"):
            # Disable ESPHome schedule programs so the controller can't start runs
            import schedule_control
            saved_states = await schedule_control.disable_schedules()

            schedule_data["system_paused"] = True
            schedule_data["weather_paused"] = True
            schedule_data["weather_pause_reason"] = pause_reason
            if saved_states:
                schedule_data["saved_schedule_states"] = saved_states
            _save_schedules(schedule_data)

            # Stop all active zones
            import run_log
            zones = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
            for zone in zones:
                if zone.get("state") in ("on", "open"):
                    entity_id = zone["entity_id"]
                    domain = entity_id.split(".")[0] if "." in entity_id else "switch"
                    if domain == "valve":
                        await ha_client.call_service("valve", "close", {"entity_id": entity_id})
                    else:
                        await ha_client.call_service("switch", "turn_off", {"entity_id": entity_id})
                    attrs = zone.get("attributes", {})
                    run_log.log_zone_event(
                        entity_id=entity_id, state="off", source="weather_pause",
                        zone_name=attrs.get("friendly_name", entity_id),
                    )

            await ha_client.fire_event("flux_irrigation_weather_pause", {
                "reason": pause_reason,
                "rules_triggered": [t["rule"] for t in triggered],
            })
            _log_weather_event("weather_pause", {
                "reason": pause_reason,
                "rules_triggered": [t["rule"] for t in triggered],
                "condition": weather.get("condition"),
                "temperature": weather.get("temperature"),
                "humidity": weather.get("humidity"),
                "wind_speed": weather.get("wind_speed"),
            })
            # Log to run history so it appears alongside zone events
            import run_log
            run_log.log_zone_event(
                entity_id="system",
                state="weather_pause",
                source="weather",
                zone_name=f"Weather Pause: {pause_reason}",
            )
            print(f"[WEATHER] System paused: {pause_reason}")
    else:
        # Auto-resume if previously weather-paused and conditions cleared
        schedule_data = _load_schedules()
        if schedule_data.get("weather_paused") and schedule_data.get("system_paused"):
            # Restore ESPHome schedule programs to their prior state
            import schedule_control
            saved_states = schedule_data.get("saved_schedule_states", {})
            await schedule_control.restore_schedules(saved_states)

            schedule_data["system_paused"] = False
            schedule_data["weather_paused"] = False
            schedule_data.pop("weather_pause_reason", None)
            schedule_data.pop("saved_schedule_states", None)
            _save_schedules(schedule_data)

            await ha_client.fire_event("flux_irrigation_weather_resume", {
                "reason": "Weather conditions cleared",
            })
            _log_weather_event("weather_resume", {
                "reason": "Weather conditions cleared",
                "condition": weather.get("condition"),
                "temperature": weather.get("temperature"),
                "humidity": weather.get("humidity"),
                "wind_speed": weather.get("wind_speed"),
            })
            # Log to run history so it appears alongside zone events
            import run_log
            run_log.log_zone_event(
                entity_id="system",
                state="weather_resume",
                source="weather",
                zone_name="Weather Resume: conditions cleared",
            )
            print("[WEATHER] System auto-resumed: weather conditions cleared")

    # Log evaluation if any rules triggered
    if triggered:
        _log_weather_event("weather_evaluation", {
            "triggered_rules": [t["rule"] for t in triggered],
            "actions": [t["action"] for t in triggered],
            "watering_multiplier": round(multiplier, 2),
            "should_pause": should_pause,
            "condition": weather.get("condition"),
            "temperature": weather.get("temperature"),
            "humidity": weather.get("humidity"),
            "wind_speed": weather.get("wind_speed"),
        })

    # Save evaluation results
    rules_data["last_evaluation"] = datetime.now(timezone.utc).isoformat()
    rules_data["last_weather_data"] = {
        "condition": weather.get("condition"),
        "temperature": weather.get("temperature"),
        "humidity": weather.get("humidity"),
        "wind_speed": weather.get("wind_speed"),
    }
    rules_data["active_adjustments"] = new_adjustments
    rules_data["watering_multiplier"] = round(multiplier, 2)
    _save_weather_rules(rules_data)

    # Trigger moisture probe re-evaluation so the combined multiplier
    # (weather × moisture) is recalculated with the updated weather multiplier
    try:
        from routes.moisture import run_moisture_evaluation
        await run_moisture_evaluation()
    except Exception as e:
        print(f"[WEATHER] Moisture re-evaluation after weather eval failed: {e}")

    return {
        "evaluated": True,
        "triggered_rules": triggered,
        "should_pause": should_pause,
        "pause_reason": pause_reason if should_pause else None,
        "watering_multiplier": round(multiplier, 2),
        "weather_condition": weather.get("condition"),
        "temperature": weather.get("temperature"),
    }


# --- API Endpoints ---

@router.get("/weather/entities", summary="List available weather entities")
async def list_weather_entities():
    """List all weather.* entities in HA for the configuration dropdown."""
    all_states = await ha_client.get_all_states()
    weather_entities = []
    for s in all_states:
        eid = s.get("entity_id", "")
        if eid.startswith("weather."):
            attrs = s.get("attributes", {})
            weather_entities.append({
                "entity_id": eid,
                "friendly_name": attrs.get("friendly_name", eid),
                "condition": s.get("state", "unknown"),
                "has_forecast": bool(attrs.get("forecast")),
            })
    return {"entities": weather_entities}


@router.get("/weather/current", summary="Get current weather and active rules")
async def get_current_weather():
    """Get current weather conditions and active weather adjustments."""
    config = get_config()
    weather = await get_weather_data()
    rules_data = _load_weather_rules()
    return {
        "weather": weather,
        "rules": rules_data.get("rules", {}),
        "active_adjustments": rules_data.get("active_adjustments", []),
        "watering_multiplier": rules_data.get("watering_multiplier", 1.0),
        "last_evaluation": rules_data.get("last_evaluation"),
        "weather_enabled": config.weather_enabled,
    }


@router.get("/weather/rules", summary="Get weather rules configuration")
async def get_weather_rules():
    """Get the current weather rules configuration."""
    return _load_weather_rules()


@router.put("/weather/rules", summary="Update weather rules")
async def update_weather_rules(body: dict):
    """Update weather rules configuration and re-evaluate immediately."""
    data = _load_weather_rules()
    if "rules" in body:
        data["rules"] = body["rules"]
    _save_weather_rules(data)
    # Re-evaluate rules immediately so the multiplier updates right away
    try:
        result = await run_weather_evaluation()
        return {
            "success": True,
            "message": "Weather rules updated",
            "watering_multiplier": result.get("watering_multiplier", 1.0),
        }
    except Exception as e:
        # Rules were saved even if evaluation fails
        return {"success": True, "message": f"Weather rules saved (evaluation error: {e})"}


@router.get("/weather/log", summary="Get weather event log")
async def get_weather_event_log(
    limit: int = Query(200, ge=1, le=1000, description="Max entries"),
    hours: int = Query(0, ge=0, le=8760, description="Filter to last N hours (0=all)"),
):
    """Get the weather event log — all evaluations, pauses, and resumes."""
    return {"events": get_weather_log(limit=limit, hours=hours)}


@router.get("/weather/log/csv", summary="Export weather log as CSV")
async def export_weather_log_csv(
    hours: int = Query(0, ge=0, le=8760, description="Filter to last N hours (0=all)"),
):
    """Export the weather event log as a downloadable CSV file."""
    from fastapi.responses import Response

    events = get_weather_log(limit=10000, hours=hours)

    lines = ["timestamp,event,condition,temperature,humidity,wind_speed,watering_multiplier,rules_triggered,reason"]
    for e in events:
        rules = ";".join(e.get("triggered_rules", []))
        line = ",".join([
            _csv_escape(e.get("timestamp", "")),
            _csv_escape(e.get("event", "")),
            _csv_escape(str(e.get("condition", ""))),
            _csv_escape(str(e.get("temperature", ""))),
            _csv_escape(str(e.get("humidity", ""))),
            _csv_escape(str(e.get("wind_speed", ""))),
            _csv_escape(str(e.get("watering_multiplier", ""))),
            _csv_escape(rules),
            _csv_escape(e.get("reason", "")),
        ])
        lines.append(line)

    csv_content = "\n".join(lines) + "\n"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=weather_log.csv"},
    )


@router.post("/weather/evaluate", summary="Manually trigger weather evaluation")
async def evaluate_weather_now():
    """Manually trigger a weather rules evaluation cycle."""
    result = await run_weather_evaluation()
    return result


@router.delete("/weather/log", summary="Clear weather event log")
async def clear_weather_log():
    """Delete all entries from the weather event log."""
    try:
        if os.path.exists(WEATHER_LOG_FILE):
            os.remove(WEATHER_LOG_FILE)
        return {"success": True, "message": "Weather log cleared"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _csv_escape(value: str) -> str:
    """Escape a value for CSV output."""
    if not value or value == "None":
        return ""
    if "," in value or '"' in value or "\n" in value:
        return '"' + value.replace('"', '""') + '"'
    return value
