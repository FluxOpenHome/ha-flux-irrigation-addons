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
    "version": 1,
    "enabled": False,
    "stale_reading_threshold_minutes": 120,
    "depth_weights": {"shallow": 0.2, "mid": 0.5, "deep": 0.3},
    "default_thresholds": {
        "skip_threshold": 80,
        "scale_wet": 70,
        "scale_dry": 30,
        "max_increase_percent": 50,
        "max_decrease_percent": 50,
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


# --- Moisture Multiplier Calculation ---

def calculate_zone_moisture_multiplier(
    zone_entity_id: str,
    data: dict,
    sensor_states: dict,
) -> dict:
    """Calculate the moisture multiplier for a specific zone.

    Algorithm:
    1. Find all probes mapped to the zone
    2. For each probe, compute weighted average of non-stale depth readings
    3. Average effective moisture across all probes for the zone
    4. Apply thresholds to derive multiplier

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
    depth_weights = data.get("depth_weights", {"shallow": 0.2, "mid": 0.5, "deep": 0.3})
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

    # Calculate weighted moisture for each probe
    probe_details = []
    effective_moistures = []

    for probe_id, probe in mapped_probes:
        sensors = probe.get("sensors", {})
        thresholds = probe.get("thresholds") or default_thresholds

        weighted_sum = 0.0
        weight_sum = 0.0
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
                weight = depth_weights.get(depth, 0.33)
                weighted_sum += value * weight
                weight_sum += weight
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

        effective = weighted_sum / weight_sum if weight_sum > 0 else None
        if effective is not None:
            effective_moistures.append(effective)

        probe_details.append({
            "probe_id": probe_id,
            "display_name": probe.get("display_name", probe_id),
            "effective_moisture": round(effective, 1) if effective is not None else None,
            "depth_readings": depth_readings,
            "all_stale": weight_sum == 0,
        })

    # Average across all probes for this zone
    if not effective_moistures:
        return {
            "multiplier": 1.0,
            "avg_moisture": None,
            "skip": False,
            "probe_count": len(mapped_probes),
            "probe_details": probe_details,
            "reason": "All probe readings are stale or unavailable",
        }

    avg_moisture = sum(effective_moistures) / len(effective_moistures)

    # Apply thresholds using the first probe's thresholds (or defaults)
    # If different probes have different thresholds, we use defaults for the zone average
    thresholds = default_thresholds
    if len(mapped_probes) == 1:
        thresholds = mapped_probes[0][1].get("thresholds") or default_thresholds

    skip_threshold = thresholds.get("skip_threshold", 80)
    scale_wet = thresholds.get("scale_wet", 70)
    scale_dry = thresholds.get("scale_dry", 30)
    max_increase = thresholds.get("max_increase_percent", 50) / 100
    max_decrease = thresholds.get("max_decrease_percent", 50) / 100

    # Calculate multiplier
    if avg_moisture >= skip_threshold:
        multiplier = 0.0
        skip = True
        reason = f"Moisture {avg_moisture:.0f}% ≥ skip threshold {skip_threshold}%"
    elif avg_moisture >= scale_wet:
        # Linear decrease: scale_wet → skip_threshold maps to (1-max_decrease) → 0
        range_span = skip_threshold - scale_wet
        if range_span > 0:
            fraction = (avg_moisture - scale_wet) / range_span
            multiplier = (1 - max_decrease) * (1 - fraction)
        else:
            multiplier = 1 - max_decrease
        skip = False
        reason = f"Moisture {avg_moisture:.0f}% ≥ wet threshold {scale_wet}%, reducing {(1 - multiplier) * 100:.0f}%"
    elif avg_moisture >= scale_dry:
        # Linear interpolation: scale_dry → scale_wet maps to (1+max_increase) → (1-max_decrease)
        range_span = scale_wet - scale_dry
        if range_span > 0:
            fraction = (avg_moisture - scale_dry) / range_span
            multiplier = (1 + max_increase) - fraction * (max_increase + max_decrease)
        else:
            multiplier = 1.0
        skip = False
        if multiplier > 1.0:
            reason = f"Moisture {avg_moisture:.0f}% below wet threshold, increasing {(multiplier - 1) * 100:.0f}%"
        elif multiplier < 1.0:
            reason = f"Moisture {avg_moisture:.0f}% above dry threshold, reducing {(1 - multiplier) * 100:.0f}%"
        else:
            reason = f"Moisture {avg_moisture:.0f}% in normal range"
    else:
        # Below scale_dry: capped at max increase
        multiplier = 1 + max_increase
        skip = False
        reason = f"Moisture {avg_moisture:.0f}% < dry threshold {scale_dry}%, increasing {max_increase * 100:.0f}%"

    return {
        "multiplier": round(max(multiplier, 0.0), 3),
        "avg_moisture": round(avg_moisture, 1),
        "skip": skip,
        "probe_count": len(mapped_probes),
        "probe_details": probe_details,
        "reason": reason,
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

async def capture_base_durations() -> dict:
    """Read current number.*_run_duration entities and save as base durations.

    Scans the config's allowed_control_entities for number.* entities whose
    name contains 'run_duration', reads their current value, and stores them.

    Returns the captured durations dict.
    """
    config = get_config()
    data = _load_data()

    # Find run_duration entities from control entities
    duration_entities = [
        eid for eid in config.allowed_control_entities
        if eid.startswith("number.") and "run_duration" in eid
    ]

    if not duration_entities:
        return {"captured": 0, "base_durations": {}}

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

    if not data.get("enabled"):
        return {"success": False, "reason": "Moisture probes not enabled"}

    base_durations = data.get("base_durations", {})
    if not base_durations:
        return {"success": False, "reason": "No base durations captured. Use 'Capture Base Durations' first."}

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

    # Build a mapping: zone_entity_id → run_duration_entity_id
    # Convention: switch.irrigator_zone_1 → number.irrigator_zone_1_run_duration
    # We find the mapping by looking for a run_duration entity that contains the zone name
    zone_to_duration = {}
    for zone_eid in config.allowed_zone_entities:
        zone_suffix = zone_eid.split(".", 1)[1] if "." in zone_eid else zone_eid
        for dur_eid in base_durations:
            if zone_suffix in dur_eid:
                zone_to_duration[zone_eid] = dur_eid
                break

    for zone_eid, dur_eid in zone_to_duration.items():
        base = base_durations[dur_eid]["base_value"]

        moisture_result = calculate_zone_moisture_multiplier(
            zone_eid, data, sensor_states,
        )
        moisture_mult = moisture_result["multiplier"]
        skip = moisture_result["skip"]

        if skip:
            # Set to minimum (1 minute) — ESPHome won't skip entirely,
            # but this minimizes water usage
            adjusted_value = 1
        else:
            combined = weather_mult * moisture_mult
            adjusted_value = max(1, round(base * combined))

        # Write to HA
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
            print(f"[MOISTURE] {dur_eid}: {base} → {adjusted_value} "
                  f"(weather={weather_mult}, moisture={moisture_mult:.3f})")
        else:
            print(f"[MOISTURE] Failed to set {dur_eid} to {adjusted_value}")

    data["duration_adjustment_active"] = True
    data["adjusted_durations"] = adjusted
    data["last_evaluation"] = datetime.now(timezone.utc).isoformat()
    data["last_evaluation_result"] = {
        "weather_multiplier": weather_mult,
        "zones_adjusted": applied_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _save_data(data)

    return {
        "success": True,
        "applied": applied_count,
        "adjustments": adjusted,
    }


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
        base_value = dur_data["base_value"]
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
    Computes multipliers for all mapped zones and applies adjusted durations.
    """
    data = _load_data()

    if not data.get("enabled"):
        return {"skipped": True, "reason": "Moisture probes not enabled"}

    if not data.get("probes"):
        return {"skipped": True, "reason": "No probes configured"}

    if not data.get("base_durations"):
        return {"skipped": True, "reason": "No base durations captured"}

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

    _save_data(data)
    return {"success": True, "message": "Moisture settings updated"}


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
