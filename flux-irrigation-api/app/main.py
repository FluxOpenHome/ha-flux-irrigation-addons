"""
Flux Open Home Irrigation Control
====================================
A Home Assistant add-on for homeowner irrigation management.
Exposes a secure, scoped API and dashboard for controlling zones,
sensors, schedules, weather rules, and moisture probes.

Management features have been moved to the Flux Management Server (cloud).

Author: Brandon / Flux Open Home
"""

import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import os

from config import get_config, async_initialize
from audit_log import cleanup_old_logs
from routes import zones, sensors, entities, history, system, admin, homeowner, weather, moisture, issues, dashboard_clone, report_pdf


PROXY_SERVICE_NAMES = [
    "irrigation_proxy_get",
    "irrigation_proxy_post",
    "irrigation_proxy_put",
    "irrigation_proxy_delete",
]


async def _check_rest_command_service(config):
    """Check if rest_command.irrigation_proxy_* services are registered in HA."""
    import httpx
    try:
        token = config.supervisor_token
        if not token:
            print("[MAIN] Cannot check rest_command service — no supervisor token")
            return
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "http://supervisor/core/api/services",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                services = resp.json()
                rest_cmd = None
                for svc in services:
                    if svc.get("domain") == "rest_command":
                        rest_cmd = svc
                        break
                if rest_cmd:
                    svc_names = list(rest_cmd.get("services", {}).keys())
                    found = [s for s in PROXY_SERVICE_NAMES if s in svc_names]
                    missing = [s for s in PROXY_SERVICE_NAMES if s not in svc_names]
                    if not missing:
                        print(f"[MAIN] ✓ All irrigation_proxy rest_commands registered: {found}")
                    else:
                        print(f"[MAIN] ✗ Missing rest_commands: {missing}")
                        print(f"[MAIN]   Found: {found}")
                        print(f"[MAIN]   Available: {svc_names}")
                        # Check for old single-service name
                        if "irrigation_proxy" in svc_names:
                            print(f"[MAIN]   ⚠ Old 'irrigation_proxy' (single) found — needs HA restart with updated packages file")
                        print(f"[MAIN]   → Restart Home Assistant to pick up the updated packages file")
                else:
                    print(f"[MAIN] ✗ rest_command domain is NOT registered in HA!")
                    print(f"[MAIN]   → The add-on auto-configures configuration.yaml on startup")
                    print(f"[MAIN]   → Fully restart Home Assistant (Settings → System → Restart)")
                    print(f"[MAIN]   → The proxy services will register after the restart")
            else:
                print(f"[MAIN] Could not check services: HTTP {resp.status_code}")
    except Exception as e:
        print(f"[MAIN] Could not check rest_command service: {e}")


def _ensure_packages_include():
    """Ensure configuration.yaml includes the packages directory.

    Checks for 'homeassistant:' with 'packages: !include_dir_named packages'
    and adds it if missing. This eliminates the manual setup step for users.
    """
    config_file = "/config/configuration.yaml"
    if not os.path.exists(config_file):
        print("[MAIN] WARNING: /config/configuration.yaml not found — cannot auto-configure packages include")
        return

    try:
        with open(config_file, "r") as f:
            content = f.read()
        lines = content.split("\n")

        # Check if packages include already exists correctly (indented under homeassistant:)
        has_correct_include = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "packages: !include_dir_named packages":
                # Check if it's indented (i.e. under homeassistant:)
                if line.startswith(" ") or line.startswith("\t"):
                    has_correct_include = True
                    break

        if has_correct_include:
            print("[MAIN] ✓ configuration.yaml already has packages include")
            return

        # Check if 'packages:' exists at the wrong indentation (top-level)
        has_toplevel_packages = False
        toplevel_packages_idx = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "packages: !include_dir_named packages" and not line.startswith(" ") and not line.startswith("\t"):
                has_toplevel_packages = True
                toplevel_packages_idx = i
                break

        # Find homeassistant: line
        ha_line_idx = -1
        for i, line in enumerate(lines):
            if line.rstrip() == "homeassistant:" or line.strip() == "homeassistant:":
                if not line.startswith(" ") and not line.startswith("\t"):
                    ha_line_idx = i
                    break

        modified = False

        if has_toplevel_packages and ha_line_idx >= 0:
            # Fix: packages is at the top level but homeassistant: exists
            # Remove the top-level packages line and add it indented under homeassistant:
            lines.pop(toplevel_packages_idx)
            # Recalculate ha_line_idx if it was after the removed line
            if ha_line_idx > toplevel_packages_idx:
                ha_line_idx -= 1
            lines.insert(ha_line_idx + 1, "  packages: !include_dir_named packages")
            modified = True
            print("[MAIN] ✓ Fixed packages include — moved under homeassistant: with proper indentation")

        elif has_toplevel_packages and ha_line_idx < 0:
            # Fix: packages exists at top level but no homeassistant: section
            # Replace the top-level packages line with both lines
            lines[toplevel_packages_idx] = "homeassistant:\n  packages: !include_dir_named packages"
            modified = True
            print("[MAIN] ✓ Added homeassistant: section and indented packages include")

        elif ha_line_idx >= 0:
            # homeassistant: exists but no packages line at all — add it
            lines.insert(ha_line_idx + 1, "  packages: !include_dir_named packages")
            modified = True
            print("[MAIN] ✓ Added packages include under existing homeassistant: section")

        else:
            # Neither exists — add both at the top of the file
            lines.insert(0, "homeassistant:")
            lines.insert(1, "  packages: !include_dir_named packages")
            lines.insert(2, "")
            modified = True
            print("[MAIN] ✓ Added homeassistant: section with packages include to configuration.yaml")

        if modified:
            new_content = "\n".join(lines)
            with open(config_file, "w") as f:
                f.write(new_content)
            print("[MAIN] IMPORTANT: Home Assistant must be restarted for packages to take effect")

    except PermissionError as e:
        print(f"[MAIN] ✗ PERMISSION ERROR reading/writing {config_file}: {e}")
    except Exception as e:
        print(f"[MAIN] ✗ Failed to update configuration.yaml: {type(e).__name__}: {e}")


def _setup_rest_command_proxy():
    """
    Write a HA packages file that creates the rest_command.irrigation_proxy
    service. This allows management companies to reach this add-on through
    Nabu Casa via HA's REST API → rest_command → localhost:8099.
    """
    packages_dir = "/config/packages"
    package_file = os.path.join(packages_dir, "flux_irrigation_proxy.yaml")

    PACKAGE_CONTENT = """# Auto-generated by Flux Open Home Irrigation Control add-on
# This enables Nabu Casa connectivity for management companies
# DO NOT EDIT — this file is regenerated on add-on startup
#
# NOTE: rest_command does NOT support Jinja templates in the 'method' field,
# so we create one entry per HTTP method. The management client calls the
# appropriate service (e.g. rest_command.irrigation_proxy_get).

rest_command:
  irrigation_proxy_get:
    url: "http://localhost:8099/{{ path }}"
    method: get
    headers:
      Content-Type: "application/json"
      X-API-Key: "{{ api_key }}"
    content_type: "application/json"

  irrigation_proxy_post:
    url: "http://localhost:8099/{{ path }}"
    method: post
    headers:
      Content-Type: "application/json"
      X-API-Key: "{{ api_key }}"
    payload: '{{ payload | default("{}") }}'
    content_type: "application/json"

  irrigation_proxy_put:
    url: "http://localhost:8099/{{ path }}"
    method: put
    headers:
      Content-Type: "application/json"
      X-API-Key: "{{ api_key }}"
    payload: '{{ payload | default("{}") }}'
    content_type: "application/json"

  irrigation_proxy_delete:
    url: "http://localhost:8099/{{ path }}"
    method: delete
    headers:
      Content-Type: "application/json"
      X-API-Key: "{{ api_key }}"
    content_type: "application/json"
"""

    try:
        # Log filesystem state for debugging
        print(f"[MAIN] Checking /config directory...")
        if os.path.exists("/config"):
            print(f"[MAIN]   /config exists (is_dir={os.path.isdir('/config')})")
            try:
                config_contents = os.listdir("/config")
                print(f"[MAIN]   /config contains {len(config_contents)} items")
                if "packages" in config_contents:
                    print(f"[MAIN]   /config/packages already exists")
                else:
                    print(f"[MAIN]   /config/packages does NOT exist — will create it")
            except Exception as e:
                print(f"[MAIN]   Cannot list /config: {e}")
        else:
            print(f"[MAIN]   WARNING: /config does NOT exist!")

        os.makedirs(packages_dir, exist_ok=True)
        print(f"[MAIN]   Created/verified {packages_dir}")

        # Check if file already exists with same content
        if os.path.exists(package_file):
            try:
                with open(package_file, "r") as f:
                    existing = f.read()
                if existing.strip() == PACKAGE_CONTENT.strip():
                    print("[MAIN] rest_command.irrigation_proxy package already configured")
                    return
            except Exception:
                pass  # Re-write the file

        with open(package_file, "w") as f:
            f.write(PACKAGE_CONTENT)

        # Verify it was written
        if os.path.exists(package_file):
            size = os.path.getsize(package_file)
            print(f"[MAIN] ✓ Created rest_command package at {package_file} ({size} bytes)")
        else:
            print(f"[MAIN] ✗ File write appeared to succeed but file not found!")

        print("[MAIN] IMPORTANT: Restart Home Assistant for the rest_command to take effect.")
    except PermissionError as e:
        print(f"[MAIN] ✗ PERMISSION ERROR writing to {packages_dir}: {e}")
        print("[MAIN]   The add-on needs 'config:rw' in config.yaml map section.")
        print("[MAIN]   Nabu Casa mode will not work until this is resolved.")
    except Exception as e:
        print(f"[MAIN] ✗ FAILED to write rest_command package: {type(e).__name__}: {e}")


# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address)


# --- Periodic Tasks ---
async def _periodic_log_cleanup():
    """Run audit log and weather log cleanup once per day."""
    while True:
        try:
            cleanup_old_logs()
        except Exception as e:
            print(f"[MAIN] Log cleanup error: {e}")
        try:
            from routes.weather import cleanup_weather_log
            config = get_config()
            cleanup_weather_log(retention_days=config.log_retention_days)
        except Exception as e:
            print(f"[MAIN] Weather log cleanup error: {e}")
        try:
            from run_log import cleanup_run_history
            config = get_config()
            cleanup_run_history(retention_days=config.log_retention_days)
        except Exception as e:
            print(f"[MAIN] Run history cleanup error: {e}")
        await asyncio.sleep(86400)  # 24 hours


async def _periodic_weather_check():
    """Periodically evaluate weather rules for irrigation adjustments."""
    while True:
        try:
            config = get_config()
            weather_ready = config.weather_enabled and (
                config.weather_entity_id or config.weather_source == "nws"
            )
            if weather_ready:
                from routes.weather import run_weather_evaluation
                result = await run_weather_evaluation()
                if result.get("triggered_rules"):
                    print(f"[MAIN] Weather evaluation: {len(result['triggered_rules'])} rule(s) triggered, "
                          f"multiplier={result.get('watering_multiplier', 1.0)}")
        except Exception as e:
            print(f"[MAIN] Weather check error: {e}")

        config = get_config()
        min_interval = 60 if config.weather_source == "nws" else 5
        interval = max(config.weather_check_interval_minutes, min_interval) * 60
        await asyncio.sleep(interval)


async def _periodic_moisture_evaluation():
    """Periodically evaluate moisture probes, adjust run durations, and recalculate schedule timeline."""
    while True:
        try:
            config = get_config()
            from routes.moisture import run_moisture_evaluation, calculate_irrigation_timeline
            result = await run_moisture_evaluation()
            if not result.get("skipped"):
                print(f"[MAIN] Moisture evaluation: {result.get('applied', 0)} zone(s) adjusted")

            # Recalculate schedule timeline (replaces old sync_schedule_times_to_probes)
            try:
                timeline = await calculate_irrigation_timeline()
                sched_count = len(timeline.get("schedules", []))
                prep_count = len(timeline.get("probe_prep", {}))
                if prep_count > 0:
                    print(f"[MAIN] Schedule timeline: {sched_count} schedule(s), "
                          f"{prep_count} probe(s) with prep timing")
            except Exception as tl_err:
                print(f"[MAIN] Schedule timeline error: {tl_err}")
        except Exception as e:
            print(f"[MAIN] Moisture evaluation error: {e}")

        config = get_config()
        interval = max(config.weather_check_interval_minutes, 5) * 60
        await asyncio.sleep(interval)


async def _periodic_entity_refresh():
    """Periodically re-resolve device entities to pick up newly enabled/disabled entities.

    This handles the case where a user enables/disables an entity in HA
    (e.g., enabling a previously disabled Zone 5) without needing to restart
    the add-on or re-select the device on the Configuration page.
    """
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        try:
            config = get_config()
            if not config.irrigation_device_id:
                continue

            old_zones = set(config.allowed_zone_entities)
            old_sensors = set(config.allowed_sensor_entities)
            old_controls = set(config.allowed_control_entities)

            print(f"[MAIN] Entity refresh running (current: {len(old_zones)} zones, "
                  f"{len(old_sensors)} sensors, {len(old_controls)} controls)")

            await config.resolve_device_entities()

            new_zones = set(config.allowed_zone_entities)
            new_sensors = set(config.allowed_sensor_entities)
            new_controls = set(config.allowed_control_entities)

            added_zones = new_zones - old_zones
            removed_zones = old_zones - new_zones
            added_sensors = new_sensors - old_sensors
            removed_sensors = old_sensors - new_sensors
            added_controls = new_controls - old_controls
            removed_controls = old_controls - new_controls

            if added_zones or removed_zones or added_sensors or removed_sensors or added_controls or removed_controls:
                print(f"[MAIN] Entity refresh detected changes:")
                if added_zones:
                    print(f"[MAIN]   + Zones added: {added_zones}")
                if removed_zones:
                    print(f"[MAIN]   - Zones removed: {removed_zones}")
                if added_sensors:
                    print(f"[MAIN]   + Sensors added: {added_sensors}")
                if removed_sensors:
                    print(f"[MAIN]   - Sensors removed: {removed_sensors}")
                if added_controls:
                    print(f"[MAIN]   + Controls added: {added_controls}")
                if removed_controls:
                    print(f"[MAIN]   - Controls removed: {removed_controls}")
                print(f"[MAIN] Entity refresh complete: {len(new_zones)} zones, "
                      f"{len(new_sensors)} sensors, {len(new_controls)} controls")
            else:
                print(f"[MAIN] Entity refresh complete: no changes detected")
        except Exception as e:
            print(f"[MAIN] Entity refresh error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    config = await async_initialize()
    print("[MAIN] Flux Open Home Irrigation Control starting...")

    # Ensure configuration.yaml has the packages include — eliminates manual setup step
    _ensure_packages_include()

    # Always set up the rest_command proxy file — needed for Nabu Casa
    # connectivity regardless of current mode (user may switch modes later)
    _setup_rest_command_proxy()
    await _check_rest_command_service(config)

    # Always log entity counts (device entities are resolved regardless of mode)
    print(f"[MAIN] Configured API keys: {len(config.api_keys)}")
    print(f"[MAIN] Irrigation device: {config.irrigation_device_id or '(not configured)'}")
    print(f"[MAIN] Resolved zones: {len(config.allowed_zone_entities)}")
    print(f"[MAIN] Resolved sensors: {len(config.allowed_sensor_entities)}")
    print(f"[MAIN] Resolved controls: {len(config.allowed_control_entities)}")

    print(f"[MAIN] Rate limit: {config.rate_limit_per_minute}/min")
    print(f"[MAIN] Audit logging: {'enabled' if config.enable_audit_log else 'disabled'}")
    if config.homeowner_url:
        print(f"[MAIN] External URL: {config.homeowner_url}")

    # Moisture probe startup recovery: handle adjusted durations from prior session
    try:
        from routes.moisture import (
            _load_data as _load_moisture_data,
            restore_base_durations,
            capture_base_durations,
            apply_adjusted_durations,
        )
        moisture_data = _load_moisture_data()
        if moisture_data.get("apply_factors_to_schedule"):
            # Toggle is ON — re-apply adjusted durations using stored base values
            # Do NOT re-capture: HA entities may have adjusted values from last session
            if moisture_data.get("base_durations"):
                print("[MAIN] Apply factors to schedule is enabled — re-applying adjusted durations from stored base")
                await apply_adjusted_durations()
            else:
                # No stored base — must capture fresh (first run after enabling)
                print("[MAIN] Apply factors enabled but no stored base — capturing fresh base durations")
                await capture_base_durations()
                await apply_adjusted_durations()
        elif moisture_data.get("duration_adjustment_active"):
            # Toggle is OFF but durations were adjusted — restore base values (safety net)
            print("[MAIN] Moisture: adjusted durations were active at shutdown — restoring base values")
            await restore_base_durations()
    except Exception as e:
        print(f"[MAIN] Moisture startup recovery error: {e}")

    # Active schedule run crash recovery: if the add-on was restarted mid-schedule,
    # the active_run state in moisture.json may have moisture-disabled zones that
    # need to be re-enabled.
    try:
        from routes.moisture import (
            _load_data as _load_moisture_data_cr,
            _end_active_run,
            _active_schedule_run,
        )
        import routes.moisture as moisture_mod
        cr_data = _load_moisture_data_cr()
        if cr_data.get("active_run"):
            print("[MAIN] Active schedule run found from prior session — checking zones")
            # Re-hydrate the in-memory state
            moisture_mod._active_schedule_run = cr_data["active_run"]
            # Check if any zones are actually running
            from routes.moisture import get_config as get_moisture_config
            cr_config = get_moisture_config()
            cr_zones = await ha_client.get_entities_by_ids(
                cr_config.allowed_zone_entities
            )
            still_running = [z for z in cr_zones if z.get("state") in ("on", "open")]
            if not still_running:
                print("[MAIN] No zones running — ending active run and restoring zones")
                await _end_active_run()
            else:
                print(f"[MAIN] {len(still_running)} zone(s) still running — "
                      f"keeping active run state")
    except Exception as e:
        print(f"[MAIN] Active run recovery error: {e}")

    # Start background tasks
    cleanup_task = asyncio.create_task(_periodic_log_cleanup())
    weather_task = None
    moisture_task = None
    zone_watcher_task = None
    entity_refresh_task = None
    if config.allowed_zone_entities:
        from run_log import watch_zone_states
        zone_watcher_task = asyncio.create_task(watch_zone_states())
        print(f"[MAIN] Zone state watcher active: monitoring {len(config.allowed_zone_entities)} zone(s)")

    # Full state sync to remote device on startup (ALL entities)
    if config.allowed_remote_entities:
        try:
            from run_log import sync_all_remote_state
            from routes.admin import sync_remote_settings
            import run_log
            # Push zone count + time format first (settings-only entities)
            settings_file = "/data/settings.json"
            use_12h = True
            if os.path.exists(settings_file):
                with open(settings_file) as f:
                    s = json.load(f)
                    use_12h = s.get("time_format", "12h") != "24h"
            await sync_remote_settings(use_12h=use_12h)
            # Then push ALL entity states (zones, schedules, durations, days, status, etc.)
            await sync_all_remote_state()
            # Hold suppression for 15s — don't let remote send anything until settled
            await asyncio.sleep(15)
            run_log._remote_reconnect_pending = False
            run_log._remote_log("Broker: startup sync complete — remote→controller mirroring enabled")
        except Exception as e:
            print(f"[MAIN] Remote device sync failed: {e}")
            # Always clear the flag so mirroring can work even if sync failed
            import run_log
            run_log._remote_reconnect_pending = False
            run_log._remote_log("Broker: startup sync FAILED — remote→controller mirroring enabled (fallback)")
    weather_ready = config.weather_enabled and (
        config.weather_entity_id or config.weather_source == "nws"
    )
    if weather_ready:
        weather_task = asyncio.create_task(_periodic_weather_check())
        source_label = "Built-In NWS (address)" if config.weather_source == "nws" else f"entity={config.weather_entity_id}"
        print(f"[MAIN] Weather control active: source={source_label}, "
              f"interval={config.weather_check_interval_minutes}min")
    from routes.moisture import _load_data as _load_moisture_data
    moisture_data = _load_moisture_data()
    if moisture_data.get("enabled"):
        moisture_task = asyncio.create_task(_periodic_moisture_evaluation())
        probe_count = len(moisture_data.get("probes", {}))
        print(f"[MAIN] Moisture probe evaluation active: {probe_count} probe(s), "
              f"interval={config.weather_check_interval_minutes}min")
        # Start awake status poller for Gophr probes
        if probe_count > 0:
            from routes.moisture import start_awake_poller, calculate_irrigation_timeline
            start_awake_poller()
            # Calculate initial schedule timeline for probe-aware irrigation
            try:
                timeline = await calculate_irrigation_timeline()
                prep_count = len(timeline.get("probe_prep", {}))
                if prep_count > 0:
                    print(f"[MAIN] Initial schedule timeline: {prep_count} probe(s) with prep timing")
            except Exception as tl_err:
                print(f"[MAIN] Initial timeline calculation error: {tl_err}")
    if config.irrigation_device_id:
        entity_refresh_task = asyncio.create_task(_periodic_entity_refresh())
        print(f"[MAIN] Entity auto-refresh active: checking every 5 minutes for newly enabled/disabled entities")

    yield

    # Shutdown
    cleanup_task.cancel()
    if weather_task:
        weather_task.cancel()
    if moisture_task:
        moisture_task.cancel()
    try:
        from routes.moisture import stop_awake_poller
        stop_awake_poller()
    except Exception:
        pass
    if zone_watcher_task:
        zone_watcher_task.cancel()
    if entity_refresh_task:
        entity_refresh_task.cancel()
    print("[MAIN] Flux Open Home Irrigation Control shutting down.")


# --- FastAPI App ---
app = FastAPI(
    title="Flux Open Home Irrigation Control",
    description=(
        "Homeowner irrigation management for Flux Open Home. "
        "Exposes a secure API for controlling zones, sensors, schedules, "
        "weather rules, and moisture probes."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# --- Middleware ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def ingress_root_path_middleware(request: Request, call_next):
    """Set root_path from HA ingress header so Swagger UI can find openapi.json."""
    ingress_path = request.headers.get("X-Ingress-Path", "")
    if ingress_path:
        request.scope["root_path"] = ingress_path.rstrip("/")
    response = await call_next(request)
    # Prevent caching of API responses so UI always gets fresh data
    if "/api/" in request.url.path:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response


# --- Routes ---
app.include_router(zones.router, prefix="/api")
app.include_router(sensors.router, prefix="/api")
app.include_router(entities.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(admin.router)
app.include_router(homeowner.router)
app.include_router(weather.router)
app.include_router(moisture.router)
app.include_router(issues.router)
app.include_router(dashboard_clone.router)
app.include_router(report_pdf.router)


@app.get("/cal/{token}", include_in_schema=False)
async def public_calendar_download(token: str):
    """Serve an .ics calendar file using a temporary token.

    This endpoint is accessible on port 8099 without HA ingress auth,
    allowing Safari on iOS to download the .ics file and hand it to
    Apple Calendar natively — the same way maps.apple.com links work.
    Tokens are single-use and expire after 5 minutes.
    """
    from routes.issues import get_cal_token_issue_id, issue_calendar_ics

    issue_id = get_cal_token_issue_id(token)
    if issue_id is None:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            "<html><body style='font-family:system-ui;padding:40px;text-align:center;'>"
            "<h2>Link Expired</h2>"
            "<p>This calendar link has expired or was already used.</p>"
            "<p>Go back to your irrigation dashboard and tap the service banner again.</p>"
            "</body></html>",
            status_code=410,
        )
    return await issue_calendar_ics(issue_id)


@app.get("/", include_in_schema=False)
async def root(request: Request):
    """Redirect root to admin UI, preserving ingress path prefix."""
    # Use a relative redirect so HA ingress path is preserved
    return RedirectResponse(url="admin", status_code=302)


@app.get("/api", include_in_schema=False)
async def api_root():
    return {
        "endpoints": {
            "zones": "/api/zones",
            "sensors": "/api/sensors",
            "entities": "/api/entities",
            "history": "/api/history/runs",
            "audit_log": "/api/history/audit",
            "system_status": "/api/system/status",
            "health": "/api/system/health",
            "docs": "/api/docs",
        }
    }
