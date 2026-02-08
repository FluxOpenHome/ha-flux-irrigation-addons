# Changelog

All notable changes to the Flux Open Home Irrigation Control add-on are documented here.

---

## [1.1.8] — 2026-02-07

### Added

- **Gophr Moisture Probe Integration** — Auto-detect Gophr moisture probes from HA sensors and integrate soil moisture data into irrigation decisions
  - Gradient-based moisture algorithm: mid sensor (root zone) is the primary decision driver, shallow sensor detects rain via wetting front analysis, deep sensor guards against over-irrigation
  - Many-to-many probe-to-zone mapping (a probe can serve multiple zones; a zone can use multiple probes)
  - Combined weather × moisture multiplier adjusts both API/dashboard timed runs and ESPHome scheduled run durations
  - Configurable root zone thresholds: skip (saturated), wet, optimal, dry — with max increase/decrease percentages and rain detection sensitivity
  - Duration adjustment mechanism: capture base durations → apply adjusted values → restore originals
  - Stale data handling: readings older than the configurable threshold are excluded (defaults to 120 minutes)
  - Background periodic evaluation runs on the weather check interval
  - Crash recovery: restores base durations on add-on restart if adjustments were active at shutdown
  - Moisture context captured in run history events
  - Moisture card on both homeowner and management dashboards with probe tiles, depth bars, zone multiplier badges, and duration status
  - Homeowner dashboard: full probe management (discover, add, remove, map to zones, configure thresholds, duration capture/apply/restore)
  - Management dashboard: full moisture settings control (enable/disable, thresholds, weights) and duration controls via proxy
  - 12 homeowner API endpoints + corresponding management proxy endpoints
- **Weather-Based Irrigation Control** — 9 configurable weather rules that automatically pause, reduce, or increase irrigation based on real-time conditions and forecasts from any Home Assistant weather entity (NWS, OpenWeatherMap, Met.no, Weather Underground, etc.)
  - Rain detection with configurable auto-resume delay
  - Rain forecast and precipitation threshold skip rules
  - Freeze protection
  - Cool/hot temperature adjustments
  - Wind speed and high humidity rules
  - Monthly seasonal adjustment multipliers
  - Weather pause vs. manual pause tracking (weather pauses auto-resume; manual pauses do not)
  - Weather event log with CSV export
  - Weather card on both homeowner and management dashboards
- **JSONL-Based Run History** — Replaced HA logbook with local JSONL storage for zone run events; includes weather conditions captured at the time of each event; CSV export for both homeowner and management
- **Management Access Control** — Consolidated management access into a single card on the Configuration page. Generate a connection key that grants full access to all devices (irrigation zones, moisture probes, weather, schedules, sensors); revoke access instantly with one click; management dashboard shows "Access Revoked" status with gray styling
- **Live Contact Sync** — Homeowner name, phone, and address are synced to the management dashboard automatically on every health check, even if added after the connection key was generated
- **First Name / Last Name Fields** — Added homeowner contact name fields that flow through the connection key to the management dashboard; displayed on property cards and detail views
- **Phone Number Field** — Homeowner phone number included in connection key and displayed on the management dashboard with click-to-call
- **Update Connection Key** — Management companies can update a customer's connection key without losing notes, aliases, or other metadata via a dedicated button on property cards
- **Connection Key Regeneration Lock** — The Generate Connection Key button is locked when an active key exists, requiring an explicit unlock + confirmation before regenerating (prevents accidental invalidation of the current key)
- **Connection Key Sharing** — Email button and QR code generation for easy connection key delivery
- **Entity Auto-Refresh** — Background task runs every 5 minutes to detect newly enabled/disabled entities in Home Assistant without requiring an add-on restart
- **Customer Search & Filtering** — Search properties by name, contact, address, phone, or notes; filter by status (online, offline, revoked)
- **Customer Notes** — Add notes to property cards on the management dashboard
- **Map Re-Center Button** — Re-center the Leaflet map on the homeowner dashboard
- **CSV Export** — Export run history and weather logs as CSV from both homeowner and management dashboards
- **Weather Log Clearing** — Clear weather event logs and run history from both dashboards
- **Dark Mode** — All pages (Homeowner Dashboard, Configuration, Management Dashboard) support a 🌙/☀️ dark mode toggle; uses CSS custom properties for consistent theming; preference saved per-device in localStorage with separate keys for homeowner and management sides
- **In-App Help** — Every page has a ❓ help button in the header that opens a scrollable modal with page-specific documentation:
  - Homeowner Dashboard: 7 sections (dashboard overview, zone control, sensors, schedules, weather, run history, system pause)
  - Configuration: 7 sections (overview, device selection, API keys, connection keys, weather settings, moisture probes, revoking access)
  - Management Dashboard: 11 sections (overview, adding properties, property cards, search/filtering, detail view, remote control, schedules, weather rules, run history, notes/aliases, updating keys)

- **Moisture Multiplier Badge** — The Moisture Probes card header now shows a multiplier badge (same style as the weather badge) reflecting the current overall moisture factor
- **Watering Factor Tile** — System Status card on both dashboards shows the combined watering factor (weather × moisture) with a breakdown of individual multipliers
- **Run History Factor Column** — Run history table includes a "Factor" column showing the combined weather × moisture multiplier for schedule-triggered events; CSV export includes moisture_multiplier and combined_multiplier columns

### Changed

- **Uptime Sensor Formatting** — Controller uptime sensor now displays as a cascading breakdown (e.g. "4 days 13 hrs 48 min") instead of a raw number with a unit; seconds removed for cleaner display; leading zero segments (years, months, weeks) are hidden when not applicable; sensor name shortened from "Irrigation System Irrigation Controller Uptime" to "Irrigation Controller Uptime"
- **Sensor Tile Targeted Updates** — Sensor tiles no longer rebuild the entire grid on every 30-second refresh; tiles are built once and only individual values are updated in place, eliminating flicker
- **Advanced Moisture Algorithm** — Replaced the simple weighted-average moisture algorithm with a gradient-based approach that uses each sensor depth as a distinct signal: the mid sensor (root zone) is the primary watering decision driver, the shallow sensor detects recent rain via wetting front analysis combined with weather forecast data, and the deep sensor guards against over-irrigation by detecting water pooling below the root zone
- **Moisture Probe Configuration on Configuration Page** — Probes are now configured from the Configuration page using a device picker dropdown (instead of keyword-based sensor scanning); select your Gophr device from a filtered list, map its sensors to shallow/mid/deep depths, and add the probe; the Homeowner Dashboard shows the moisture card once probes are added and enabled
- **Gophr Logo** — The Gophr logo is displayed next to the Moisture Probes card header on the Configuration page
- **Collapsible Device Entities** — The device entity list on the Configuration page (zones, sensors, controls) is now collapsed by default; click to expand and see the full list
- **Smart Device Filtering** — The device selection dropdown on the Configuration page now filters to show only irrigation-related devices by default (matching keywords like "Flux", "irrigation", "sprinkler", or "ESPHome"); click "Show all devices" to see the full list if needed
- **ESPHome Schedule Control** — System pause/resume now disables/restores ESPHome schedule programs on the controller, preventing the controller from starting runs while paused
- **Weather settings moved to control pages** — Weather configuration is now accessible from the homeowner and management control interfaces
- **Unit conversion improvements** — Better handling of temperature and wind speed units across weather integrations
- **Improved management dashboard** — Contact name, phone, and address displayed on property cards; revoked status detection and display; sort order includes revoked state
- **Apply Factors to Schedule** — Replaced the manual 3-button Duration Controls (Capture/Apply/Restore) with a single "Apply Factors to Schedule" toggle in the Schedule card. When enabled, the system automatically captures base run durations, applies the combined watering factor (weather × moisture), and keeps durations updated as conditions change. Disabling the toggle immediately restores original durations.
- **Watering Factor tile conditional breakdown** — The Watering Factor tile on the System Status card now only shows the moisture multiplier (M: x.xx) when moisture probes are enabled and configured; otherwise it only shows the weather multiplier (W: x.xx)

### Fixed

- **Weather card flicker eliminated** — Weather card now uses targeted DOM updates instead of full innerHTML rebuilds; the card structure is built once and only individual text values/styles are updated on refresh; cache key uses only visible data (not timestamps) so unchanged weather doesn't trigger any DOM work
- **Slow weather rules save** — Moisture probe re-evaluation after saving weather rules now runs in the background instead of blocking the save response; previously the chain of HA service calls could cause noticeable delays
- **Weather rules not applied until next check** — Saving weather rules now immediately re-evaluates conditions and updates the watering multiplier badge; previously the multiplier only updated on the periodic check (up to 15 minutes later) or when clicking "Test Rules Now"
- **Button entity names** — Device control tiles for button entities no longer show the device name suffix (e.g. "Irrigation System Restart irrigation_controller" → "Irrigation System Restart") and the action button reads "PRESS"
- Run history "hours" parameter parsing error when the select dropdown value was empty — now uses `parseInt` with a fallback to 24 hours
- Phone number not visible on management dashboard even when set in connection key
- Zone 5 (and other disabled entities) not appearing — entities with `disabled_by` set are now properly filtered, and the auto-refresh task picks up newly enabled entities automatically
- Connection key regeneration after revoke no longer silently fails — fixed schema validation, stale API key reuse, and HA token corruption issues that prevented the revoke → regenerate → reconnect flow from working
- Management dashboard no longer incorrectly shows "Access Revoked" when the API key is simply stale — only the explicit revoked flag from the homeowner triggers revoked status
- HA Long-Lived Access Token validation prevents generating broken Nabu Casa connection keys when the token is missing or corrupted
- Homeowner dashboard JavaScript fatal error caused by unescaped single quotes in moisture probe onclick handlers — prevented all dashboard functionality from loading
- Moisture probe API helper `mapi()` was using undefined `BASE` variable instead of `HBASE` — moisture probe API calls would always fail

---

## [1.1.0] — 2026-02-06

### Added

- **Management Mode** — Multi-property dashboard for irrigation management companies to monitor and control remote homeowner systems
- **Connection Keys** — Base64-encoded keys containing API URL, credentials, and property metadata for easy homeowner-to-management setup
- **Nabu Casa Proxy** — Route management requests through Home Assistant's REST API via rest_command proxy for zero-config remote connectivity
- **Direct Connection Mode** — Support for port forwarding, Cloudflare Tunnel, Tailscale, and other direct access methods
- **Homeowner Dashboard** — Full local control with zone start/stop (timed or manual), sensor monitoring, and system status
- **Zone Aliases** — Custom display names for zones on both homeowner and management dashboards
- **Property Map** — Leaflet-based map showing property location on the homeowner dashboard
- **System Pause/Resume** — Emergency pause that stops all active zones
- **Audit Logging** — All API actions logged with timestamp, API key, action, and client IP
- **Rate Limiting** — Configurable per-minute request limits
- **Timed Zone Runs** — Start zones with an optional duration that auto-stops
- **Device Selection** — Admin UI to pick the irrigation controller device; auto-discovers zones, sensors, and control entities
- **Interactive API Docs** — Built-in Swagger UI at `/api/docs`
- **HA Events** — Custom events for automations (timed runs, schedule changes, rain delays, pause/resume)

---

## [1.0.0] — 2026-02-05

### Added

- Initial release
- Basic irrigation API with zone control, sensor monitoring, and system status
- API key authentication with configurable permissions
- Home Assistant add-on packaging
