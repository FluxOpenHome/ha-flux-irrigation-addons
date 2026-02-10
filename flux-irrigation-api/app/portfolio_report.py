"""
Flux Open Home - Portfolio Statistics Report
=============================================
Generates a cross-customer portfolio analysis PDF.  Aggregates data
from all connected customer instances and renders comparative
statistics, tables, and recommendations via fpdf2.

Reuses the FluxReport class from report_pdf.py for consistent styling.
"""

import os
import tempfile
from datetime import datetime, timedelta
from collections import Counter

from fpdf import FPDF
from report_settings import hex_to_rgb

# Reuse FluxReport class and constants from the per-customer report
from routes.report_pdf import (
    FluxReport,
    _PAGE_W,
    _MARGIN,
    _CW,
    _ROW_H,
    _HDR_H,
    _lighten,
    _scale_cols,
    _hours_label,
    _format_duration,
    _safe_str,
    GREEN_PRIMARY,
    GREEN_ACCENT,
    GREEN_LIGHT,
    TEXT_DARK,
    TEXT_MUTED,
    TEXT_LIGHT,
    WHITE,
    DIVIDER_COLOR,
    SEVERITY_COLORS,
)

# Logo paths
_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
_FLUX_LOGO = os.path.join(_ASSETS_DIR, "flux_logo.png")
_GOPHR_LOGO = os.path.join(_ASSETS_DIR, "gophr_logo.jpg")


# ─── Data Aggregation ────────────────────────────────────────────────


def _compute_portfolio_stats(customer_data: list, hours: int) -> dict:
    """Pre-compute all aggregate statistics from raw customer data."""
    total = len(customer_data)
    online = sum(1 for c in customer_data if c.get("online"))
    offline = total - online

    # Zones
    total_zones = 0
    zone_counts = []
    for c in customer_data:
        zones = c.get("zones", [])
        if isinstance(zones, list):
            n = len(zones)
        elif isinstance(zones, dict):
            n = zones.get("count", 0)
        else:
            n = 0
        total_zones += n
        zone_counts.append(n)
    avg_zones = round(total_zones / total, 1) if total else 0

    # Moisture probes
    properties_with_probes = 0
    total_probes = 0
    total_mapped_zones = 0
    total_zones_for_probe_props = 0
    for c in customer_data:
        moisture = c.get("moisture", {})
        if not isinstance(moisture, dict):
            continue
        probes = moisture.get("probes", {})
        if isinstance(probes, dict) and len(probes) > 0:
            properties_with_probes += 1
            total_probes += len(probes)
            # Count mapped zones
            for probe in probes.values():
                mapped = probe.get("mapped_zones", [])
                if isinstance(mapped, list):
                    total_mapped_zones += len(mapped)
            # Zone count for this property
            zones = c.get("zones", [])
            if isinstance(zones, list):
                total_zones_for_probe_props += len(zones)

    # Weather
    weather_enabled_count = 0
    weather_factors = []
    rain_skip_count = 0
    freeze_count = 0
    for c in customer_data:
        w = c.get("weather", {})
        if not isinstance(w, dict):
            continue
        if w.get("weather_enabled"):
            weather_enabled_count += 1
            mult = w.get("watering_multiplier")
            if mult is not None:
                try:
                    weather_factors.append(float(mult))
                except (ValueError, TypeError):
                    pass
            # Check active adjustments for rain/freeze
            adj = w.get("active_adjustments", [])
            if isinstance(adj, list):
                for a in adj:
                    reason = (a.get("reason", "") or "").lower() if isinstance(a, dict) else ""
                    if "rain" in reason:
                        rain_skip_count += 1
                    if "freeze" in reason or "cold" in reason:
                        freeze_count += 1

    avg_weather_factor = round(sum(weather_factors) / len(weather_factors), 2) if weather_factors else 1.0

    # Issues
    total_issues = 0
    severe_count = 0
    annoyance_count = 0
    clarification_count = 0
    healthy_count = 0
    issue_type_counter = Counter()
    for c in customer_data:
        issues = c.get("issues", [])
        if not isinstance(issues, list):
            issues = []
        n = len(issues)
        total_issues += n
        if n == 0:
            healthy_count += 1
        for iss in issues:
            if isinstance(iss, dict):
                sev = (iss.get("severity", "") or "").lower()
                if sev == "severe":
                    severe_count += 1
                elif sev == "annoyance":
                    annoyance_count += 1
                else:
                    clarification_count += 1
                itype = iss.get("type", "Unknown")
                issue_type_counter[itype] += 1

    # Run history
    total_runs = 0
    run_counts = []
    total_run_seconds = 0
    run_count_for_avg = 0
    last_run_per_prop = []
    for c in customer_data:
        history = c.get("history", [])
        if not isinstance(history, list):
            history = []
        n = len(history)
        total_runs += n
        run_counts.append(n)
        last_ts = None
        for evt in history:
            if isinstance(evt, dict):
                dur = evt.get("duration_seconds")
                if dur:
                    try:
                        total_run_seconds += float(dur)
                        run_count_for_avg += 1
                    except (ValueError, TypeError):
                        pass
                ts = evt.get("start_time") or evt.get("timestamp")
                if ts and (not last_ts or ts > last_ts):
                    last_ts = ts
        last_run_per_prop.append(last_ts)

    days = hours / 24
    avg_runs_per_prop_per_day = round(total_runs / (total * days), 1) if total and days else 0
    avg_run_duration_s = total_run_seconds / run_count_for_avg if run_count_for_avg else 0

    # Water usage estimation
    total_gallons = 0.0
    gallons_per_prop = []
    water_sources = Counter()
    for c in customer_data:
        prop_gallons = 0.0
        zone_heads = c.get("zone_heads", {})
        if not isinstance(zone_heads, dict):
            zone_heads = {}
        history = c.get("history", [])
        if not isinstance(history, list):
            history = []

        # Build GPM lookup from zone_heads
        gpm_map = {}
        for entity_id, head_data in zone_heads.items():
            if isinstance(head_data, dict):
                total_gpm = head_data.get("total_gpm", 0) or 0
                gpm_map[entity_id] = total_gpm

        for evt in history:
            if not isinstance(evt, dict):
                continue
            eid = evt.get("entity_id", "")
            dur = evt.get("duration_seconds", 0)
            try:
                dur = float(dur)
            except (ValueError, TypeError):
                dur = 0
            gpm = gpm_map.get(eid, 0)
            if gpm > 0 and dur > 0:
                prop_gallons += gpm * (dur / 60)

        total_gallons += prop_gallons
        gallons_per_prop.append(prop_gallons)

        # Water source
        ws = c.get("water_settings", {})
        if isinstance(ws, dict):
            source = ws.get("water_source", "Unknown") or "Unknown"
            water_sources[source] += 1

    avg_gallons = round(total_gallons / total, 1) if total else 0

    return {
        "total_properties": total,
        "online": online,
        "offline": offline,
        "total_zones": total_zones,
        "avg_zones": avg_zones,
        "zone_counts": zone_counts,
        "properties_with_probes": properties_with_probes,
        "total_probes": total_probes,
        "total_mapped_zones": total_mapped_zones,
        "total_zones_for_probe_props": total_zones_for_probe_props,
        "weather_enabled_count": weather_enabled_count,
        "avg_weather_factor": avg_weather_factor,
        "weather_factors": weather_factors,
        "rain_skip_count": rain_skip_count,
        "freeze_count": freeze_count,
        "total_issues": total_issues,
        "severe_count": severe_count,
        "annoyance_count": annoyance_count,
        "clarification_count": clarification_count,
        "healthy_count": healthy_count,
        "issue_type_counter": issue_type_counter,
        "total_runs": total_runs,
        "run_counts": run_counts,
        "avg_runs_per_prop_per_day": avg_runs_per_prop_per_day,
        "avg_run_duration_s": avg_run_duration_s,
        "last_run_per_prop": last_run_per_prop,
        "total_gallons": total_gallons,
        "avg_gallons": avg_gallons,
        "gallons_per_prop": gallons_per_prop,
        "water_sources": water_sources,
    }


def _prop_name(cdata: dict) -> str:
    """Get the display name for a customer entry."""
    cust = cdata.get("customer", {})
    return cust.get("name", "Unknown")


def _prop_location(cdata: dict) -> str:
    """Get city, state for a customer entry."""
    cust = cdata.get("customer", {})
    city = cust.get("city", "")
    state = cust.get("state", "")
    parts = [p for p in [city, state] if p]
    return ", ".join(parts) if parts else "-"


def _count_prop_zones(cdata: dict) -> int:
    zones = cdata.get("zones", [])
    if isinstance(zones, list):
        return len(zones)
    return 0


def _count_prop_probes(cdata: dict) -> int:
    moisture = cdata.get("moisture", {})
    if isinstance(moisture, dict):
        probes = moisture.get("probes", {})
        if isinstance(probes, dict):
            return len(probes)
    return 0


def _count_prop_issues(cdata: dict) -> list:
    """Return (severe, annoyance, clarification, total)."""
    issues = cdata.get("issues", [])
    if not isinstance(issues, list):
        issues = []
    sev = ann = clar = 0
    for iss in issues:
        if isinstance(iss, dict):
            s = (iss.get("severity", "") or "").lower()
            if s == "severe":
                sev += 1
            elif s == "annoyance":
                ann += 1
            else:
                clar += 1
    return [sev, ann, clar, sev + ann + clar]


def _count_prop_runs(cdata: dict) -> int:
    history = cdata.get("history", [])
    if isinstance(history, list):
        return len(history)
    return 0


def _prop_avg_run_duration(cdata: dict) -> float:
    """Average run duration in seconds for a property."""
    history = cdata.get("history", [])
    if not isinstance(history, list):
        return 0
    total = 0
    count = 0
    for evt in history:
        if isinstance(evt, dict):
            dur = evt.get("duration_seconds")
            if dur:
                try:
                    total += float(dur)
                    count += 1
                except (ValueError, TypeError):
                    pass
    return total / count if count else 0


def _prop_last_run(cdata: dict) -> str:
    """Last run timestamp string."""
    history = cdata.get("history", [])
    if not isinstance(history, list):
        return "-"
    last = None
    for evt in history:
        if isinstance(evt, dict):
            ts = evt.get("start_time") or evt.get("timestamp")
            if ts and (not last or ts > last):
                last = ts
    if last:
        try:
            dt = datetime.fromisoformat(last)
            return dt.strftime("%b %d, %Y %H:%M")
        except Exception:
            return str(last)[:16]
    return "-"


def _estimate_prop_gallons(cdata: dict) -> float:
    """Estimate total gallons for a property from zone heads GPM + run history."""
    zone_heads = cdata.get("zone_heads", {})
    if not isinstance(zone_heads, dict):
        zone_heads = {}
    history = cdata.get("history", [])
    if not isinstance(history, list):
        history = []

    gpm_map = {}
    for eid, hd in zone_heads.items():
        if isinstance(hd, dict):
            gpm_map[eid] = hd.get("total_gpm", 0) or 0

    total = 0.0
    for evt in history:
        if not isinstance(evt, dict):
            continue
        eid = evt.get("entity_id", "")
        dur = evt.get("duration_seconds", 0)
        try:
            dur = float(dur)
        except (ValueError, TypeError):
            dur = 0
        gpm = gpm_map.get(eid, 0)
        if gpm > 0 and dur > 0:
            total += gpm * (dur / 60)
    return total


def _prop_total_gpm(cdata: dict) -> float:
    """Sum of all zone GPM values for a property."""
    zone_heads = cdata.get("zone_heads", {})
    if not isinstance(zone_heads, dict):
        return 0
    total = 0.0
    for hd in zone_heads.values():
        if isinstance(hd, dict):
            total += hd.get("total_gpm", 0) or 0
    return total


def _prop_weather_enabled(cdata: dict) -> bool:
    w = cdata.get("weather", {})
    return isinstance(w, dict) and w.get("weather_enabled", False)


def _prop_weather_factor(cdata: dict) -> float:
    w = cdata.get("weather", {})
    if isinstance(w, dict):
        try:
            return float(w.get("watering_multiplier", 1.0))
        except (ValueError, TypeError):
            pass
    return 1.0


def _prop_water_source(cdata: dict) -> str:
    ws = cdata.get("water_settings", {})
    if isinstance(ws, dict):
        return ws.get("water_source", "-") or "-"
    return "-"


def _stat_box(pdf: FluxReport, x: float, y: float, value: str, label: str, accent_rgb: tuple, width: float = 40):
    """Render a stat tile (big number + small label) at absolute position."""
    box_h = 22
    accent_light = _lighten(accent_rgb, 0.85)
    pdf.set_fill_color(*accent_light)
    pdf.rect(x, y, width, box_h, "F")
    # Accent left bar
    pdf.set_fill_color(*accent_rgb)
    pdf.rect(x, y, 2, box_h, "F")

    # Big value
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*accent_rgb)
    pdf.set_xy(x + 4, y + 2)
    pdf.cell(width - 6, 10, str(value), align="C")

    # Small label
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.set_xy(x + 4, y + 13)
    pdf.cell(width - 6, 5, label, align="C")


def _horizontal_bar(pdf: FluxReport, x: float, y: float, value: float, max_value: float, bar_width: float, color: tuple, height: float = 4):
    """Draw a horizontal bar chart element."""
    if max_value <= 0:
        return
    w = min(bar_width * (value / max_value), bar_width)
    if w < 1:
        w = 1
    pdf.set_fill_color(*color)
    pdf.rect(x, y, w, height, "F")


# ─── Report Builder ──────────────────────────────────────────────────


def build_portfolio_report(
    customer_data: list,
    hours: int,
    report_settings: dict = None,
    custom_logo_bytes: bytes = None,
) -> FPDF:
    """Build the portfolio statistics report PDF."""

    # Parse settings
    rs = report_settings or {}
    company_name = rs.get("company_name", "") or ""
    custom_footer = rs.get("custom_footer", "") or ""
    accent_hex = rs.get("accent_color", "#1a7a4c") or "#1a7a4c"
    hidden_sections = set(rs.get("hidden_sections", []))

    accent_rgb = hex_to_rgb(accent_hex)
    accent_light = _lighten(accent_rgb, 0.75)
    accent_mid = _lighten(accent_rgb, 0.4)

    # Custom logo temp file
    custom_logo_path = None
    if custom_logo_bytes:
        tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tf.write(custom_logo_bytes)
        tf.close()
        custom_logo_path = tf.name

    # Create PDF
    pdf = FluxReport(
        company_name=company_name,
        custom_footer=custom_footer if custom_footer else "Powered by Flux Open Home & Gophr  |  Portfolio Report",
        accent_rgb=accent_rgb,
    )
    pdf.alias_nb_pages()

    # Pre-compute stats
    stats = _compute_portfolio_stats(customer_data, hours)

    # ── Cover Page ────────────────────────────────────────────────
    pdf.add_page()

    # Top accent band
    pdf.set_fill_color(*accent_rgb)
    pdf.rect(0, 0, _PAGE_W, 6, "F")

    # Logo
    logo_y = 22
    if custom_logo_path and os.path.exists(custom_logo_path):
        try:
            logo_w = 80
            logo_x = (_PAGE_W - logo_w) / 2
            pdf.image(custom_logo_path, x=logo_x, y=logo_y, w=logo_w)
            logo_y += 28
        except Exception:
            pass
    elif os.path.exists(_FLUX_LOGO):
        try:
            logo_w = 80
            logo_x = (_PAGE_W - logo_w) / 2
            pdf.image(_FLUX_LOGO, x=logo_x, y=logo_y, w=logo_w)
            logo_y += 28
        except Exception:
            pass

    # Title
    pdf.set_y(logo_y + 8)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*accent_rgb)
    pdf.cell(_CW, 12, "Portfolio Statistics Report", new_x="LMARGIN", new_y="NEXT", align="C")

    # Subtitle
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*TEXT_MUTED)
    subtitle = company_name if company_name else "Flux Open Home Management"
    pdf.cell(_CW, 7, subtitle, new_x="LMARGIN", new_y="NEXT", align="C")

    # Report period + date
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TEXT_DARK)
    pdf.cell(_CW, 5, _hours_label(hours), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.cell(_CW, 5, f"Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", new_x="LMARGIN", new_y="NEXT", align="C")

    # Decorative line
    pdf.ln(4)
    pdf.set_draw_color(*accent_mid)
    pdf.set_line_width(0.8)
    line_w = 80
    pdf.line((_PAGE_W - line_w) / 2, pdf.get_y(), (_PAGE_W + line_w) / 2, pdf.get_y())
    pdf.ln(6)

    # Summary stat boxes
    box_w = 40
    gap = 6
    n_boxes = 4
    total_w = n_boxes * box_w + (n_boxes - 1) * gap
    start_x = (_PAGE_W - total_w) / 2
    box_y = pdf.get_y()

    _stat_box(pdf, start_x, box_y, str(stats["total_properties"]), "Properties", accent_rgb, box_w)
    _stat_box(pdf, start_x + box_w + gap, box_y, str(stats["online"]), "Online", accent_rgb, box_w)
    _stat_box(pdf, start_x + 2 * (box_w + gap), box_y, str(stats["total_zones"]), "Total Zones", accent_rgb, box_w)
    _stat_box(pdf, start_x + 3 * (box_w + gap), box_y, str(stats["properties_with_probes"]), "With Probes", accent_rgb, box_w)

    pdf.set_y(box_y + 30)

    # "Powered by" if custom logo
    if custom_logo_path:
        pdf.ln(6)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(_CW, 4, "Powered by", new_x="LMARGIN", new_y="NEXT", align="C")
        if os.path.exists(_FLUX_LOGO):
            try:
                small_w = 45
                small_x = (_PAGE_W - small_w) / 2
                pdf.image(_FLUX_LOGO, x=small_x, y=pdf.get_y(), w=small_w)
                pdf.ln(14)
            except Exception:
                pass

    pdf._is_first_page = False

    # ── Section: Portfolio Overview ───────────────────────────────
    if "portfolio_overview" not in hidden_sections:
        pdf.add_page()
        pdf.section_header("Portfolio Overview")

        # Stat tiles row
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*TEXT_DARK)
        pdf.key_value("Total Properties", f"{stats['total_properties']}  ({stats['online']} online, {stats['offline']} offline)")
        pdf.key_value("Total Zones", str(stats["total_zones"]))
        pdf.key_value("Average Zones / Property", str(stats["avg_zones"]))
        pdf.key_value("Properties with Probes", f"{stats['properties_with_probes']} of {stats['total_properties']}")
        pdf.key_value("Weather Control Enabled", f"{stats['weather_enabled_count']} of {stats['total_properties']}")
        pdf.spacer(4)

        # Property connectivity table
        pdf.sub_header("Property Connectivity")
        cols = _scale_cols([
            ("Property", 50), ("Location", 40), ("Status", 20),
            ("Zones", 18), ("Probes", 18), ("Issues", 18),
        ])
        pdf.table_header(cols)
        widths = [c[1] for c in cols]
        for i, c in enumerate(customer_data):
            issues = _count_prop_issues(c)
            pdf.table_row([
                _prop_name(c),
                _prop_location(c),
                "Online" if c.get("online") else "Offline",
                str(_count_prop_zones(c)),
                str(_count_prop_probes(c)),
                str(issues[3]),
            ], widths, shade=(i % 2 == 0))
        pdf.spacer(4)

    # ── Section: Irrigation Activity ─────────────────────────────
    if "irrigation_activity" not in hidden_sections:
        pdf.add_page()
        pdf.section_header("Irrigation Activity")

        pdf.key_value("Total Runs (all properties)", str(stats["total_runs"]))
        pdf.key_value("Avg Runs / Property / Day", str(stats["avg_runs_per_prop_per_day"]))
        pdf.key_value("Avg Run Duration", _format_duration(stats["avg_run_duration_s"]))
        pdf.spacer(4)

        # Per-property run table
        pdf.sub_header("Runs by Property")
        cols = _scale_cols([
            ("Property", 50), ("Total Runs", 30), ("Avg Duration", 30), ("Last Run", 50),
        ])
        pdf.table_header(cols)
        widths = [c[1] for c in cols]

        # Sort by run count descending
        sorted_data = sorted(customer_data, key=lambda c: _count_prop_runs(c), reverse=True)
        max_runs = max((_count_prop_runs(c) for c in customer_data), default=1) or 1
        for i, c in enumerate(sorted_data):
            runs = _count_prop_runs(c)
            pdf.table_row([
                _prop_name(c),
                str(runs),
                _format_duration(_prop_avg_run_duration(c)),
                _prop_last_run(c),
            ], widths, shade=(i % 2 == 0))

            # Mini bar chart after each row
            bar_y = pdf.get_y() - _ROW_H + 1
            bar_x = _MARGIN + widths[0] + 2
            bar_max_w = widths[1] - 6
            if max_runs > 0 and runs > 0:
                _horizontal_bar(pdf, bar_x, bar_y, runs, max_runs, bar_max_w, accent_light, 3)

        pdf.spacer(4)

    # ── Section: Water Usage ─────────────────────────────────────
    if "water_usage" not in hidden_sections:
        pdf.add_page()
        pdf.section_header("Estimated Water Usage")

        pdf.key_value("Total Est. Gallons (portfolio)", f"{stats['total_gallons']:,.0f} gal")
        pdf.key_value("Avg Gallons / Property", f"{stats['avg_gallons']:,.0f} gal")

        # Water source breakdown
        if stats["water_sources"]:
            sources_str = ", ".join(f"{src}: {cnt}" for src, cnt in stats["water_sources"].most_common())
            pdf.key_value("Water Sources", sources_str)
        pdf.spacer(4)

        # Per-property water table
        pdf.sub_header("Water Usage by Property")
        cols = _scale_cols([
            ("Property", 45), ("Est. Gallons", 30), ("Water Source", 30),
            ("Zones", 18), ("Total GPM", 25),
        ])
        pdf.table_header(cols)
        widths = [c[1] for c in cols]

        sorted_data = sorted(customer_data, key=lambda c: _estimate_prop_gallons(c), reverse=True)
        for i, c in enumerate(sorted_data):
            gal = _estimate_prop_gallons(c)
            pdf.table_row([
                _prop_name(c),
                f"{gal:,.0f}" if gal > 0 else "-",
                _prop_water_source(c),
                str(_count_prop_zones(c)),
                f"{_prop_total_gpm(c):.1f}" if _prop_total_gpm(c) > 0 else "-",
            ], widths, shade=(i % 2 == 0))
        pdf.spacer(4)

    # ── Section: Weather Impact ──────────────────────────────────
    if "weather_impact" not in hidden_sections:
        pdf.add_page()
        pdf.section_header("Weather Impact Analysis")

        pdf.key_value("Weather Control Enabled", f"{stats['weather_enabled_count']} of {stats['total_properties']} properties")
        pdf.key_value("Avg Weather Factor", f"{stats['avg_weather_factor']:.2f}x")
        pdf.key_value("Properties with Rain Skip", str(stats["rain_skip_count"]))
        pdf.key_value("Properties with Freeze Protection", str(stats["freeze_count"]))
        pdf.spacer(4)

        # Per-property weather table
        pdf.sub_header("Weather Settings by Property")
        cols = _scale_cols([
            ("Property", 50), ("Weather Enabled", 30), ("Current Factor", 30),
            ("Status", 40),
        ])
        pdf.table_header(cols)
        widths = [c[1] for c in cols]

        for i, c in enumerate(customer_data):
            w = c.get("weather", {})
            enabled = _prop_weather_enabled(c)
            factor = _prop_weather_factor(c)
            # Check for active adjustments
            adj_list = w.get("active_adjustments", []) if isinstance(w, dict) else []
            status_parts = []
            if isinstance(adj_list, list):
                for a in adj_list:
                    if isinstance(a, dict):
                        reason = a.get("reason", "")
                        if reason:
                            status_parts.append(reason)
            status = ", ".join(status_parts[:2]) if status_parts else ("Active" if enabled else "Disabled")

            pdf.table_row([
                _prop_name(c),
                "Yes" if enabled else "No",
                f"{factor:.2f}x" if enabled else "-",
                status,
            ], widths, shade=(i % 2 == 0))
        pdf.spacer(4)

    # ── Section: Moisture Analytics ──────────────────────────────
    if "moisture_analytics" not in hidden_sections:
        pdf.add_page()

        # Section header with Gophr logo
        pdf._ensure_space(20)
        pdf.ln(2)
        y = pdf.get_y()
        pdf.set_fill_color(*accent_rgb)
        pdf.rect(_MARGIN, y, _CW, 8, "F")
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_xy(_MARGIN + 3, y + 1)
        pdf.cell(_CW - 30, 6, "Moisture Probe Analytics")
        # Gophr logo in header
        if os.path.exists(_GOPHR_LOGO):
            try:
                pdf.image(_GOPHR_LOGO, x=_PAGE_W - _MARGIN - 24, y=y + 0.5, h=7)
            except Exception:
                pass
        pdf.set_xy(_MARGIN, y + 8)
        pdf.ln(3)
        pdf.set_text_color(*TEXT_DARK)

        pdf.key_value("Total Probes (portfolio)", str(stats["total_probes"]))
        pdf.key_value("Properties with Probes", f"{stats['properties_with_probes']} of {stats['total_properties']}")
        if stats["properties_with_probes"] > 0:
            avg_probes = round(stats["total_probes"] / stats["properties_with_probes"], 1)
            pdf.key_value("Avg Probes / Property", str(avg_probes))
        if stats["total_zones_for_probe_props"] > 0:
            coverage = round(stats["total_mapped_zones"] / stats["total_zones_for_probe_props"] * 100, 1)
            pdf.key_value("Zone Coverage (probe props)", f"{coverage}%")
        pdf.spacer(4)

        # Per-property moisture table
        pdf.sub_header("Probes by Property")
        cols = _scale_cols([
            ("Property", 50), ("Probes", 22), ("Mapped Zones", 28),
            ("Zones", 22), ("Coverage", 28),
        ])
        pdf.table_header(cols)
        widths = [c[1] for c in cols]

        # Only show properties with probes, plus a few without
        props_with = [c for c in customer_data if _count_prop_probes(c) > 0]
        props_without = [c for c in customer_data if _count_prop_probes(c) == 0]

        for i, c in enumerate(props_with):
            probes = _count_prop_probes(c)
            zones = _count_prop_zones(c)
            moisture = c.get("moisture", {})
            mapped = 0
            if isinstance(moisture, dict):
                for p in moisture.get("probes", {}).values():
                    if isinstance(p, dict):
                        mz = p.get("mapped_zones", [])
                        if isinstance(mz, list):
                            mapped += len(mz)
            coverage = f"{round(mapped / zones * 100)}%" if zones > 0 else "-"
            pdf.table_row([
                _prop_name(c),
                str(probes),
                str(mapped),
                str(zones),
                coverage,
            ], widths, shade=(i % 2 == 0))

        if props_without:
            pdf.spacer(2)
            pdf.set_font("Helvetica", "I", 7.5)
            pdf.set_text_color(*TEXT_MUTED)
            no_probe_names = ", ".join(_prop_name(c) for c in props_without[:5])
            extra = f" (+{len(props_without) - 5} more)" if len(props_without) > 5 else ""
            pdf.set_x(_MARGIN)
            pdf.cell(_CW, 4, f"No probes: {no_probe_names}{extra}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*TEXT_DARK)
        pdf.spacer(4)

    # ── Section: System Health ───────────────────────────────────
    if "system_health" not in hidden_sections:
        pdf.add_page()
        pdf.section_header("System Health & Issues")

        pdf.key_value("Total Open Issues", str(stats["total_issues"]))
        pdf.key_value("Severe", str(stats["severe_count"]))
        pdf.key_value("Annoyance", str(stats["annoyance_count"]))
        pdf.key_value("Clarification", str(stats["clarification_count"]))
        pdf.key_value("Healthy Properties (0 issues)", f"{stats['healthy_count']} of {stats['total_properties']}")
        pdf.key_value("Offline Properties", str(stats["offline"]))
        pdf.spacer(2)

        # Most common issue types
        if stats["issue_type_counter"]:
            pdf.sub_header("Most Common Issue Types")
            for itype, cnt in stats["issue_type_counter"].most_common(8):
                pdf.info_line(f"{itype}: {cnt}", indent=6)
            pdf.spacer(3)

        # Per-property issues table
        pdf.sub_header("Issues by Property")
        cols = _scale_cols([
            ("Property", 50), ("Severe", 22), ("Annoyance", 25),
            ("Clarification", 28), ("Total", 20), ("Status", 20),
        ])
        pdf.table_header(cols)
        widths = [c[1] for c in cols]

        sorted_data = sorted(customer_data, key=lambda c: _count_prop_issues(c)[3], reverse=True)
        for i, c in enumerate(sorted_data):
            sev, ann, clar, total = _count_prop_issues(c)
            status = "Online" if c.get("online") else "Offline"
            pdf.table_row([
                _prop_name(c),
                str(sev) if sev else "-",
                str(ann) if ann else "-",
                str(clar) if clar else "-",
                str(total),
                status,
            ], widths, shade=(i % 2 == 0))
        pdf.spacer(4)

    # ── Section: Property Comparison ─────────────────────────────
    if "property_comparison" not in hidden_sections:
        pdf.add_page()
        pdf.section_header("Property Comparison")

        cols = _scale_cols([
            ("Property", 38), ("Zones", 16), ("Probes", 16), ("Runs", 16),
            ("Est. Gal", 22), ("Issues", 16), ("Weather", 16), ("Status", 20),
        ])
        pdf.table_header(cols)
        widths = [c[1] for c in cols]

        for i, c in enumerate(customer_data):
            gal = _estimate_prop_gallons(c)
            issues_total = _count_prop_issues(c)[3]
            w_factor = _prop_weather_factor(c) if _prop_weather_enabled(c) else None
            pdf.table_row([
                _prop_name(c),
                str(_count_prop_zones(c)),
                str(_count_prop_probes(c)) if _count_prop_probes(c) > 0 else "-",
                str(_count_prop_runs(c)),
                f"{gal:,.0f}" if gal > 0 else "-",
                str(issues_total) if issues_total > 0 else "0",
                f"{w_factor:.2f}x" if w_factor is not None else "-",
                "Online" if c.get("online") else "Offline",
            ], widths, shade=(i % 2 == 0))
        pdf.spacer(4)

    # ── Section: Recommendations ─────────────────────────────────
    if "recommendations" not in hidden_sections:
        pdf.add_page()
        pdf.section_header("Recommendations")

        recommendations = []

        # Offline properties
        for c in customer_data:
            if not c.get("online"):
                recommendations.append(("offline", _prop_name(c), f"{_prop_name(c)} is currently offline and cannot be monitored."))

        # No probes
        for c in customer_data:
            if c.get("online") and _count_prop_probes(c) == 0:
                recommendations.append(("probe", _prop_name(c), f"Consider adding Gophr moisture probes to {_prop_name(c)} for smarter water management."))

        # Weather disabled
        for c in customer_data:
            if c.get("online") and not _prop_weather_enabled(c):
                recommendations.append(("weather", _prop_name(c), f"Enable weather-based control for {_prop_name(c)} to automatically adjust irrigation."))

        # High issues
        for c in customer_data:
            issues_total = _count_prop_issues(c)[3]
            if issues_total >= 3:
                recommendations.append(("issues", _prop_name(c), f"{_prop_name(c)} has {issues_total} open issues requiring attention."))

        # Above-average water usage
        if stats["avg_gallons"] > 0:
            for c in customer_data:
                gal = _estimate_prop_gallons(c)
                if gal > stats["avg_gallons"] * 1.5 and gal > 100:
                    pct = round((gal / stats["avg_gallons"] - 1) * 100)
                    recommendations.append(("water", _prop_name(c), f"{_prop_name(c)} uses {pct}% more water than the portfolio average."))

        # No recent runs
        for c in customer_data:
            if c.get("online") and _count_prop_runs(c) == 0:
                recommendations.append(("inactive", _prop_name(c), f"{_prop_name(c)} has not run irrigation in the reporting period."))

        if recommendations:
            # Render each recommendation as a mini card
            icons = {
                "offline": "!",
                "probe": "+",
                "weather": "~",
                "issues": "!",
                "water": "#",
                "inactive": "?",
            }
            colors = {
                "offline": SEVERITY_COLORS.get("severe", (231, 76, 60)),
                "probe": (52, 152, 219),
                "weather": (243, 156, 18),
                "issues": SEVERITY_COLORS.get("annoyance", (243, 156, 18)),
                "water": (52, 152, 219),
                "inactive": TEXT_MUTED,
            }

            for rtype, prop, text in recommendations:
                pdf._ensure_space(12)
                y = pdf.get_y()
                color = colors.get(rtype, accent_rgb)
                # Left accent bar
                pdf.set_fill_color(*color)
                pdf.rect(_MARGIN, y, 2, 8, "F")
                # Light background
                light_bg = _lighten(color, 0.9)
                pdf.set_fill_color(*light_bg)
                pdf.rect(_MARGIN + 2, y, _CW - 2, 8, "F")
                # Text
                pdf.set_font("Helvetica", "", 7.5)
                pdf.set_text_color(*TEXT_DARK)
                pdf.set_xy(_MARGIN + 5, y + 1.5)
                pdf.cell(_CW - 10, 5, text)
                pdf.set_xy(_MARGIN, y + 9)
        else:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*TEXT_MUTED)
            pdf.set_x(_MARGIN)
            pdf.cell(_CW, 6, "No recommendations at this time. All properties are well-configured.", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*TEXT_DARK)

        pdf.spacer(4)

    # ── End Page ──────────────────────────────────────────────────
    pdf._ensure_space(40)
    pdf.divider()
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*accent_rgb)
    end_title = f"{company_name}  |  Portfolio Statistics Report" if company_name else "Flux Open Home  |  Portfolio Statistics Report"
    pdf.cell(_CW, 5, end_title, new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.cell(_CW, 4, f"{_hours_label(hours)}  |  Generated {datetime.now().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(_CW, 4, f"{stats['total_properties']} Properties  |  {stats['total_zones']} Zones  |  {stats['total_runs']} Runs", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    # "Powered by" Flux logo at bottom if custom logo used
    if custom_logo_path and os.path.exists(_FLUX_LOGO):
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(_CW, 4, "Powered by", new_x="LMARGIN", new_y="NEXT", align="C")
        try:
            small_w = 40
            small_x = (_PAGE_W - small_w) / 2
            pdf.image(_FLUX_LOGO, x=small_x, y=pdf.get_y(), w=small_w)
        except Exception:
            pass

    # Cleanup temp logo file
    if custom_logo_path:
        try:
            os.unlink(custom_logo_path)
        except Exception:
            pass

    return pdf
