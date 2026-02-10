"""
Flux Open Home - Portfolio Report Settings
===========================================
Persists configuration for the cross-customer portfolio statistics report:
company logo, company name, accent color, section visibility, and custom
footer text.

Settings are stored on the management instance at
/data/portfolio_report_settings.json.  The custom logo is stored as
/data/portfolio_report_logo.png.
"""

import json
import os
import re

SETTINGS_FILE = "/data/portfolio_report_settings.json"
CUSTOM_LOGO_FILE = "/data/portfolio_report_logo.png"

DEFAULT_SETTINGS = {
    "company_name": "",              # Shown on cover page + page headers
    "custom_footer": "",             # Replaces default footer
    "accent_color": "#1a7a4c",       # Cover page accent (hex, default = GREEN_PRIMARY)
    "has_custom_logo": False,        # Whether a custom logo has been uploaded
    "hidden_sections": [],           # List of section keys to hide
}

# Valid section keys that can be toggled on/off
PORTFOLIO_SECTIONS = [
    "portfolio_overview",
    "irrigation_activity",
    "water_usage",
    "weather_impact",
    "moisture_analytics",
    "system_health",
    "property_comparison",
    "recommendations",
]

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _load_settings() -> dict:
    """Load portfolio report settings from persistent storage."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                # Merge with defaults for forward-compat
                merged = dict(DEFAULT_SETTINGS)
                merged.update(data)
                # Sync has_custom_logo with actual file
                merged["has_custom_logo"] = os.path.exists(CUSTOM_LOGO_FILE)
                return merged
        except (json.JSONDecodeError, IOError):
            pass
    settings = dict(DEFAULT_SETTINGS)
    settings["has_custom_logo"] = os.path.exists(CUSTOM_LOGO_FILE)
    return settings


def _save_settings(data: dict):
    """Save portfolio report settings to persistent storage."""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_settings() -> dict:
    """Get the current portfolio report settings."""
    return _load_settings()


def save_settings(settings: dict) -> dict:
    """Save portfolio report settings with validation.

    - accent_color must be a valid 6-digit hex color (#RRGGBB)
    - hidden_sections must only contain valid section keys
    - company_name and custom_footer are trimmed strings
    """
    current = _load_settings()

    # Company name -- trim
    if "company_name" in settings:
        current["company_name"] = str(settings.get("company_name", "") or "").strip()[:200]

    # Custom footer -- trim
    if "custom_footer" in settings:
        current["custom_footer"] = str(settings.get("custom_footer", "") or "").strip()[:500]

    # Accent color -- validate hex
    if "accent_color" in settings:
        color = str(settings.get("accent_color", "#1a7a4c") or "#1a7a4c").strip()
        if _HEX_RE.match(color):
            current["accent_color"] = color
        # else: keep current value

    # Hidden sections -- validate keys
    if "hidden_sections" in settings:
        raw = settings.get("hidden_sections", [])
        if isinstance(raw, list):
            current["hidden_sections"] = [s for s in raw if s in PORTFOLIO_SECTIONS]
        # else: keep current value

    # Sync logo flag with actual file
    current["has_custom_logo"] = os.path.exists(CUSTOM_LOGO_FILE)

    _save_settings(current)
    return current


def save_logo(image_bytes: bytes) -> bool:
    """Save a custom logo image as PNG.

    Attempts to convert the image to PNG using Pillow. If Pillow is not
    available, saves the raw bytes (assumes the upload is already PNG/JPEG).
    Returns True on success.
    """
    os.makedirs(os.path.dirname(CUSTOM_LOGO_FILE), exist_ok=True)
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_bytes))
        # Convert to RGBA (handles palette, grayscale, etc.)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        img.save(CUSTOM_LOGO_FILE, format="PNG")
    except Exception:
        # Fallback: save raw bytes
        with open(CUSTOM_LOGO_FILE, "wb") as f:
            f.write(image_bytes)

    # Update settings flag
    settings = _load_settings()
    settings["has_custom_logo"] = True
    _save_settings(settings)
    return True


def delete_logo() -> bool:
    """Remove the custom logo file."""
    if os.path.exists(CUSTOM_LOGO_FILE):
        try:
            os.remove(CUSTOM_LOGO_FILE)
        except OSError:
            pass
    # Update settings flag
    settings = _load_settings()
    settings["has_custom_logo"] = False
    _save_settings(settings)
    return True


def get_logo_path() -> str | None:
    """Return the custom logo file path if it exists, else None."""
    if os.path.exists(CUSTOM_LOGO_FILE):
        return CUSTOM_LOGO_FILE
    return None
