"""
Flux Open Home - Clone Dashboard to Native HA Lovelace
========================================================
Creates (or updates) a native Home Assistant Lovelace dashboard populated
with cards that mirror the Flux irrigation homeowner UI.

Uses the HA WebSocket API:
  - lovelace/dashboards/list   — check if dashboard exists
  - lovelace/dashboards/create — create a new storage-mode dashboard
  - lovelace/config/save       — push the full card/view config

The generated dashboard uses only native HA card types (entities, gauge,
history-graph, weather-forecast, markdown, etc.) — no custom components.
"""

import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from config import get_config
import ha_client
from config_changelog import log_change, get_actor

router = APIRouter(
    prefix="/admin/api/homeowner/dashboard",
    tags=["Dashboard Clone"],
)

DASHBOARD_URL_PATH = "flux-irrigation"
DASHBOARD_TITLE = "Flux Irrigation"
DASHBOARD_ICON = "mdi:sprinkler-variant"

# Day-of-week ordering for schedule day switches
DAY_ORDER = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


# ---------------------------------------------------------------------------
#  Entity classification (Python port of JS SCHEDULE_PATTERNS)
# ---------------------------------------------------------------------------

def _classify_entity(entity_id: str, domain: str) -> Optional[str]:
    """Classify a control entity into a schedule category.

    Returns one of: 'schedule_enable', 'day_switches', 'start_times',
    'run_durations', 'repeat_cycles', 'zone_enables', 'zone_modes',
    'system_controls', or None if not a schedule entity.
    """
    eid = entity_id.lower()

    if (domain == "switch" and re.search(r"schedule", eid)
            and re.search(r"enable", eid)
            and not re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", eid)
            and not re.search(r"enable_zone", eid)):
        return "schedule_enable"

    if (domain == "switch" and re.search(r"schedule", eid)
            and re.search(r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", eid)):
        return "day_switches"

    if domain == "text" and re.search(r"start_time", eid):
        return "start_times"

    if (domain == "number"
            and (re.search(r"run_duration", eid)
                 or (re.search(r"zone_?\d", eid) and not re.search(r"repeat|cycle|mode", eid))
                 or re.search(r"duration.*zone", eid))):
        return "run_durations"

    if domain == "number" and re.search(r"repeat_cycle", eid):
        return "repeat_cycles"

    if domain == "switch" and re.search(r"enable_zone", eid):
        return "zone_enables"

    if domain == "select" and re.search(r"zone_\d+_mode", eid):
        return "zone_modes"

    if (domain == "switch"
            and (re.search(r"auto_advance", eid) or re.search(r"start_stop", eid))):
        return "system_controls"

    return None


def _is_rain_entity(entity_id: str) -> bool:
    """Check if an entity is rain-related."""
    eid = entity_id.lower()
    return bool(
        re.search(r"rain_sensor$", eid)
        or re.search(r"rain_sensor_enabled", eid)
        or re.search(r"rain_delay_enabled", eid)
        or re.search(r"rain_delay_hours", eid)
        or re.search(r"rain_sensor_type", eid)
        or re.search(r"rain_delay_active", eid)
    )


def _is_expansion_entity(entity_id: str) -> bool:
    """Check if an entity is expansion-board-related."""
    eid = entity_id.lower()
    return bool(re.search(r"detected_zones", eid) or re.search(r"rescan_expansion", eid))


def _day_sort_key(entity_id: str) -> int:
    """Sort key for day-of-week switch entities (Mon=0 .. Sun=6)."""
    eid = entity_id.lower()
    for day, idx in DAY_ORDER.items():
        if day in eid:
            return idx
    return 99


def _extract_start_time_number(entity_id: str) -> int:
    """Extract numeric suffix from start_time entity for sorting."""
    m = re.search(r"start_time[_\s]*(\d+)", entity_id, re.IGNORECASE)
    return int(m.group(1)) if m else 99


def _extract_zone_number(entity_id: str) -> int:
    """Extract zone number from entity ID for sorting."""
    m = re.search(r"zone[_\s]*(\d+)", entity_id, re.IGNORECASE)
    return int(m.group(1)) if m else 99


# ---------------------------------------------------------------------------
#  Lovelace WebSocket helpers
# ---------------------------------------------------------------------------

async def _list_dashboards() -> list:
    """List all existing Lovelace dashboards."""
    try:
        result = await ha_client._ws_command("lovelace/dashboards/list")
        return result or []
    except Exception as e:
        print(f"[DASHBOARD] Failed to list dashboards: {e}")
        return []


async def _create_dashboard(url_path: str, title: str, icon: str) -> dict:
    """Create a new storage-mode Lovelace dashboard."""
    return await ha_client._ws_command_with_data("lovelace/dashboards/create", {
        "url_path": url_path,
        "title": title,
        "icon": icon,
        "show_in_sidebar": True,
        "require_admin": False,
    })


async def _save_dashboard_config(url_path: str, config: dict):
    """Save (overwrite) the Lovelace config for a dashboard."""
    return await ha_client._ws_command_with_data("lovelace/config/save", {
        "url_path": url_path,
        "config": config,
    })


# ---------------------------------------------------------------------------
#  View builders
# ---------------------------------------------------------------------------

def _build_overview_view(
    zone_eids: list[str],
    sensor_eids: list[str],
    weather_entity_id: str,
    rain_sensor_eids: list[str],
    rain_control_eids: list[str],
) -> dict:
    """Build the Overview view: zones, weather, sensors, rain."""
    cards: list[dict] = []

    # Info card
    cards.append({
        "type": "markdown",
        "title": "Flux Irrigation",
        "content": (
            "This dashboard was auto-generated by the **Flux Open Home** "
            "irrigation add-on.  Use the Flux UI for advanced features "
            "(moisture multipliers, probe mapping, schedule sync, run history)."
        ),
    })

    # Zone switches
    if zone_eids:
        cards.append({
            "type": "entities",
            "title": "Irrigation Zones",
            "entities": [{"entity": eid} for eid in sorted(zone_eids, key=_extract_zone_number)],
            "show_header_toggle": False,
        })

    # Weather
    if weather_entity_id:
        cards.append({
            "type": "weather-forecast",
            "entity": weather_entity_id,
            "show_forecast": True,
        })

    # Rain sensor entities
    rain_all = [eid for eid in (rain_sensor_eids + rain_control_eids)]
    if rain_all:
        cards.append({
            "type": "entities",
            "title": "Rain Sensor",
            "entities": [{"entity": eid} for eid in rain_all],
        })

    # Non-rain, non-expansion sensors
    filtered_sensors = [
        eid for eid in sensor_eids
        if not _is_rain_entity(eid) and not _is_expansion_entity(eid)
    ]
    if filtered_sensors:
        cards.append({
            "type": "entities",
            "title": "Sensors",
            "entities": [{"entity": eid} for eid in filtered_sensors],
        })

    return {
        "title": "Overview",
        "path": "overview",
        "icon": "mdi:view-dashboard",
        "cards": cards,
    }


def _build_schedule_view(control_eids: list[str]) -> dict:
    """Build the Schedule view from classified control entities."""
    # Classify all control entities
    categories: dict[str, list[str]] = {
        "schedule_enable": [],
        "day_switches": [],
        "start_times": [],
        "run_durations": [],
        "repeat_cycles": [],
        "zone_enables": [],
        "zone_modes": [],
        "system_controls": [],
    }

    for eid in control_eids:
        domain = eid.split(".")[0] if "." in eid else ""
        cat = _classify_entity(eid, domain)
        if cat and cat in categories:
            categories[cat].append(eid)

    cards: list[dict] = []

    # Schedule enable + system controls (auto_advance, start_stop)
    sched_enables = categories["schedule_enable"] + categories["system_controls"]
    if sched_enables:
        cards.append({
            "type": "entities",
            "title": "Schedule Control",
            "entities": [{"entity": eid} for eid in sched_enables],
        })

    # Day switches (sorted Mon→Sun)
    day_switches = sorted(categories["day_switches"], key=_day_sort_key)
    if day_switches:
        cards.append({
            "type": "entities",
            "title": "Active Days",
            "entities": [{"entity": eid} for eid in day_switches],
            "show_header_toggle": False,
        })

    # Start times (sorted by number)
    start_times = sorted(categories["start_times"], key=_extract_start_time_number)
    if start_times:
        cards.append({
            "type": "entities",
            "title": "Start Times",
            "entities": [{"entity": eid} for eid in start_times],
        })

    # Zone run durations (sorted by zone number)
    run_durations = sorted(categories["run_durations"], key=_extract_zone_number)
    if run_durations:
        cards.append({
            "type": "entities",
            "title": "Zone Run Durations",
            "entities": [{"entity": eid} for eid in run_durations],
        })

    # Zone enables (sorted by zone number)
    zone_enables = sorted(categories["zone_enables"], key=_extract_zone_number)
    if zone_enables:
        cards.append({
            "type": "entities",
            "title": "Zone Enable / Disable",
            "entities": [{"entity": eid} for eid in zone_enables],
        })

    # Zone modes
    zone_modes = sorted(categories["zone_modes"], key=_extract_zone_number)
    if zone_modes:
        cards.append({
            "type": "entities",
            "title": "Zone Modes",
            "entities": [{"entity": eid} for eid in zone_modes],
        })

    # Repeat cycles
    if categories["repeat_cycles"]:
        cards.append({
            "type": "entities",
            "title": "Repeat Cycles",
            "entities": [{"entity": eid} for eid in categories["repeat_cycles"]],
        })

    if not cards:
        cards.append({
            "type": "markdown",
            "content": "No schedule entities found.",
        })

    return {
        "title": "Schedule",
        "path": "schedule",
        "icon": "mdi:calendar-clock",
        "cards": cards,
    }


def _build_moisture_view(moisture_data: dict) -> Optional[dict]:
    """Build the Moisture Probes view (returns None if no probes)."""
    probes = moisture_data.get("probes", {})
    if not probes:
        return None

    cards: list[dict] = []

    for probe_id, probe in probes.items():
        display_name = probe.get("display_name", probe_id)
        sensors = probe.get("sensors", {})
        extra = probe.get("extra_sensors", {})

        # Gauge cards for depth sensors
        gauge_cards: list[dict] = []
        for depth in ("shallow", "mid", "deep"):
            eid = sensors.get(depth)
            if eid:
                gauge_cards.append({
                    "type": "gauge",
                    "entity": eid,
                    "name": f"{display_name} — {depth.capitalize()}",
                    "min": 0,
                    "max": 100,
                    "severity": {
                        "green": 40,
                        "yellow": 20,
                        "red": 0,
                    },
                })

        if gauge_cards:
            cards.append({
                "type": "grid",
                "columns": min(len(gauge_cards), 3),
                "cards": gauge_cards,
            })

        # History graph for moisture trends (48h)
        depth_eids = [sensors[d] for d in ("shallow", "mid", "deep") if sensors.get(d)]
        if depth_eids:
            cards.append({
                "type": "history-graph",
                "title": f"{display_name} — Moisture Trends",
                "entities": [{"entity": eid} for eid in depth_eids],
                "hours_to_show": 48,
            })

        # Device sensors: wifi, battery, sleep_duration
        device_eids = [extra[k] for k in ("wifi", "battery") if extra.get(k)]
        # sleep_duration is a sensor entity (readable)
        if extra.get("sleep_duration"):
            device_eids.append(extra["sleep_duration"])

        if device_eids:
            cards.append({
                "type": "entities",
                "title": f"{display_name} — Device Info",
                "entities": [{"entity": eid} for eid in device_eids],
            })

    if not cards:
        return None

    return {
        "title": "Moisture",
        "path": "moisture",
        "icon": "mdi:water-percent",
        "cards": cards,
    }


def _build_history_view(zone_eids: list[str]) -> Optional[dict]:
    """Build the History view with zone run history graphs."""
    if not zone_eids:
        return None

    sorted_zones = sorted(zone_eids, key=_extract_zone_number)
    cards: list[dict] = []

    # Combined 24h graph
    cards.append({
        "type": "history-graph",
        "title": "All Zones — Last 24 Hours",
        "entities": [{"entity": eid} for eid in sorted_zones],
        "hours_to_show": 24,
    })

    # Individual 48h graphs
    for eid in sorted_zones:
        # Derive a readable name: "switch.zone_1" → "Zone 1"
        name = eid.split(".", 1)[-1].replace("_", " ").title()
        cards.append({
            "type": "history-graph",
            "title": name,
            "entities": [{"entity": eid}],
            "hours_to_show": 48,
        })

    return {
        "title": "History",
        "path": "history",
        "icon": "mdi:chart-line",
        "cards": cards,
    }


# ---------------------------------------------------------------------------
#  Main config assembly
# ---------------------------------------------------------------------------

async def _build_lovelace_config() -> dict:
    """Build the complete Lovelace dashboard config from current system state."""
    config = get_config()

    zone_eids = list(config.allowed_zone_entities)
    sensor_eids = list(config.allowed_sensor_entities)
    control_eids = list(config.allowed_control_entities)
    weather_eid = config.weather_entity_id or ""

    # Separate rain / expansion entities from sensors and controls
    rain_sensor_eids = [eid for eid in sensor_eids if _is_rain_entity(eid)]
    rain_control_eids = [eid for eid in control_eids if _is_rain_entity(eid)]

    # Load moisture probe data
    moisture_data: dict = {}
    try:
        from routes.moisture import _load_data as _load_moisture_data
        moisture_data = _load_moisture_data()
    except Exception:
        pass

    # Build views
    views: list[dict] = []

    views.append(_build_overview_view(
        zone_eids, sensor_eids, weather_eid,
        rain_sensor_eids, rain_control_eids,
    ))

    views.append(_build_schedule_view(control_eids))

    moisture_view = _build_moisture_view(moisture_data)
    if moisture_view:
        views.append(moisture_view)

    history_view = _build_history_view(zone_eids)
    if history_view:
        views.append(history_view)

    return {"views": views}


# ---------------------------------------------------------------------------
#  API endpoint
# ---------------------------------------------------------------------------

@router.post("/clone-to-ha", summary="Clone dashboard to native HA Lovelace")
async def clone_dashboard_to_ha(request: Request):
    """Create or update a native Home Assistant Lovelace dashboard.

    Generates a storage-mode dashboard populated with cards that mirror
    the Flux irrigation system's current configuration:

    - **Overview**: Zone controls, weather, rain sensor, system sensors
    - **Schedule**: Day switches, start times, zone durations, enables
    - **Moisture**: Probe gauges, trends, device sensors (if probes configured)
    - **History**: Zone run history graphs (24h combined + 48h per zone)

    The dashboard appears in the HA sidebar immediately.  Pressing the
    button again updates the existing dashboard (idempotent).
    """
    cfg = get_config()
    if not cfg.allowed_zone_entities and not cfg.allowed_sensor_entities:
        raise HTTPException(
            status_code=400,
            detail="No irrigation device configured.  Please select a device on the Configuration page first.",
        )

    try:
        # Step 1: Check if dashboard already exists
        dashboards = await _list_dashboards()
        exists = any(d.get("url_path") == DASHBOARD_URL_PATH for d in dashboards)

        # Step 2: Create if needed
        if not exists:
            await _create_dashboard(DASHBOARD_URL_PATH, DASHBOARD_TITLE, DASHBOARD_ICON)
            print(f"[DASHBOARD] Created HA dashboard: /{DASHBOARD_URL_PATH}")

        # Step 3: Build config from current system state
        lovelace_config = await _build_lovelace_config()

        # Step 4: Push config
        await _save_dashboard_config(DASHBOARD_URL_PATH, lovelace_config)

        view_count = len(lovelace_config.get("views", []))
        card_count = sum(len(v.get("cards", [])) for v in lovelace_config.get("views", []))
        action = "Updated" if exists else "Created"
        print(f"[DASHBOARD] {action} HA dashboard: /{DASHBOARD_URL_PATH} "
              f"({view_count} views, {card_count} cards)")

        # Step 5: Log the change
        log_change(
            get_actor(request), "System",
            f"{action} HA dashboard '/{DASHBOARD_URL_PATH}' "
            f"({view_count} views, {card_count} cards)",
        )

        return {
            "success": True,
            "created": not exists,
            "updated": exists,
            "url_path": DASHBOARD_URL_PATH,
            "views": view_count,
            "cards": card_count,
            "message": f"Dashboard '/{DASHBOARD_URL_PATH}' {action.lower()} successfully "
                       f"({view_count} views, {card_count} cards)",
        }

    except Exception as e:
        print(f"[DASHBOARD] Clone failed: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to create HA dashboard: {e}")
