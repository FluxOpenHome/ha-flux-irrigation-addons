"""
Flux Open Home - PDF System Report Generator
===============================================
Generates a comprehensive, professional system report as a downloadable PDF.
Gathers data from all system components (zones, weather, moisture,
schedule, sensors, issues, run history) and renders via fpdf2.

Uses Flux Open Home and Gophr logos for branding.
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import Response
from fpdf import FPDF

from config import get_config
import ha_client
import run_log

router = APIRouter(prefix="/admin/api/homeowner/report", tags=["Report"])

# Logo paths — these are bundled in app/assets/ and copied to /app/assets/ in Docker
_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
_FLUX_LOGO = os.path.join(_ASSETS_DIR, "flux_logo.png")
_GOPHR_LOGO = os.path.join(_ASSETS_DIR, "gophr_logo.jpg")

_ZONE_NUMBER_RE = re.compile(r'zone[_]?(\d+)', re.IGNORECASE)

# ─── Brand Colors ──────────────────────────────────────────────────────
GREEN_PRIMARY = (26, 122, 76)       # #1a7a4c
GREEN_ACCENT = (46, 204, 113)       # #2ecc71
GREEN_LIGHT = (212, 237, 218)       # #d4edda
TEXT_DARK = (44, 62, 80)            # #2c3e50
TEXT_MUTED = (127, 140, 141)        # #7f8c8d
TEXT_LIGHT = (149, 165, 166)        # #95a5a6
WHITE = (255, 255, 255)
TABLE_HEADER_BG = (26, 122, 76)
TABLE_ROW_ALT = (245, 248, 245)
TABLE_ROW_NORMAL = (255, 255, 255)
DIVIDER_COLOR = (200, 215, 200)
SEVERITY_COLORS = {
    "severe": (231, 76, 60),        # red
    "annoyance": (243, 156, 18),    # orange
    "clarification": (52, 152, 219),  # blue
}


def _extract_zone_number(entity_id: str) -> int:
    m = _ZONE_NUMBER_RE.search(entity_id)
    return int(m.group(1)) if m else 0


def _zone_name(entity_id: str) -> str:
    if "." in entity_id:
        return entity_id.split(".", 1)[1]
    return entity_id


# ─── Data Gathering Helpers ────────────────────────────────────────────

async def _get_status() -> dict:
    """Gather system status data (mirrors homeowner_status logic)."""
    config = get_config()
    ha_connected = await ha_client.check_connection()
    zones = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    max_zones = config.detected_zone_count
    if max_zones > 0:
        zones = [z for z in zones if _extract_zone_number(z.get("entity_id", "")) <= max_zones]
    active_zones = [z for z in zones if z.get("state") == "on"]
    sensors = await ha_client.get_entities_by_ids(config.allowed_sensor_entities)

    from routes.schedule import _load_schedules
    schedule_data = _load_schedules()

    rain_delay_until = schedule_data.get("rain_delay_until")
    rain_delay_active = False
    if rain_delay_until:
        try:
            delay_end = datetime.fromisoformat(rain_delay_until)
            rain_delay_active = datetime.now(timezone.utc) < delay_end
        except ValueError:
            pass

    weather_multiplier = 1.0
    try:
        from routes.weather import _load_weather_rules
        weather_rules = _load_weather_rules()
        weather_multiplier = weather_rules.get("watering_multiplier", 1.0)
    except Exception:
        pass

    moisture_enabled = False
    try:
        from routes.moisture import _load_data as _load_moisture_data
        moisture_data = _load_moisture_data()
        moisture_enabled = moisture_data.get("enabled", False)
    except Exception:
        pass

    return {
        "ha_connected": ha_connected,
        "system_paused": schedule_data.get("system_paused", False),
        "total_zones": len(zones),
        "active_zones": len(active_zones),
        "total_sensors": len(sensors),
        "rain_delay_active": rain_delay_active,
        "rain_delay_until": rain_delay_until if rain_delay_active else None,
        "moisture_enabled": moisture_enabled,
        "weather_multiplier": weather_multiplier,
        "address": config.homeowner_address or "",
        "city": config.homeowner_city or "",
        "state": config.homeowner_state or "",
        "zip": config.homeowner_zip or "",
        "phone": config.homeowner_phone or "",
        "first_name": config.homeowner_first_name or "",
        "last_name": config.homeowner_last_name or "",
    }


async def _get_zones() -> list:
    config = get_config()
    entities = await ha_client.get_entities_by_ids(config.allowed_zone_entities)
    max_zones = config.detected_zone_count
    zones = []
    for entity in entities:
        if max_zones > 0:
            zn = _extract_zone_number(entity["entity_id"])
            if zn > max_zones:
                continue
        attrs = entity.get("attributes", {})
        zones.append({
            "entity_id": entity["entity_id"],
            "name": _zone_name(entity["entity_id"]),
            "state": entity.get("state", "unknown"),
            "friendly_name": attrs.get("friendly_name"),
            "last_changed": entity.get("last_changed"),
        })
    return zones


def _get_zone_aliases() -> dict:
    aliases_file = "/data/homeowner_aliases.json"
    if os.path.exists(aliases_file):
        try:
            with open(aliases_file, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _get_all_zone_heads() -> dict:
    import zone_nozzle_data
    return zone_nozzle_data.get_all_zones_heads()


async def _get_sensors() -> list:
    config = get_config()
    entities = await ha_client.get_entities_by_ids(config.allowed_sensor_entities)
    sensors = []
    for entity in entities:
        attrs = entity.get("attributes", {})
        sensors.append({
            "entity_id": entity["entity_id"],
            "name": _zone_name(entity["entity_id"]),
            "state": entity.get("state", "unknown"),
            "unit_of_measurement": attrs.get("unit_of_measurement"),
            "friendly_name": attrs.get("friendly_name"),
            "last_updated": entity.get("last_updated"),
        })
    return sensors


async def _get_weather() -> dict:
    config = get_config()
    if not config.weather_enabled or not config.weather_entity_id:
        return {"weather_enabled": False}
    try:
        from routes.weather import get_weather_data, _load_weather_rules
        weather = await get_weather_data()
        rules_data = _load_weather_rules()
        return {
            "weather_enabled": True,
            "weather": weather,
            "active_adjustments": rules_data.get("active_adjustments", []),
            "watering_multiplier": rules_data.get("watering_multiplier", 1.0),
            "rules": rules_data.get("rules", {}),
        }
    except Exception:
        return {"weather_enabled": False}


def _get_moisture() -> dict:
    try:
        from routes.moisture import _load_data as _load_moisture_data
        return _load_moisture_data()
    except Exception:
        return {"enabled": False}


def _get_issues() -> list:
    try:
        import issue_store
        return issue_store.get_all_issues()
    except Exception:
        return []


# ─── Utility Functions ─────────────────────────────────────────────────

def _safe_str(val, default="-") -> str:
    if val is None or val == "":
        return default
    return str(val)


def _format_duration(seconds) -> str:
    if seconds is None or seconds <= 0:
        return "-"
    mins = seconds / 60
    if mins >= 60:
        hours = int(mins // 60)
        remaining = int(mins % 60)
        return f"{hours}h {remaining}m"
    return f"{round(mins, 1)}m"


def _friendly_zone_name(entity_id: str, aliases: dict, zones: list) -> str:
    """Get the best display name for a zone."""
    if not isinstance(aliases, dict):
        aliases = {}
    if entity_id in aliases:
        return aliases[entity_id]
    for z in zones:
        if z.get("entity_id") == entity_id:
            fn = z.get("friendly_name") or z.get("name", entity_id)
            return fn.replace("_", " ").title()
    return entity_id.split(".", 1)[-1].replace("_", " ").title()


def _hours_label(hours: int) -> str:
    if hours <= 24:
        return "Last 24 Hours"
    elif hours <= 168:
        return "Last 7 Days"
    elif hours <= 720:
        return "Last 30 Days"
    elif hours <= 2160:
        return "Last 90 Days"
    else:
        return "Last Year"


def _format_timestamp(iso_str: str, fmt: str = "%Y-%m-%d %H:%M") -> str:
    if not iso_str:
        return "-"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime(fmt)
    except Exception:
        return str(iso_str)[:16]


# ─── PDF Builder Class ────────────────────────────────────────────────

# Page geometry constants
_PAGE_W = 215.9   # letter width mm
_MARGIN = 15
_CW = _PAGE_W - 2 * _MARGIN  # 185.9 mm content width
_ROW_H = 5.5      # standard table row height
_HDR_H = 6.5      # table header row height


class FluxReport(FPDF):
    """Professional PDF report with branding, headers, footers, and styled tables."""

    def __init__(self, company_name: str = "", custom_footer: str = "", accent_rgb: tuple = None):
        super().__init__(orientation="P", unit="mm", format="letter")
        self.set_auto_page_break(auto=True, margin=22)
        self._page_width = _PAGE_W
        self._margin = _MARGIN
        self.set_left_margin(self._margin)
        self.set_right_margin(self._margin)
        self._content_width = _CW
        self._is_first_page = True
        # Branding overrides
        self._company_name = company_name or ""
        self._custom_footer = custom_footer or ""
        self._accent_rgb = accent_rgb or GREEN_PRIMARY

    def header(self):
        if self._is_first_page:
            return
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*TEXT_LIGHT)
        self.set_draw_color(*self._accent_rgb)
        self.set_line_width(0.4)
        self.line(self._margin, 12, self._page_width - self._margin, 12)
        self.set_xy(self._margin, 6)
        header_text = f"{self._company_name}  |  System Report" if self._company_name else "Flux Open Home  |  System Report"
        self.cell(self._content_width / 2, 5, header_text, align="L")
        self.cell(self._content_width / 2, 5,
                  f"Generated {datetime.now().strftime('%b %d, %Y')}", align="R")
        self.set_y(16)

    def footer(self):
        self.set_y(-16)
        self.set_draw_color(*DIVIDER_COLOR)
        self.set_line_width(0.3)
        self.line(self._margin, self.get_y(), self._page_width - self._margin, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*TEXT_LIGHT)
        gophr_shown = False
        if os.path.exists(_GOPHR_LOGO):
            try:
                self.image(_GOPHR_LOGO, x=self._margin, y=self.get_y() - 1, h=6)
                gophr_shown = True
            except Exception:
                pass
        footer_x = self._margin + 25 if gophr_shown else self._margin
        self.set_xy(footer_x, self.get_y())
        footer_text = self._custom_footer if self._custom_footer else "Powered by Flux Open Home & Gophr"
        self.cell(60, 5, footer_text, align="L")
        self.set_xy(self._margin, self.get_y())
        self.cell(self._content_width, 5, f"Page {self.page_no()}/{{nb}}", align="R")

    # ── Helpers ──────────────────────────────────────────────────

    def _remaining(self) -> float:
        """Remaining vertical space before auto page break."""
        return 279.4 - 22 - self.get_y()  # letter height - bottom margin - current y

    def _ensure_space(self, needed: float):
        """Add a page break if not enough space remains for the given content."""
        if self._remaining() < needed:
            self.add_page()

    # ── Section & Layout Helpers ──────────────────────────────────

    def section_header(self, title: str):
        """Accent-colored bar section header."""
        self._ensure_space(20)
        self.ln(2)
        y = self.get_y()
        self.set_fill_color(*self._accent_rgb)
        self.rect(self._margin, y, self._content_width, 8, "F")
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 10)
        self.set_xy(self._margin + 3, y + 1)
        self.cell(self._content_width - 6, 6, title)
        self.set_xy(self._margin, y + 8)
        self.ln(3)
        self.set_text_color(*TEXT_DARK)

    def sub_header(self, title: str):
        """Smaller sub-section with accent left bar."""
        self._ensure_space(15)
        y = self.get_y()
        self.set_fill_color(*self._accent_rgb)
        self.rect(self._margin, y, 2, 5.5, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self._accent_rgb)
        self.set_xy(self._margin + 4, y)
        self.cell(self._content_width - 4, 5.5, title)
        self.set_xy(self._margin, y + 5.5)
        self.ln(1.5)
        self.set_text_color(*TEXT_DARK)

    def key_value(self, key: str, value: str, key_width: int = 50):
        """Styled key: value pair."""
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*TEXT_MUTED)
        self.set_x(self._margin)
        self.cell(key_width, 5, key, new_x="END")
        self.set_font("Helvetica", "", 8.5)
        self.set_text_color(*TEXT_DARK)
        self.cell(0, 5, str(value), new_x="LMARGIN", new_y="NEXT")

    def table_header(self, cols: list):
        """Table header row. cols = [(label, width), ...]."""
        if self._remaining() < _HDR_H + _ROW_H + 2:
            self.add_page()
        self.set_auto_page_break(auto=False)
        self.set_fill_color(*self._accent_rgb)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 7.5)
        y = self.get_y()
        x = self._margin
        for label, w in cols:
            self.set_xy(x, y)
            self.cell(w, _HDR_H, "  " + label, fill=True)
            x += w
        self.set_xy(self._margin, y + _HDR_H)
        self.ln(0.3)
        self.set_text_color(*TEXT_DARK)
        self.set_auto_page_break(auto=True, margin=22)

    def table_row(self, cells: list, widths: list, shade: bool = False):
        """Single table data row with alternating shading."""
        # Pre-check page break BEFORE drawing — avoids fpdf2 auto-break
        # interfering with absolute XY positioning within the row
        if self._remaining() < _ROW_H + 1:
            self.add_page()
        # Temporarily disable auto page break so set_xy works correctly
        self.set_auto_page_break(auto=False)
        if shade:
            self.set_fill_color(*TABLE_ROW_ALT)
        else:
            self.set_fill_color(*TABLE_ROW_NORMAL)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*TEXT_DARK)
        y = self.get_y()
        x = self._margin
        for i, val in enumerate(cells):
            w = widths[i] if i < len(widths) else 20
            text = str(val) if val is not None else "-"
            max_chars = max(int(w / 1.8), 6)
            if len(text) > max_chars:
                text = text[:max_chars - 2] + ".."
            self.set_xy(x, y)
            self.cell(w, _ROW_H, "  " + text, fill=True)
            x += w
        self.set_xy(self._margin, y + _ROW_H)
        self.set_auto_page_break(auto=True, margin=22)

    def info_line(self, text: str, bold: bool = False, indent: int = 4):
        """Single line of info text."""
        style = "B" if bold else ""
        self.set_font("Helvetica", style, 8)
        self.set_x(self._margin + indent)
        self.cell(0, 4.5, text, new_x="LMARGIN", new_y="NEXT")

    def divider(self):
        """Subtle horizontal divider."""
        self.ln(1)
        self.set_draw_color(*DIVIDER_COLOR)
        self.set_line_width(0.2)
        y = self.get_y()
        self.line(self._margin + 10, y, self._page_width - self._margin - 10, y)
        self.ln(2)

    def spacer(self, h: float = 3):
        self.ln(h)


# ─── Column width helpers ─────────────────────────────────────────────
# All column widths are defined here so they add up to _CW exactly.

def _scale_cols(raw: list) -> list:
    """Scale column tuples so widths sum to exactly _CW."""
    total = sum(w for _, w in raw)
    scale = _CW / total
    return [(label, round(w * scale, 1)) for label, w in raw]


# ─── Report Builder ───────────────────────────────────────────────────

def _lighten(rgb: tuple, amount: float = 0.5) -> tuple:
    """Lighten an RGB color toward white. amount=0 is original, amount=1 is white."""
    r, g, b = rgb
    return (
        int(r + (255 - r) * amount),
        int(g + (255 - g) * amount),
        int(b + (255 - b) * amount),
    )


def build_report(
    status: dict,
    zones: list,
    zone_aliases: dict,
    zone_heads: dict,
    sensors: list,
    weather: dict,
    moisture: dict,
    issues: list,
    history: list,
    hours: int,
    water_settings: dict = None,
    report_settings: dict = None,
    custom_logo_bytes: bytes = None,
) -> FPDF:
    """Build the complete professional system report PDF."""
    # Defensive type checks
    if not isinstance(zone_heads, dict):
        zone_heads = {}
    if not isinstance(zone_aliases, dict):
        zone_aliases = {}

    # Parse report branding settings
    rs = report_settings or {}
    company_name = rs.get("company_name", "") or ""
    custom_footer = rs.get("custom_footer", "") or ""
    accent_hex = rs.get("accent_color", "#1a7a4c") or "#1a7a4c"
    hidden_sections = set(rs.get("hidden_sections", []))

    # Parse accent color
    from report_settings import hex_to_rgb
    accent_rgb = hex_to_rgb(accent_hex)
    accent_light = _lighten(accent_rgb, 0.75)
    accent_accent = _lighten(accent_rgb, 0.4)

    # Prepare custom logo as temp file if provided
    custom_logo_path = None
    if custom_logo_bytes:
        import tempfile
        tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tf.write(custom_logo_bytes)
        tf.close()
        custom_logo_path = tf.name

    pdf = FluxReport(
        company_name=company_name,
        custom_footer=custom_footer,
        accent_rgb=accent_rgb,
    )
    pdf.alias_nb_pages()

    # ══════════════════════════════════════════════════════════════════
    #  COVER / TITLE PAGE
    # ══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf._is_first_page = True

    # Accent-colored top band
    pdf.set_fill_color(*accent_rgb)
    pdf.rect(0, 0, _PAGE_W, 5, "F")

    # Logo — custom logo takes prime position, or default Flux logo
    logo_y = 22
    _used_custom_logo = False
    if custom_logo_path and os.path.exists(custom_logo_path):
        try:
            logo_w = 100
            logo_x = (_PAGE_W - logo_w) / 2
            pdf.image(custom_logo_path, x=logo_x, y=logo_y, w=logo_w)
            logo_y += 30
            _used_custom_logo = True
        except Exception:
            logo_y = 22
    elif os.path.exists(_FLUX_LOGO):
        try:
            logo_w = 100
            logo_x = (_PAGE_W - logo_w) / 2
            pdf.image(_FLUX_LOGO, x=logo_x, y=logo_y, w=logo_w)
            logo_y += 30
        except Exception:
            logo_y = 22

    # Title text — centered
    pdf.set_y(logo_y + 4)
    pdf.set_font("Helvetica", "", 24)
    pdf.set_text_color(*accent_rgb)
    pdf.cell(_CW, 12, "System Report", new_x="LMARGIN", new_y="NEXT", align="C")

    # Decorative line under title
    pdf.set_draw_color(*accent_accent)
    pdf.set_line_width(0.8)
    cx = _PAGE_W / 2
    line_y = pdf.get_y() + 1
    pdf.line(cx - 35, line_y, cx + 35, line_y)
    pdf.ln(7)

    # Report metadata — centered
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.cell(_CW, 6, f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(_CW, 6, f"Report Period: {_hours_label(hours)}",
             new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)

    # Property Info Box
    name_parts = []
    if status.get("first_name"):
        name_parts.append(status["first_name"])
    if status.get("last_name"):
        name_parts.append(status["last_name"])

    has_property_info = name_parts or status.get("address") or status.get("phone")
    if has_property_info:
        # Calculate box height based on content
        info_lines = 0
        if name_parts:
            info_lines += 1
        if status.get("address"):
            info_lines += 1
        city_parts = []
        if status.get("city"):
            city_parts.append(status["city"])
        if status.get("state"):
            city_parts.append(status["state"])
        if status.get("zip"):
            city_parts.append(status["zip"])
        if city_parts:
            info_lines += 1
        if status.get("phone"):
            info_lines += 1
        box_h = max(info_lines * 7 + 8, 28)

        box_x = _MARGIN + 30
        box_w = _CW - 60
        box_y = pdf.get_y()

        # Light accent box
        pdf.set_fill_color(*accent_light)
        pdf.rect(box_x, box_y, box_w, box_h, "F")
        # Accent left bar
        pdf.set_fill_color(*accent_rgb)
        pdf.rect(box_x, box_y, 2, box_h, "F")

        inner_y = box_y + 4
        pdf.set_y(inner_y)
        if name_parts:
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(*TEXT_DARK)
            pdf.cell(_CW, 7, " ".join(name_parts), new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*TEXT_DARK)
        if status.get("address"):
            pdf.cell(_CW, 6, status["address"], new_x="LMARGIN", new_y="NEXT", align="C")
        if city_parts:
            pdf.cell(_CW, 6, ", ".join(city_parts), new_x="LMARGIN", new_y="NEXT", align="C")
        if status.get("phone"):
            pdf.set_text_color(*TEXT_MUTED)
            pdf.cell(_CW, 6, status["phone"], new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_y(box_y + box_h + 4)

    # "Powered by Flux Open Home" — shown when a custom logo is used
    if _used_custom_logo and os.path.exists(_FLUX_LOGO):
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(_CW, 4, "Powered by", new_x="LMARGIN", new_y="NEXT", align="C")
        try:
            small_w = 45
            small_x = (_PAGE_W - small_w) / 2
            pdf.image(_FLUX_LOGO, x=small_x, y=pdf.get_y(), w=small_w)
            pdf.ln(14)
        except Exception:
            pass

    # Gophr logo centered
    if os.path.exists(_GOPHR_LOGO):
        try:
            gophr_w = 55
            gophr_x = (_PAGE_W - gophr_w) / 2
            pdf.image(_GOPHR_LOGO, x=gophr_x, y=pdf.get_y(), w=gophr_w)
            pdf.ln(22)
        except Exception:
            pass

    # Quick stats row
    pdf.ln(4)
    pdf.set_draw_color(*DIVIDER_COLOR)
    pdf.set_line_width(0.3)
    line_y = pdf.get_y()
    pdf.line(_MARGIN + 20, line_y, _PAGE_W - _MARGIN - 20, line_y)
    pdf.ln(4)

    stat_width = _CW / 4
    stat_items = [
        (str(status.get("total_zones", 0)), "Zones"),
        (f"{status.get('weather_multiplier', 1.0)}x", "Weather Factor"),
        ("Active" if not status.get("system_paused") else "Paused", "System"),
        ("Yes" if status.get("moisture_enabled") else "No", "Moisture Probes"),
    ]
    stats_y = pdf.get_y()
    for idx, (val, label) in enumerate(stat_items):
        col_x = _MARGIN + idx * stat_width
        pdf.set_xy(col_x, stats_y)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(*accent_rgb)
        pdf.cell(stat_width, 9, val, align="C")
        pdf.set_xy(col_x, stats_y + 9)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(stat_width, 5, label, align="C")
    pdf.set_y(stats_y + 18)

    # ══════════════════════════════════════════════════════════════════
    #  CONTENT PAGES
    # ══════════════════════════════════════════════════════════════════
    pdf._is_first_page = False
    pdf.add_page()

    # ── System Status ─────────────────────────────────────────────
    if "system_status" not in hidden_sections:
        pdf.section_header("System Status")
        pdf.key_value("HA Connection", "Connected" if status.get("ha_connected") else "Disconnected")
        pdf.key_value("System State", "Paused" if status.get("system_paused") else "Active")
        pdf.key_value("Total Zones", str(status.get("total_zones", 0)))
        pdf.key_value("Active Zones", str(status.get("active_zones", 0)))
        pdf.key_value("Total Sensors", str(status.get("total_sensors", 0)))
        pdf.key_value("Weather Multiplier", f"{status.get('weather_multiplier', 1.0)}x")
        pdf.key_value("Moisture Probes", "Enabled" if status.get("moisture_enabled") else "Disabled")
        if status.get("rain_delay_active"):
            pdf.key_value("Rain Delay", f"Active until {_format_timestamp(status.get('rain_delay_until', ''))}")
        pdf.spacer(4)

    # ── Issues ────────────────────────────────────────────────────
    if "issues" not in hidden_sections and issues:
        cols = _scale_cols([("Severity", 25), ("Status", 22), ("Description", 82), ("Reported", 28), ("Service Date", 30)])
        widths = [w for _, w in cols]
        pdf.section_header(f"Issues ({len(issues)})")
        pdf.table_header(cols)
        for i, issue in enumerate(issues):
            sev = _safe_str(issue.get("severity", "")).capitalize()
            stat = _safe_str(issue.get("status", "")).capitalize()
            desc = _safe_str(issue.get("description", ""))
            created = _format_timestamp(issue.get("created_at", ""), "%Y-%m-%d")
            svc_date = _safe_str(issue.get("service_date"))
            pdf.table_row([sev, stat, desc, created, svc_date], widths, shade=(i % 2 == 1))
        pdf.spacer(4)

    # ── Zones Overview ────────────────────────────────────────────
    if "zones" not in hidden_sections:
        cols = _scale_cols([("Zone", 55), ("State", 20), ("GPM", 20), ("Heads", 18), ("Notes", 73)])
        widths = [w for _, w in cols]
        pdf.section_header(f"Zones ({len(zones)})")
        pdf.table_header(cols)
        for i, z in enumerate(zones):
            eid = z.get("entity_id", "")
            name = _friendly_zone_name(eid, zone_aliases, zones)
            state = _safe_str(z.get("state", "")).capitalize()
            heads_data = zone_heads.get(eid, {})
            gpm = "-"
            head_count = "-"
            notes = "-"
            if heads_data:
                total_gpm = heads_data.get("total_gpm", 0)
                gpm = str(round(total_gpm, 1)) if total_gpm > 0 else "-"
                heads_list = heads_data.get("heads", [])
                head_count = str(len(heads_list)) if heads_list else "-"
                notes = _safe_str(heads_data.get("notes", ""))
            pdf.table_row([name, state, gpm, head_count, notes], widths, shade=(i % 2 == 1))
        pdf.spacer(4)

    # ── Zone Head/Nozzle Details ──────────────────────────────────
    zones_with_heads = [(z, zone_heads.get(z.get("entity_id", ""), {}))
                        for z in zones if zone_heads.get(z.get("entity_id", ""), {}).get("heads")]
    if "zone_heads" not in hidden_sections and zones_with_heads:
        pdf.section_header("Zone Head & Nozzle Details")
        head_cols = _scale_cols([("Type", 30), ("GPM", 16), ("Arc", 18), ("Radius", 18),
                                 ("Height", 16), ("PSI", 14), ("Brand", 28), ("Model", 46)])
        head_widths = [w for _, w in head_cols]
        for z, hd in zones_with_heads:
            eid = z.get("entity_id", "")
            name = _friendly_zone_name(eid, zone_aliases, zones)
            total_gpm = hd.get("total_gpm", 0)
            head_count = len(hd.get("heads", []))
            pdf.sub_header(f"{name}  ({head_count} head{'s' if head_count != 1 else ''}, {round(total_gpm, 1)} GPM)")
            if hd.get("notes"):
                pdf.set_font("Helvetica", "I", 7.5)
                pdf.set_text_color(*TEXT_MUTED)
                pdf.set_x(pdf._margin + 6)
                pdf.cell(0, 4, f"Notes: {hd['notes']}", new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(*TEXT_DARK)
                pdf.ln(0.5)
            pdf.table_header(head_cols)
            for j, head in enumerate(hd.get("heads", [])):
                pdf.table_row([
                    _safe_str(head.get("nozzle_type")),
                    _safe_str(head.get("gpm")),
                    _safe_str(head.get("spray_arc")),
                    _safe_str(head.get("radius")),
                    _safe_str(head.get("popup_height")),
                    _safe_str(head.get("psi")),
                    _safe_str(head.get("brand")),
                    _safe_str(head.get("model")),
                ], head_widths, shade=(j % 2 == 1))
            pdf.spacer(3)
        pdf.spacer(2)

    # ── Weather Settings ──────────────────────────────────────────
    if "weather" not in hidden_sections and weather.get("weather_enabled"):
        pdf.section_header("Weather-Based Control")
        wx = weather.get("weather", {})
        pdf.key_value("Condition", _safe_str(wx.get("condition", "")).capitalize())
        if wx.get("temperature") is not None:
            unit = wx.get("temperature_unit", "F")
            pdf.key_value("Temperature", f"{wx['temperature']}{unit}")
        if wx.get("humidity") is not None:
            pdf.key_value("Humidity", f"{wx['humidity']}%")
        if wx.get("wind_speed") is not None:
            unit = wx.get("wind_speed_unit", "mph")
            pdf.key_value("Wind Speed", f"{wx['wind_speed']} {unit}")
        pdf.key_value("Watering Multiplier", f"{weather.get('watering_multiplier', 1.0)}x")

        # Active adjustments
        adjustments = weather.get("active_adjustments", [])
        if adjustments:
            pdf.spacer(1)
            pdf.sub_header("Active Adjustments")
            for adj in adjustments:
                rule = _safe_str(adj.get("rule", "")).replace("_", " ").title()
                action = _safe_str(adj.get("action", ""))
                reason = _safe_str(adj.get("reason", ""))
                pdf.info_line(f"{rule}:  {action} - {reason}", indent=6)

        # Rules summary
        rules = weather.get("rules", {})
        if not isinstance(rules, dict):
            rules = {}
        enabled_rules = [(k, v) for k, v in rules.items()
                         if isinstance(v, dict) and v.get("enabled")]
        if enabled_rules:
            pdf.spacer(1)
            pdf.sub_header("Enabled Weather Rules")
            for rule_name, rule_data in enabled_rules:
                label = rule_name.replace("_", " ").title()
                pdf.info_line(f"{label}", indent=6)
        pdf.spacer(4)

    # ── Moisture Probes ───────────────────────────────────────────
    if "moisture" not in hidden_sections and moisture.get("enabled"):
        pdf.section_header("Moisture Probes")
        probes = moisture.get("probes", {})
        if not isinstance(probes, dict):
            probes = {}
        if probes:
            for probe_id, probe_data in probes.items():
                label = probe_data.get("display_name") or probe_id.replace("_", " ").title()
                pdf.sub_header(f"Probe: {label}")
                mappings = probe_data.get("zone_mappings", [])
                if mappings:
                    mapped_names = []
                    for eid in mappings:
                        mapped_names.append(_friendly_zone_name(eid, zone_aliases, zones))
                    pdf.info_line(f"Mapped zones: {', '.join(mapped_names)}", indent=6)
                thresholds = probe_data.get("thresholds", {})
                if thresholds:
                    pdf.info_line(f"Saturation: {thresholds.get('saturated', 'N/A')}%  |  Dry: {thresholds.get('dry', 'N/A')}%", indent=6)
                pdf.spacer(1.5)
        else:
            pdf.info_line("No moisture probes configured.")
        pdf.spacer(3)

    # ── Sensors ───────────────────────────────────────────────────
    if "sensors" not in hidden_sections and sensors:
        cols = _scale_cols([("Sensor", 60), ("Value", 28), ("Unit", 28), ("Last Updated", 50)])
        widths = [w for _, w in cols]
        pdf.section_header(f"Sensors ({len(sensors)})")
        pdf.table_header(cols)
        for i, s in enumerate(sensors):
            name = s.get("friendly_name") or s.get("name", s.get("entity_id", ""))
            val = _safe_str(s.get("state"))
            unit = _safe_str(s.get("unit_of_measurement", ""))
            updated = _format_timestamp(s.get("last_updated", ""))
            pdf.table_row([name, val, unit, updated], widths, shade=(i % 2 == 1))
        pdf.spacer(4)

    # ── Estimated Water Usage ─────────────────────────────────────
    zone_gpm_map = {}
    for eid, hd in zone_heads.items():
        total_gpm = hd.get("total_gpm", 0)
        if total_gpm > 0:
            zone_gpm_map[eid] = total_gpm

    if "water_usage" not in hidden_sections and zone_gpm_map:
        zone_gallons = {}
        zone_minutes = {}
        total_gallons = 0.0
        total_minutes = 0.0

        for event in history:
            eid = event.get("entity_id", "")
            dur = event.get("duration_seconds")
            if dur and dur > 0 and eid in zone_gpm_map:
                gpm = zone_gpm_map[eid]
                mins = dur / 60.0
                gals = mins * gpm
                zone_gallons[eid] = zone_gallons.get(eid, 0) + gals
                zone_minutes[eid] = zone_minutes.get(eid, 0) + mins
                total_gallons += gals
                total_minutes += mins

        if total_gallons > 0:
            pdf.section_header(f"Estimated Water Usage  -  {_hours_label(hours)}")
            pdf.spacer(1)
            pdf.set_font("Helvetica", "B", 20)
            pdf.set_text_color(*accent_rgb)
            pdf.cell(_CW, 10, f"{total_gallons:,.1f} gallons", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*TEXT_MUTED)
            pdf.cell(_CW, 5, f"Total run time: {_format_duration(total_minutes * 60)}",
                     new_x="LMARGIN", new_y="NEXT", align="C")

            # Water source info
            ws = water_settings or {}
            ws_label = {"city": "City Water", "reclaimed": "Reclaimed Water", "well": "Well Water"}.get(
                ws.get("water_source", ""), "")
            if ws_label:
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(*TEXT_MUTED)
                pdf.cell(_CW, 5, f"Source: {ws_label}", new_x="LMARGIN", new_y="NEXT", align="C")

            # Water cost (city/reclaimed only)
            cost_per_1k = float(ws.get("cost_per_1000_gal", 0) or 0)
            if cost_per_1k > 0 and ws.get("water_source") in ("city", "reclaimed"):
                water_cost = (total_gallons / 1000) * cost_per_1k
                pdf.set_font("Helvetica", "B", 14)
                pdf.set_text_color(*accent_rgb)
                pdf.cell(_CW, 7, f"Estimated Water Cost: ${water_cost:,.2f}", new_x="LMARGIN", new_y="NEXT", align="C")
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(*TEXT_MUTED)
                pdf.cell(_CW, 4, f"(${cost_per_1k:.2f} per 1,000 gallons)", new_x="LMARGIN", new_y="NEXT", align="C")

            pdf.set_text_color(*TEXT_DARK)
            pdf.spacer(3)

            cols = _scale_cols([("Zone", 65), ("Run Time", 30), ("GPM", 25), ("Est. Gallons", 35)])
            widths = [w for _, w in cols]
            pdf.table_header(cols)
            sorted_zones = sorted(zone_gallons.items(), key=lambda x: x[1], reverse=True)
            for i, (eid, gals) in enumerate(sorted_zones):
                name = _friendly_zone_name(eid, zone_aliases, zones)
                mins = zone_minutes.get(eid, 0)
                gpm = zone_gpm_map.get(eid, 0)
                pdf.table_row(
                    [name, _format_duration(mins * 60), str(round(gpm, 1)), f"{gals:,.1f}"],
                    widths, shade=(i % 2 == 1)
                )
            pdf.spacer(4)

    # ── Run History ───────────────────────────────────────────────
    if "run_history" not in hidden_sections and history:
        on_events = [e for e in history if e.get("duration_seconds") and e["duration_seconds"] > 0]
        pdf.section_header(f"Run History  -  {_hours_label(hours)}")
        pdf.key_value("Total Events", str(len(history)))
        pdf.key_value("Completed Runs", str(len(on_events)))
        total_dur = sum(e.get("duration_seconds", 0) for e in on_events)
        pdf.key_value("Total Run Time", _format_duration(total_dur))
        pdf.spacer(2)

        # Recent events table (limit 100)
        recent = history[:100]
        if recent:
            label = f"Recent Events (showing {len(recent)} of {len(history)})" if len(history) > 100 else f"All Events ({len(history)})"
            pdf.sub_header(label)
            cols = _scale_cols([("Time", 30), ("Zone", 42), ("State", 14), ("Duration", 22),
                                ("Source", 24), ("Weather", 24), ("Factor", 18)])
            widths = [w for _, w in cols]
            pdf.table_header(cols)
            for i, e in enumerate(recent):
                ts = _format_timestamp(e.get("timestamp", ""), "%m/%d %H:%M")
                eid = e.get("entity_id", "")
                name = _friendly_zone_name(eid, zone_aliases, zones)
                state = _safe_str(e.get("state", "")).upper()
                dur = _format_duration(e.get("duration_seconds"))
                source = _safe_str(e.get("source", "")).replace("_", " ").title()
                wx_cond = ""
                wx = e.get("weather")
                if wx and isinstance(wx, dict):
                    wx_cond = _safe_str(wx.get("condition", "")).capitalize()
                factor = ""
                if wx and isinstance(wx, dict) and wx.get("watering_multiplier") is not None:
                    factor = f"{wx['watering_multiplier']}x"
                pdf.table_row([ts, name, state, dur, source, wx_cond, factor],
                              widths, shade=(i % 2 == 1))
        pdf.spacer(4)

    # ── End Page ──────────────────────────────────────────────────
    pdf.divider()
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(_CW, 5, "End of Report", new_x="LMARGIN", new_y="NEXT", align="C")
    if company_name:
        pdf.cell(_CW, 5, f"{company_name}  |  System Report",
                 new_x="LMARGIN", new_y="NEXT", align="C")
    else:
        pdf.cell(_CW, 5, "Flux Open Home Irrigation Control  |  gophr.com",
                 new_x="LMARGIN", new_y="NEXT", align="C")

    # Cleanup temp logo file
    if custom_logo_path:
        try:
            os.unlink(custom_logo_path)
        except Exception:
            pass

    return pdf


# ─── API Endpoint ──────────────────────────────────────────────────────

@router.get("/pdf", summary="Generate system report PDF")
async def generate_report_pdf(
    hours: int = Query(720, ge=1, le=8760, description="Hours of history (max 1 year)"),
):
    """Generate a comprehensive system report as a downloadable PDF."""
    import traceback
    try:
        # Gather all data
        status = await _get_status()
        zones = await _get_zones()
        zone_aliases = _get_zone_aliases()
        zone_heads = _get_all_zone_heads()
        sensors = await _get_sensors()
        weather = await _get_weather()
        moisture = _get_moisture()
        issues = _get_issues()
        history = run_log.get_run_history(hours=hours)

        # Water source settings
        try:
            import water_data
            water_settings = water_data.get_water_settings()
        except Exception:
            water_settings = {}

        # Report branding settings
        try:
            import report_settings as rs_mod
            rs = rs_mod.get_report_settings()
            logo_path = rs_mod.get_logo_path()
            custom_logo_bytes = None
            if logo_path:
                with open(logo_path, "rb") as f:
                    custom_logo_bytes = f.read()
        except Exception:
            rs = {}
            custom_logo_bytes = None

        # Build PDF
        pdf = build_report(
            status, zones, zone_aliases, zone_heads,
            sensors, weather, moisture, issues, history, hours,
            water_settings=water_settings,
            report_settings=rs,
            custom_logo_bytes=custom_logo_bytes,
        )

        # Return as downloadable PDF
        pdf_bytes = bytes(pdf.output())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="flux_system_report_{timestamp}.pdf"',
            },
        )
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[REPORT PDF] Error generating report: {e}\n{tb}")
        # Extract last line number from traceback for easier debugging
        tb_lines = [l.strip() for l in tb.strip().split("\n") if l.strip()]
        location = ""
        for tl in reversed(tb_lines):
            if tl.startswith("File "):
                location = f" [{tl}]"
                break
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate PDF report: {str(e)}{location}"},
        )
