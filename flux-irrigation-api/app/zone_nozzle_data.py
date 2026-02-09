"""
Flux Open Home - Zone Nozzle/Head Details
==========================================
Manages per-zone sprinkler head inventory for professional documentation.
Each zone can store multiple heads with type, GPM, spray arc, radius, etc.

Persists data in /data/zone_nozzle_details.json.

The sprinkler model database is loaded from sprinkler_models.json in the
app directory.  To add models, simply edit that JSON file — no Python
changes required.
"""

import json
import os
import uuid

ZONE_NOZZLE_FILE = "/data/zone_nozzle_details.json"
_MODELS_FILE = os.path.join(os.path.dirname(__file__), "sprinkler_models.json")

# -------------------------------------------------------------------
# Reference data – professional sprinkler head types & specifications
# -------------------------------------------------------------------

NOZZLE_TYPES = [
    {
        "id": "pop_up_spray",
        "name": "Pop-Up Spray Head",
        "category": "spray",
        "description": "Fixed-pattern spray with high precipitation rate. Best for small to medium areas.",
        "gpm_min": 0.06,
        "gpm_max": 5.0,
        "radius_min_ft": 5,
        "radius_max_ft": 15,
        "precip_rate": "1.0–2.5 in/hr",
        "pressure_psi": "15–70 (optimal 30)",
        "pop_up_heights": ["2\"", "3\"", "4\"", "6\"", "12\""],
        "arc_options": [60, 90, 120, 150, 180, 210, 240, 270, 360],
        "adjustable_arc": False,
    },
    {
        "id": "rotary_nozzle",
        "name": "Rotary Nozzle (MP Rotator)",
        "category": "spray",
        "description": "Multi-stream rotating nozzle with low, matched precipitation rate. Water-efficient.",
        "gpm_min": 0.06,
        "gpm_max": 2.4,
        "radius_min_ft": 8,
        "radius_max_ft": 24,
        "precip_rate": "0.4–0.8 in/hr",
        "pressure_psi": "20–75 (optimal 30–45)",
        "pop_up_heights": ["2\"", "3\"", "4\"", "6\"", "12\""],
        "arc_options": [],
        "adjustable_arc": True,
        "arc_range": "45°–360°",
    },
    {
        "id": "gear_rotor",
        "name": "Gear-Drive Rotor",
        "category": "rotor",
        "description": "Gear-driven rotating stream for medium to large areas. Matched precipitation rate.",
        "gpm_min": 0.54,
        "gpm_max": 4.6,
        "radius_min_ft": 18,
        "radius_max_ft": 50,
        "precip_rate": "0.25–0.75 in/hr",
        "pressure_psi": "25–65 (optimal 40–50)",
        "pop_up_heights": ["2\"", "3\"", "4\"", "6\""],
        "arc_options": [],
        "adjustable_arc": True,
        "arc_range": "40°–360°",
    },
    {
        "id": "impact_rotor",
        "name": "Impact Rotor",
        "category": "rotor",
        "description": "Impact-driven rotating arm for very large areas. High flow rate.",
        "gpm_min": 1.5,
        "gpm_max": 15.0,
        "radius_min_ft": 20,
        "radius_max_ft": 150,
        "precip_rate": "0.1–1.5 in/hr",
        "pressure_psi": "25–60 (optimal 40–50)",
        "pop_up_heights": ["2\"", "3\"", "4\"", "6\""],
        "arc_options": [],
        "adjustable_arc": True,
        "arc_range": "20°–360°",
    },
    {
        "id": "micro_spray",
        "name": "Micro-Spray",
        "category": "low_volume",
        "description": "Low-volume fine spray for shrubs, ground cover, and small beds. Uses GPH.",
        "gpm_min": 0.08,
        "gpm_max": 0.42,
        "radius_min_ft": 3,
        "radius_max_ft": 12,
        "precip_rate": "Varies by pattern",
        "pressure_psi": "15–50 (optimal 20–30)",
        "pop_up_heights": [],
        "arc_options": [90, 180, 270, 360],
        "adjustable_arc": False,
        "note": "Flow often rated in GPH (5–25 GPH)",
    },
    {
        "id": "bubbler",
        "name": "Bubbler",
        "category": "low_volume",
        "description": "Flood/bubble pattern for tree basins and large shrubs. Adjustable flow.",
        "gpm_min": 0.0,
        "gpm_max": 0.22,
        "radius_min_ft": 1,
        "radius_max_ft": 3,
        "precip_rate": "Flood pattern",
        "pressure_psi": "15–50 (optimal 25)",
        "pop_up_heights": [],
        "arc_options": [360],
        "adjustable_arc": False,
        "note": "Flow often rated in GPH (0–13 GPH)",
    },
    {
        "id": "drip_emitter",
        "name": "Drip Emitter",
        "category": "low_volume",
        "description": "Point-source low-volume watering for individual plants. Most water-efficient.",
        "gpm_min": 0.01,
        "gpm_max": 0.07,
        "radius_min_ft": 0,
        "radius_max_ft": 1,
        "precip_rate": "Point source",
        "pressure_psi": "10–50 (optimal 15–25)",
        "pop_up_heights": [],
        "arc_options": [360],
        "adjustable_arc": False,
        "note": "Flow rated in GPH (0.5–4.0 GPH)",
    },
    {
        "id": "drip_line",
        "name": "Drip Tape / Drip Line",
        "category": "low_volume",
        "description": "In-line emitters for row crops, vegetable gardens, and annual beds.",
        "gpm_min": 0.0,
        "gpm_max": 1.0,
        "radius_min_ft": 0,
        "radius_max_ft": 0,
        "precip_rate": "0.45–0.74 GPM per 100ft",
        "pressure_psi": "8–10",
        "pop_up_heights": [],
        "arc_options": [],
        "adjustable_arc": False,
        "note": "Emitter spacing: 4\", 6\", 8\", 12\"",
    },
    {
        "id": "fixed_spray",
        "name": "Fixed / Stationary Spray",
        "category": "spray",
        "description": "Non-pop-up fixed spray head, mounted on a riser. Common in older systems.",
        "gpm_min": 0.06,
        "gpm_max": 5.0,
        "radius_min_ft": 5,
        "radius_max_ft": 15,
        "precip_rate": "1.0–2.5 in/hr",
        "pressure_psi": "15–70 (optimal 30)",
        "pop_up_heights": [],
        "arc_options": [60, 90, 120, 150, 180, 210, 240, 270, 360],
        "adjustable_arc": False,
    },
    {
        "id": "strip_spray",
        "name": "Strip / Side-Strip Nozzle",
        "category": "spray",
        "description": "Rectangular spray pattern for narrow strips, walkways, and medians.",
        "gpm_min": 0.14,
        "gpm_max": 1.5,
        "radius_min_ft": 4,
        "radius_max_ft": 30,
        "precip_rate": "1.0–2.0 in/hr",
        "pressure_psi": "15–50 (optimal 30)",
        "pop_up_heights": ["2\"", "3\"", "4\"", "6\"", "12\""],
        "arc_options": [],
        "adjustable_arc": False,
        "note": "Pattern: Left strip, right strip, center strip, end strip",
    },
]

BRANDS = [
    "Rain Bird",
    "Hunter",
    "Toro",
    "K-Rain",
    "Irritrol",
    "Orbit",
    "Nelson",
    "Weathermatic",
    "Jain",
    "Other",
]

# Standard arc options for dropdowns
STANDARD_ARCS = [
    {"value": 60, "label": "60° (1/6 circle)"},
    {"value": 90, "label": "90° (quarter)"},
    {"value": 120, "label": "120° (1/3 circle)"},
    {"value": 150, "label": "150° (5/12 circle)"},
    {"value": 180, "label": "180° (half)"},
    {"value": 210, "label": "210° (7/12 circle)"},
    {"value": 240, "label": "240° (2/3 circle)"},
    {"value": 270, "label": "270° (3/4 circle)"},
    {"value": 300, "label": "300° (5/6 circle)"},
    {"value": 360, "label": "360° (full circle)"},
]


# -------------------------------------------------------------------
# Persistence
# -------------------------------------------------------------------

def _load_data() -> dict:
    """Load zone nozzle data from persistent storage."""
    if os.path.exists(ZONE_NOZZLE_FILE):
        try:
            with open(ZONE_NOZZLE_FILE, "r") as f:
                data = json.load(f)
                if "zones" not in data:
                    data["zones"] = {}
                return data
        except (json.JSONDecodeError, IOError):
            pass
    return {"zones": {}}


def _save_data(data: dict):
    """Save zone nozzle data to persistent storage."""
    os.makedirs(os.path.dirname(ZONE_NOZZLE_FILE), exist_ok=True)
    with open(ZONE_NOZZLE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# -------------------------------------------------------------------
# CRUD operations
# -------------------------------------------------------------------

def get_zone_heads(entity_id: str) -> dict:
    """Get all head details for a specific zone."""
    data = _load_data()
    zone_data = data.get("zones", {}).get(entity_id, {})
    return {
        "entity_id": entity_id,
        "heads": zone_data.get("heads", []),
        "notes": zone_data.get("notes", ""),
        "total_gpm": sum(h.get("gpm", 0) for h in zone_data.get("heads", [])),
        "show_gpm_on_card": zone_data.get("show_gpm_on_card", False),
        "show_head_count_on_card": zone_data.get("show_head_count_on_card", False),
    }


def get_all_zones_heads() -> dict:
    """Get head details for all zones."""
    data = _load_data()
    result = {}
    for eid, zone_data in data.get("zones", {}).items():
        result[eid] = {
            "heads": zone_data.get("heads", []),
            "notes": zone_data.get("notes", ""),
            "total_gpm": sum(h.get("gpm", 0) for h in zone_data.get("heads", [])),
            "show_gpm_on_card": zone_data.get("show_gpm_on_card", False),
            "show_head_count_on_card": zone_data.get("show_head_count_on_card", False),
        }
    return result


def save_zone_heads(entity_id: str, heads: list, notes: str = "",
                    show_gpm_on_card: bool = False,
                    show_head_count_on_card: bool = False) -> dict:
    """Save complete head list for a zone. Replaces all heads."""
    data = _load_data()
    if "zones" not in data:
        data["zones"] = {}

    # Ensure every head has an ID
    for head in heads:
        if not head.get("id"):
            head["id"] = str(uuid.uuid4())[:8]

    data["zones"][entity_id] = {
        "heads": heads,
        "notes": notes,
        "show_gpm_on_card": show_gpm_on_card,
        "show_head_count_on_card": show_head_count_on_card,
    }
    _save_data(data)
    return get_zone_heads(entity_id)


def delete_zone_heads(entity_id: str) -> bool:
    """Remove all head data for a zone."""
    data = _load_data()
    if entity_id in data.get("zones", {}):
        del data["zones"][entity_id]
        _save_data(data)
        return True
    return False


def _load_models() -> list:
    """Load sprinkler model database from JSON file.

    The file lives alongside this module (sprinkler_models.json) so that
    adding new models only requires editing a simple JSON array.
    """
    if os.path.exists(_MODELS_FILE):
        try:
            with open(_MODELS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []


def get_reference_data() -> dict:
    """Return nozzle type reference data for the UI."""
    return {
        "nozzle_types": NOZZLE_TYPES,
        "brands": BRANDS,
        "standard_arcs": STANDARD_ARCS,
        "models": _load_models(),
    }
