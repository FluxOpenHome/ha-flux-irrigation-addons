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

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from config import get_config
import ha_client


router = APIRouter(prefix="/admin/api/homeowner/moisture", tags=["Moisture Probes"])

MOISTURE_FILE = "/data/moisture_probes.json"

# Keywords used to auto-discover moisture probe sensor entities
PROBE_KEYWORDS = ["gophr", "moisture", "soil"]


# --- Data Model ---

DEFAULT_DATA = {
    "version": 2,
    "enabled": False,
    "apply_factors_to_schedule": False,
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


# Keywords for filtering HA devices to likely moisture probes
DEVICE_KEYWORDS = ["gophr", "moisture", "soil", "probe"]


async def list_moisture_devices(show_all: bool = False) -> dict:
    """List HA devices, optionally filtered to likely moisture probe devices.

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
        # Filter to moisture/probe-related devices
        def _is_moisture_device(name: str, manufacturer: str, model: str) -> bool:
            searchable = f"{name} {manufacturer} {model}".lower()
            return any(kw in searchable for kw in DEVICE_KEYWORDS)

        result = [d for d in all_devices if _is_moisture_device(
            d["name"], d["manufacturer"], d["model"]
        )]

    result.sort(key=lambda d: d["name"].lower())
    return {"devices": result, "total_count": len(all_devices), "filtered": not show_all}


async def get_device_sensors(device_id: str) -> list[dict]:
    """Get all sensor entities belonging to a specific device.

    Returns sensor entities with their current state, for the user
    to map as probe depth sensors (shallow/mid/deep).

    Works even when the device is offline — entity registry entries persist
    regardless of device connectivity. State may show as 'unavailable' or
    'unknown' for offline devices.
    """
    entity_registry = await ha_client.get_entity_registry()
    all_states = await ha_client.get_all_states()

    print(f"[MOISTURE] get_device_sensors: looking for device_id={device_id}, "
          f"registry has {len(entity_registry)} entities, states has {len(all_states)} entries")

    # Build a lookup of entity_id → state data
    state_lookup = {}
    for s in all_states:
        state_lookup[s.get("entity_id", "")] = s

    sensors = []
    matched_any = 0
    for entity in entity_registry:
        if entity.get("device_id") != device_id:
            continue
        matched_any += 1
        if entity.get("disabled_by"):
            continue

        eid = entity.get("entity_id", "")
        domain = eid.split(".")[0] if "." in eid else ""

        # Only include sensor entities
        if domain != "sensor":
            continue

        state_data = state_lookup.get(eid, {})
        attrs = state_data.get("attributes", {})
        friendly_name = attrs.get(
            "friendly_name",
            entity.get("name") or entity.get("original_name", eid)
        )

        sensors.append({
            "entity_id": eid,
            "friendly_name": friendly_name,
            "state": state_data.get("state", "unavailable"),
            "unit_of_measurement": attrs.get("unit_of_measurement", ""),
            "device_class": attrs.get("device_class", ""),
            "last_updated": state_data.get("last_updated", ""),
            "original_name": entity.get("original_name", ""),
        })

    print(f"[MOISTURE] get_device_sensors: {matched_any} total entities matched device, "
          f"{len(sensors)} are sensors")
    if matched_any == 0:
        # Log some device IDs from the registry to help debug mismatches
        sample_device_ids = set()
        for e in entity_registry[:50]:
            did = e.get("device_id", "")
            if did:
                sample_device_ids.add(did)
        print(f"[MOISTURE] Sample device_ids in registry: {list(sample_device_ids)[:10]}")

    sensors.sort(key=lambda s: s["entity_id"])
    return sensors


# --- Sensor State Fetching ---

async def _get_probe_sensor_states(probes: dict) -> dict:
    """Fetch current states for all sensors across all probes.

    Returns:
        {entity_id: {state: float|None, last_updated: str, stale: bool}}
    """
    # Collect all unique sensor entity IDs
    sensor_ids = set()
    for probe in probes.values():
        for depth, eid in probe.get("sensors", {}).items():
            if eid:
                sensor_ids.add(eid)

    if not sensor_ids:
        return {}

    all_states = await ha_client.get_entities_by_ids(list(sensor_ids))
    result = {}
    for s in all_states:
        eid = s.get("entity_id", "")
        state_val = s.get("state", "unknown")
        try:
            numeric_val = float(state_val)
        except (ValueError, TypeError):
            numeric_val = None

        result[eid] = {
            "state": numeric_val,
            "raw_state": state_val,
            "last_updated": s.get("last_updated", ""),
            "friendly_name": s.get("attributes", {}).get("friendly_name", eid),
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
        reasons.append(f"Root zone {primary_val:.0f}% ≥ skip threshold {root_skip}%")

    elif primary_val >= root_wet:
        # Root zone is adequately moist — reduce watering
        range_span = root_skip - root_wet
        if range_span > 0:
            # Linear from (1-max_decrease) at root_wet to 0 at root_skip
            fraction = (primary_val - root_wet) / range_span
            multiplier = (1 - max_decrease) * (1 - fraction)
        else:
            multiplier = 1 - max_decrease
        reasons.append(f"Root zone {primary_val:.0f}% ≥ wet threshold {root_wet}%")

    elif primary_val >= root_optimal:
        # Root zone is in the optimal-to-wet range — slight reduction
        range_span = root_wet - root_optimal
        if range_span > 0:
            fraction = (primary_val - root_optimal) / range_span
            multiplier = 1.0 - (max_decrease * fraction)
        else:
            multiplier = 1.0
        if multiplier < 1.0:
            reasons.append(f"Root zone {primary_val:.0f}% approaching wet threshold")
        else:
            reasons.append(f"Root zone {primary_val:.0f}% in optimal range")

    elif primary_val >= root_dry:
        # Root zone between dry and optimal — increase slightly
        range_span = root_optimal - root_dry
        if range_span > 0:
            fraction = (root_optimal - primary_val) / range_span
            multiplier = 1.0 + (max_increase * fraction * 0.5)  # Up to half max increase
        else:
            multiplier = 1.0
        reasons.append(f"Root zone {primary_val:.0f}% below optimal, slightly increasing")

    else:
        # Root zone is critically dry — maximum increase
        multiplier = 1 + max_increase
        reasons.append(f"Root zone {primary_val:.0f}% < dry threshold {root_dry}%, max increase")

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
            reasons.append(f"Root zone {mid_val:.0f}% near wet threshold + rain → skipping")

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

    # For multiple probes: use the MINIMUM multiplier (most conservative)
    # If any probe says skip, we skip
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
    """Get the combined weather × moisture multiplier for a zone.

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
    moisture_result = calculate_zone_moisture_multiplier(
        zone_entity_id, data, sensor_states,
    )

    moisture_mult = moisture_result["multiplier"]
    skip = moisture_result["skip"]

    combined = weather_mult * moisture_mult if not skip else 0.0

    return {
        "combined_multiplier": round(combined, 3),
        "weather_multiplier": weather_mult,
        "moisture_multiplier": moisture_mult,
        "moisture_skip": skip,
        "moisture_reason": moisture_result["reason"],
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


async def apply_adjusted_durations() -> dict:
    """Compute and write adjusted durations to HA number entities.

    For each zone with mapped probes and a corresponding run_duration entity:
    1. Compute the combined weather × moisture multiplier
    2. Calculate adjusted duration = base × combined_multiplier
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

    # Check if any zones are currently running — skip if so
    zones = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    running = [z for z in zones if z.get("state") in ("on", "open")]
    if running:
        return {
            "success": False,
            "reason": f"{len(running)} zone(s) currently running. Wait for them to finish.",
        }

    sensor_states = await _get_probe_sensor_states(data.get("probes", {}))
    weather_mult = get_weather_multiplier()

    adjusted = {}
    applied_count = 0
    failed = []

    print(f"[MOISTURE] Applying factors: {len(base_durations)} duration entities, "
          f"weather_mult={weather_mult}")

    # Build reverse mapping: duration_entity_id → zone_entity_id (for moisture lookup)
    # Match by zone number: extract "zone_N" from both and pair them
    import re
    def _extract_zone_num(eid: str):
        m = re.search(r"zone[_\s]?(\d+)", eid, re.IGNORECASE)
        return m.group(1) if m else None

    dur_to_zone = {}
    zone_by_num = {}
    for zone_eid in config.allowed_zone_entities:
        zn = _extract_zone_num(zone_eid)
        if zn:
            zone_by_num[zn] = zone_eid

    for dur_eid in base_durations:
        zn = _extract_zone_num(dur_eid)
        if zn and zn in zone_by_num:
            dur_to_zone[dur_eid] = zone_by_num[zn]

    for dur_eid, dur_data in base_durations.items():
        base = dur_data["base_value"]

        # Get moisture multiplier for the corresponding zone (defaults to 1.0 if no match)
        zone_eid = dur_to_zone.get(dur_eid)
        if zone_eid:
            moisture_result = calculate_zone_moisture_multiplier(
                zone_eid, data, sensor_states,
            )
            moisture_mult = moisture_result["multiplier"]
            skip = moisture_result["skip"]
        else:
            moisture_mult = 1.0
            skip = False

        if skip:
            adjusted_value = 1.0
        else:
            combined = weather_mult * moisture_mult
            adjusted_value = float(max(1, round(base * combined)))

        # Write to HA via number.set_value service
        print(f"[MOISTURE] Setting {dur_eid}: base={base} → adjusted={adjusted_value} "
              f"(weather={weather_mult}, moisture={moisture_mult:.3f})")
        success = await ha_client.call_service("number", "set_value", {
            "entity_id": dur_eid,
            "value": adjusted_value,
        })

        if success:
            applied_count += 1
            adjusted[dur_eid] = {
                "entity_id": dur_eid,
                "original": base,
                "adjusted": adjusted_value,
                "weather_multiplier": weather_mult,
                "moisture_multiplier": moisture_mult,
                "combined_multiplier": round(weather_mult * moisture_mult, 3),
                "skip": skip,
                "applied_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            failed.append(dur_eid)
            print(f"[MOISTURE] FAILED to set {dur_eid} to {adjusted_value}")

    data["duration_adjustment_active"] = applied_count > 0
    data["adjusted_durations"] = adjusted
    data["last_evaluation"] = datetime.now(timezone.utc).isoformat()
    data["last_evaluation_result"] = {
        "weather_multiplier": weather_mult,
        "zones_adjusted": applied_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _save_data(data)

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
    base_durations = data.get("base_durations", {})

    if not base_durations:
        return {"success": True, "restored": 0, "reason": "No base durations to restore"}

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
    sensors: dict = Field(
        default_factory=dict,
        description='Sensor entity IDs by depth: {"shallow": "sensor.xxx", "mid": "sensor.yyy", "deep": "sensor.zzz"}',
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
    sensors: Optional[dict] = None
    zone_mappings: Optional[list[str]] = None
    thresholds: Optional[dict] = None


class MoistureSettingsRequest(BaseModel):
    enabled: Optional[bool] = None
    apply_factors_to_schedule: Optional[bool] = None
    stale_reading_threshold_minutes: Optional[int] = Field(None, ge=5, le=1440)
    depth_weights: Optional[dict] = None
    default_thresholds: Optional[dict] = None


# --- API Endpoints ---

@router.get("/probes/discover", summary="Discover moisture probe candidates")
async def api_discover_probes():
    """Scan all HA sensors for entities that look like moisture probes."""
    candidates = await discover_moisture_probes()
    return {"candidates": candidates, "total": len(candidates)}


@router.get("/devices", summary="List devices for moisture probe selection")
async def api_list_devices(show_all: bool = False):
    """List HA devices, optionally filtered to likely moisture probe devices.

    By default filters to devices matching keywords: gophr, moisture, soil, probe.
    Pass ?show_all=true to return every device.
    """
    return await list_moisture_devices(show_all=show_all)


@router.get("/devices/{device_id}/sensors", summary="Get sensor entities for a device")
async def api_get_device_sensors(device_id: str):
    """Get all sensor entities belonging to a specific device.

    Returns sensors that can be mapped as probe depth readings.
    """
    sensors = await get_device_sensors(device_id)
    return {"device_id": device_id, "sensors": sensors, "total": len(sensors)}


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

    sensor_states = await _get_probe_sensor_states(probes)
    stale_threshold = data.get("stale_reading_threshold_minutes", 120)

    # Enrich probe data with live readings
    enriched = {}
    for probe_id, probe in probes.items():
        sensors_with_readings = {}
        for depth, eid in probe.get("sensors", {}).items():
            sensor_data = sensor_states.get(eid, {})
            sensors_with_readings[depth] = {
                "entity_id": eid,
                "value": sensor_data.get("state"),
                "raw_state": sensor_data.get("raw_state", "unknown"),
                "friendly_name": sensor_data.get("friendly_name", eid),
                "last_updated": sensor_data.get("last_updated", ""),
                "stale": _is_stale(sensor_data.get("last_updated", ""), stale_threshold),
            }

        enriched[probe_id] = {
            **probe,
            "sensors_live": sensors_with_readings,
        }

    return {
        "enabled": data.get("enabled", False),
        "probes": enriched,
        "total": len(enriched),
    }


@router.post("/probes", summary="Add a new moisture probe")
async def api_add_probe(body: ProbeCreateRequest):
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
        "sensors": body.sensors,
        "zone_mappings": body.zone_mappings,
        "thresholds": body.thresholds,
    }

    data.setdefault("probes", {})[body.probe_id] = probe
    _save_data(data)

    return {"success": True, "probe": probe}


@router.put("/probes/{probe_id}", summary="Update a moisture probe")
async def api_update_probe(probe_id: str, body: ProbeUpdateRequest):
    """Update display name, thresholds, sensor mappings, or zone assignments."""
    data = _load_data()

    if probe_id not in data.get("probes", {}):
        raise HTTPException(status_code=404, detail=f"Probe '{probe_id}' not found")

    probe = data["probes"][probe_id]
    if body.display_name is not None:
        probe["display_name"] = body.display_name
    if body.sensors is not None:
        probe["sensors"] = body.sensors
    if body.zone_mappings is not None:
        probe["zone_mappings"] = body.zone_mappings
    if body.thresholds is not None:
        probe["thresholds"] = body.thresholds

    _save_data(data)
    return {"success": True, "probe": probe}


@router.delete("/probes/{probe_id}", summary="Remove a moisture probe")
async def api_delete_probe(probe_id: str):
    """Remove a moisture probe configuration."""
    data = _load_data()

    if probe_id not in data.get("probes", {}):
        raise HTTPException(status_code=404, detail=f"Probe '{probe_id}' not found")

    del data["probes"][probe_id]
    _save_data(data)

    return {"success": True, "message": f"Probe '{probe_id}' removed"}


@router.get("/settings", summary="Get moisture probe settings")
async def api_get_settings():
    """Get global moisture probe settings."""
    data = _load_data()
    return {
        "enabled": data.get("enabled", False),
        "apply_factors_to_schedule": data.get("apply_factors_to_schedule", False),
        "stale_reading_threshold_minutes": data.get("stale_reading_threshold_minutes", 120),
        "depth_weights": data.get("depth_weights", DEFAULT_DATA["depth_weights"]),
        "default_thresholds": data.get("default_thresholds", DEFAULT_DATA["default_thresholds"]),
    }


@router.put("/settings", summary="Update moisture probe settings")
async def api_update_settings(body: MoistureSettingsRequest):
    """Update global moisture settings (enable/disable, stale threshold, weights, defaults)."""
    data = _load_data()

    if body.enabled is not None:
        data["enabled"] = body.enabled
    if body.stale_reading_threshold_minutes is not None:
        data["stale_reading_threshold_minutes"] = body.stale_reading_threshold_minutes
    if body.depth_weights is not None:
        data["depth_weights"] = body.depth_weights
    if body.default_thresholds is not None:
        data["default_thresholds"] = body.default_thresholds

    # Handle apply_factors_to_schedule toggle
    if body.apply_factors_to_schedule is not None:
        was_enabled = data.get("apply_factors_to_schedule", False)
        data["apply_factors_to_schedule"] = body.apply_factors_to_schedule
        _save_data(data)

        if body.apply_factors_to_schedule and not was_enabled:
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
        elif not body.apply_factors_to_schedule and was_enabled:
            # Toggling OFF: restore base durations
            result = await restore_base_durations()
            restored = result.get("restored", 0)
            return {
                "success": True,
                "message": f"Original durations restored for {restored} zone(s)",
                "restored": restored,
            }

    _save_data(data)
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


@router.get("/multiplier", summary="Get overall moisture multiplier")
async def api_overall_multiplier():
    """Get the overall moisture multiplier across all probes.

    Returns both the moisture-only multiplier and a combined (weather × moisture)
    multiplier for the system-level watering factor display.
    """
    result = await calculate_overall_moisture_multiplier()
    weather_mult = get_weather_multiplier()
    moisture_mult = result["moisture_multiplier"]
    combined = round(weather_mult * moisture_mult, 3) if moisture_mult > 0 else 0.0
    return {
        **result,
        "weather_multiplier": weather_mult,
        "combined_multiplier": combined,
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
