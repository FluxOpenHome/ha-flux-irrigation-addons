"""
Flux Open Home - Clone Dashboard to Native HA Lovelace
========================================================
Creates (or updates) a native Home Assistant Lovelace dashboard populated
with modern, visually appealing cards that mirror the Flux irrigation system.

Uses the HA WebSocket API:
  - lovelace/dashboards/list   — check if dashboard exists
  - lovelace/dashboards/create — create a new storage-mode dashboard
  - lovelace/config/save       — push the full card/view config

The generated dashboard uses modern native HA card types (tile, gauge,
statistics-graph, grid, heading, area, etc.) — no custom components required.
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

# Color palette for zones — rotate through these
ZONE_COLORS = [
    "green", "blue", "cyan", "teal", "light-green",
    "indigo", "deep-purple", "amber", "deep-orange", "lime",
    "light-blue", "purple", "orange", "brown", "blue-grey",
    "pink", "red", "yellow",
]


# ---------------------------------------------------------------------------
#  Entity classification (Python port of JS SCHEDULE_PATTERNS)
# ---------------------------------------------------------------------------

def _classify_entity(entity_id: str, domain: str) -> Optional[str]:
    """Classify a control entity into a schedule category."""
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


def _find_common_prefix(names: list[str]) -> str:
    """Find the longest common prefix across a list of friendly names.

    E.g., ['Irrigation System Sprinkler Zone 1', 'Irrigation System Sprinkler Zone 2',
           'Irrigation System Sprinkler Schedule Monday']
    → 'Irrigation System Sprinkler '
    """
    if not names or len(names) < 2:
        return ""
    shortest = min(names, key=len)
    for i, ch in enumerate(shortest):
        for name in names:
            if name[i] != ch:
                # Back up to the last space boundary
                prefix = shortest[:i]
                last_space = prefix.rfind(" ")
                return prefix[:last_space + 1] if last_space >= 0 else ""
    return shortest


def _strip_device_prefix(friendly_name: str, prefix: str) -> str:
    """Strip the common device prefix from a friendly name.

    'Irrigation System Sprinkler Schedule Monday' with prefix
    'Irrigation System Sprinkler ' → 'Schedule Monday'
    """
    if prefix and friendly_name.startswith(prefix):
        stripped = friendly_name[len(prefix):].strip()
        return stripped if stripped else friendly_name
    return friendly_name


async def _build_friendly_name_map(entity_ids: list[str]) -> dict[str, str]:
    """Fetch friendly names from HA for all entity IDs, then strip the
    common device prefix to produce short, readable names.

    Returns {entity_id: short_name}.
    """
    if not entity_ids:
        return {}

    # Fetch all states in one call (faster than individual fetches)
    all_states = await ha_client.get_all_states()
    state_map = {s["entity_id"]: s for s in all_states}

    # Build raw friendly name map
    raw_names: dict[str, str] = {}
    for eid in entity_ids:
        state = state_map.get(eid)
        if state and state.get("attributes", {}).get("friendly_name"):
            raw_names[eid] = state["attributes"]["friendly_name"]
        else:
            # Fallback: derive from entity ID
            raw_names[eid] = eid.split(".", 1)[-1].replace("_", " ").title()

    # Find common prefix across ALL friendly names
    all_friendly = list(raw_names.values())
    prefix = _find_common_prefix(all_friendly)

    # Strip prefix from each name
    short_names: dict[str, str] = {}
    for eid, fname in raw_names.items():
        short_names[eid] = _strip_device_prefix(fname, prefix)

    return short_names


def _n(entity_id: str, name_map: dict[str, str]) -> str:
    """Look up short name for an entity. Fallback to entity ID parsing."""
    if entity_id in name_map:
        return name_map[entity_id]
    return entity_id.split(".", 1)[-1].replace("_", " ").title()


def _zone_color(index: int) -> str:
    """Get a color for a zone by index."""
    return ZONE_COLORS[index % len(ZONE_COLORS)]


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
#  View builders — Modern, visually rich cards
# ---------------------------------------------------------------------------

def _build_overview_view(
    zone_eids: list[str],
    sensor_eids: list[str],
    weather_entity_id: str,
    rain_sensor_eids: list[str],
    rain_control_eids: list[str],
    name_map: dict[str, str],
) -> dict:
    """Build the Overview view with tile cards and modern layout."""
    cards: list[dict] = []

    # --- Welcome / Info banner ---
    cards.append({
        "type": "markdown",
        "content": (
            "# 💧 Flux Irrigation\n"
            "Your irrigation system at a glance. Tap any zone tile to toggle it.\n\n"
            "*For advanced features (moisture probes, schedule sync, run history, "
            "weather multipliers), use the **Flux UI**.*"
        ),
    })

    # --- Weather card (prominent, at top) ---
    if weather_entity_id:
        cards.append({
            "type": "weather-forecast",
            "entity": weather_entity_id,
            "show_forecast": True,
            "forecast_type": "daily",
        })

    # --- Zone tile cards in a grid ---
    if zone_eids:
        sorted_zones = sorted(zone_eids, key=_extract_zone_number)
        zone_tiles = []
        for i, eid in enumerate(sorted_zones):
            tile = {
                "type": "tile",
                "entity": eid,
                "name": _n(eid, name_map),
                "icon": "mdi:sprinkler-variant",
                "color": _zone_color(i),
                "vertical": False,
            }
            zone_tiles.append(tile)

        cards.append({
            "type": "grid",
            "columns": 3,
            "square": False,
            "cards": zone_tiles,
        })

    # --- Rain sensor / controls ---
    rain_all = rain_sensor_eids + rain_control_eids
    if rain_all:
        rain_tiles = []
        for eid in rain_all:
            domain = eid.split(".")[0]
            icon_map = {
                "binary_sensor": "mdi:weather-rainy",
                "switch": "mdi:weather-pouring",
                "number": "mdi:timer-sand",
                "select": "mdi:water-alert",
            }
            rain_tiles.append({
                "type": "tile",
                "entity": eid,
                "name": _n(eid, name_map),
                "icon": icon_map.get(domain, "mdi:water"),
                "color": "blue",
            })
        cards.append({
            "type": "grid",
            "columns": 2,
            "square": False,
            "cards": rain_tiles,
        })

    # --- Sensor entities (non-rain, non-expansion) ---
    filtered_sensors = [
        eid for eid in sensor_eids
        if not _is_rain_entity(eid) and not _is_expansion_entity(eid)
    ]
    if filtered_sensors:
        sensor_tiles = []
        for eid in filtered_sensors:
            domain = eid.split(".")[0]
            eid_lower = eid.lower()
            # Choose icons based on entity type
            icon = "mdi:information-outline"
            color = "grey"
            if "wifi" in eid_lower or "signal" in eid_lower:
                icon = "mdi:wifi"
                color = "indigo"
            elif "battery" in eid_lower:
                icon = "mdi:battery"
                color = "green"
            elif "temperature" in eid_lower or "temp" in eid_lower:
                icon = "mdi:thermometer"
                color = "deep-orange"
            elif "humidity" in eid_lower:
                icon = "mdi:water-percent"
                color = "cyan"
            elif "pressure" in eid_lower:
                icon = "mdi:gauge"
                color = "purple"
            elif "voltage" in eid_lower or "current" in eid_lower or "power" in eid_lower:
                icon = "mdi:flash"
                color = "amber"
            elif "uptime" in eid_lower:
                icon = "mdi:timer-outline"
                color = "teal"
            elif domain == "binary_sensor":
                icon = "mdi:checkbox-marked-circle-outline"
                color = "green"

            sensor_tiles.append({
                "type": "tile",
                "entity": eid,
                "name": _n(eid, name_map),
                "icon": icon,
                "color": color,
            })

        cards.append({
            "type": "grid",
            "columns": 3,
            "square": False,
            "cards": sensor_tiles,
        })

    return {
        "title": "Overview",
        "path": "overview",
        "icon": "mdi:view-dashboard",
        "cards": cards,
    }


def _build_schedule_view(control_eids: list[str], name_map: dict[str, str]) -> dict:
    """Build a modern Schedule view with tile cards grouped by category."""
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

    # --- Header ---
    cards.append({
        "type": "markdown",
        "content": (
            "# 📅 Irrigation Schedule\n"
            "Manage your watering days, start times, and zone durations."
        ),
    })

    # --- Schedule enable + system controls as tile cards ---
    sched_enables = categories["schedule_enable"] + categories["system_controls"]
    if sched_enables:
        tiles = []
        for eid in sched_enables:
            eid_lower = eid.lower()
            icon = "mdi:calendar-check"
            color = "green"
            if "auto_advance" in eid_lower:
                icon = "mdi:skip-forward"
                color = "teal"
            elif "start_stop" in eid_lower:
                icon = "mdi:play-pause"
                color = "blue"
            tiles.append({
                "type": "tile",
                "entity": eid,
                "name": _n(eid, name_map),
                "icon": icon,
                "color": color,
            })
        cards.append({
            "type": "grid",
            "columns": min(len(tiles), 3),
            "square": False,
            "cards": tiles,
        })

    # --- Day switches (Mon→Sun) as colored tile toggles ---
    day_switches = sorted(categories["day_switches"], key=_day_sort_key)
    if day_switches:
        day_tiles = []
        day_icons = {
            "monday": "mdi:alpha-m-circle",
            "tuesday": "mdi:alpha-t-circle",
            "wednesday": "mdi:alpha-w-circle",
            "thursday": "mdi:alpha-t-circle-outline",
            "friday": "mdi:alpha-f-circle",
            "saturday": "mdi:alpha-s-circle",
            "sunday": "mdi:alpha-s-circle-outline",
        }
        for eid in day_switches:
            eid_lower = eid.lower()
            icon = "mdi:calendar"
            for day_name, day_icon in day_icons.items():
                if day_name in eid_lower:
                    icon = day_icon
                    break
            day_tiles.append({
                "type": "tile",
                "entity": eid,
                "name": _n(eid, name_map),
                "icon": icon,
                "color": "green",
            })
        cards.append({
            "type": "grid",
            "columns": min(len(day_tiles), 4),
            "square": False,
            "cards": day_tiles,
        })

    # --- Start times ---
    start_times = sorted(categories["start_times"], key=_extract_start_time_number)
    if start_times:
        st_tiles = []
        for i, eid in enumerate(start_times):
            st_tiles.append({
                "type": "tile",
                "entity": eid,
                "name": _n(eid, name_map),
                "icon": "mdi:clock-start",
                "color": "amber",
            })
        cards.append({
            "type": "grid",
            "columns": min(len(st_tiles), 4),
            "square": False,
            "cards": st_tiles,
        })

    # --- Zone run durations (sorted by zone number) ---
    run_durations = sorted(categories["run_durations"], key=_extract_zone_number)
    if run_durations:
        dur_tiles = []
        for i, eid in enumerate(run_durations):
            dur_tiles.append({
                "type": "tile",
                "entity": eid,
                "name": _n(eid, name_map),
                "icon": "mdi:timer-outline",
                "color": _zone_color(i),
            })
        cards.append({
            "type": "grid",
            "columns": 3,
            "square": False,
            "cards": dur_tiles,
        })

    # --- Zone enables (sorted by zone number) ---
    zone_enables = sorted(categories["zone_enables"], key=_extract_zone_number)
    if zone_enables:
        en_tiles = []
        for i, eid in enumerate(zone_enables):
            en_tiles.append({
                "type": "tile",
                "entity": eid,
                "name": _n(eid, name_map),
                "icon": "mdi:checkbox-marked-circle-outline",
                "color": _zone_color(i),
            })
        cards.append({
            "type": "grid",
            "columns": 3,
            "square": False,
            "cards": en_tiles,
        })

    # --- Zone modes ---
    zone_modes = sorted(categories["zone_modes"], key=_extract_zone_number)
    if zone_modes:
        mode_tiles = []
        for i, eid in enumerate(zone_modes):
            mode_tiles.append({
                "type": "tile",
                "entity": eid,
                "name": _n(eid, name_map),
                "icon": "mdi:tune-variant",
                "color": _zone_color(i),
            })
        cards.append({
            "type": "grid",
            "columns": 3,
            "square": False,
            "cards": mode_tiles,
        })

    # --- Repeat cycles ---
    if categories["repeat_cycles"]:
        cyc_tiles = []
        for eid in categories["repeat_cycles"]:
            cyc_tiles.append({
                "type": "tile",
                "entity": eid,
                "name": _n(eid, name_map),
                "icon": "mdi:repeat",
                "color": "deep-purple",
            })
        cards.append({
            "type": "grid",
            "columns": min(len(cyc_tiles), 3),
            "square": False,
            "cards": cyc_tiles,
        })

    if len(cards) <= 1:
        cards.append({
            "type": "markdown",
            "content": "*No schedule entities found. Configure your device first.*",
        })

    return {
        "title": "Schedule",
        "path": "schedule",
        "icon": "mdi:calendar-clock",
        "cards": cards,
    }


def _build_moisture_view(moisture_data: dict, name_map: dict[str, str]) -> Optional[dict]:
    """Build a modern Moisture Probes view with gauges and statistics graphs."""
    probes = moisture_data.get("probes", {})
    if not probes:
        return None

    cards: list[dict] = []

    cards.append({
        "type": "markdown",
        "content": (
            "# 🌱 Moisture Probes\n"
            "Live soil moisture readings and trends from your Gophr probes."
        ),
    })

    for probe_id, probe in probes.items():
        display_name = probe.get("display_name", probe_id)
        sensors = probe.get("sensors", {})
        extra = probe.get("extra_sensors", {})

        # --- Probe header ---
        cards.append({
            "type": "markdown",
            "content": f"## {display_name}",
        })

        # --- Gauge cards for depth sensors ---
        gauge_cards: list[dict] = []
        depth_colors = {
            "shallow": {"green": 40, "yellow": 20, "red": 0},
            "mid": {"green": 35, "yellow": 15, "red": 0},
            "deep": {"green": 30, "yellow": 10, "red": 0},
        }
        depth_icons = {
            "shallow": "mdi:arrow-down-thin",
            "mid": "mdi:arrow-down",
            "deep": "mdi:arrow-down-bold",
        }
        for depth in ("shallow", "mid", "deep"):
            eid = sensors.get(depth)
            if eid:
                gauge_cards.append({
                    "type": "gauge",
                    "entity": eid,
                    "name": f"{depth.capitalize()}",
                    "min": 0,
                    "max": 100,
                    "needle": True,
                    "severity": depth_colors.get(depth, {"green": 40, "yellow": 20, "red": 0}),
                    "segments": [
                        {"from": 0, "color": "#e74c3c"},
                        {"from": 20, "color": "#f39c12"},
                        {"from": 40, "color": "#2ecc71"},
                        {"from": 80, "color": "#3498db"},
                    ],
                })

        if gauge_cards:
            cards.append({
                "type": "grid",
                "columns": min(len(gauge_cards), 3),
                "square": False,
                "cards": gauge_cards,
            })

        # --- Moisture trend statistics graph (48h) ---
        depth_eids = [sensors[d] for d in ("shallow", "mid", "deep") if sensors.get(d)]
        if depth_eids:
            cards.append({
                "type": "statistics-graph",
                "title": f"{display_name} — 48h Trends",
                "entities": depth_eids,
                "days_to_show": 2,
                "stat_types": ["mean"],
                "chart_type": "line",
                "period": "hour",
            })

        # --- Device sensors as tiles ---
        device_tiles = []
        if extra.get("wifi"):
            device_tiles.append({
                "type": "tile",
                "entity": extra["wifi"],
                "name": _n(extra["wifi"], name_map),
                "icon": "mdi:wifi",
                "color": "indigo",
            })
        if extra.get("battery"):
            device_tiles.append({
                "type": "tile",
                "entity": extra["battery"],
                "name": _n(extra["battery"], name_map),
                "icon": "mdi:battery",
                "color": "green",
            })
        if extra.get("sleep_duration"):
            device_tiles.append({
                "type": "tile",
                "entity": extra["sleep_duration"],
                "name": _n(extra["sleep_duration"], name_map),
                "icon": "mdi:sleep",
                "color": "deep-purple",
            })
        if extra.get("status_led"):
            device_tiles.append({
                "type": "tile",
                "entity": extra["status_led"],
                "name": _n(extra["status_led"], name_map),
                "icon": "mdi:led-on",
                "color": "amber",
            })

        if device_tiles:
            cards.append({
                "type": "grid",
                "columns": min(len(device_tiles), 4),
                "square": False,
                "cards": device_tiles,
            })

    if len(cards) <= 1:
        return None

    return {
        "title": "Moisture",
        "path": "moisture",
        "icon": "mdi:water-percent",
        "cards": cards,
    }


def _build_history_view(zone_eids: list[str], name_map: dict[str, str]) -> Optional[dict]:
    """Build a modern History view with statistics graphs."""
    if not zone_eids:
        return None

    sorted_zones = sorted(zone_eids, key=_extract_zone_number)
    cards: list[dict] = []

    cards.append({
        "type": "markdown",
        "content": (
            "# 📊 Run History\n"
            "See when your zones have been active."
        ),
    })

    # --- Combined 24h history graph ---
    cards.append({
        "type": "history-graph",
        "title": "All Zones — Last 24 Hours",
        "entities": [{"entity": eid} for eid in sorted_zones],
        "hours_to_show": 24,
    })

    # --- Individual zone tiles + history in a nice grid ---
    for i, eid in enumerate(sorted_zones):
        name = _n(eid, name_map)
        # Vertical stack: tile card on top, history below
        cards.append({
            "type": "vertical-stack",
            "cards": [
                {
                    "type": "tile",
                    "entity": eid,
                    "name": name,
                    "icon": "mdi:sprinkler-variant",
                    "color": _zone_color(i),
                    "vertical": False,
                },
                {
                    "type": "history-graph",
                    "entities": [{"entity": eid}],
                    "hours_to_show": 48,
                },
            ],
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

    # Collect ALL entity IDs that will appear on the dashboard
    all_eids = set(zone_eids + sensor_eids + control_eids)
    if weather_eid:
        all_eids.add(weather_eid)
    # Add moisture probe entity IDs
    for probe in moisture_data.get("probes", {}).values():
        for depth_eid in probe.get("sensors", {}).values():
            if depth_eid:
                all_eids.add(depth_eid)
        for extra_eid in probe.get("extra_sensors", {}).values():
            if extra_eid:
                all_eids.add(extra_eid)

    # Fetch friendly names from HA and strip common device prefix
    name_map = await _build_friendly_name_map(list(all_eids))

    # Build views
    views: list[dict] = []

    views.append(_build_overview_view(
        zone_eids, sensor_eids, weather_eid,
        rain_sensor_eids, rain_control_eids, name_map,
    ))

    views.append(_build_schedule_view(control_eids, name_map))

    moisture_view = _build_moisture_view(moisture_data, name_map)
    if moisture_view:
        views.append(moisture_view)

    history_view = _build_history_view(zone_eids, name_map)
    if history_view:
        views.append(history_view)

    return {"views": views}


# ---------------------------------------------------------------------------
#  API endpoint
# ---------------------------------------------------------------------------

@router.post("/clone-to-ha", summary="Clone dashboard to native HA Lovelace")
async def clone_dashboard_to_ha(request: Request):
    """Create or update a native Home Assistant Lovelace dashboard.

    Generates a storage-mode dashboard populated with modern cards that mirror
    the Flux irrigation system's current configuration:

    - **Overview**: Zone tile controls, weather forecast, rain sensor, system sensors
    - **Schedule**: Day toggles, start times, zone durations, enables — all as tile cards
    - **Moisture**: Needle gauges, statistics graphs, device info tiles (if probes configured)
    - **History**: Zone run history graphs with tile cards (24h combined + 48h per zone)

    Uses modern HA card types: tile, gauge (with needle), statistics-graph, grid,
    markdown headers, and vertical-stack for rich visual layouts.

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
