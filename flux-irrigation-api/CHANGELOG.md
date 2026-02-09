# Changelog

All notable changes to the Flux Open Home Irrigation Control add-on are documented here.

---

## [1.1.12] — 2026-02-09

### Changed

- **Wake schedule popup — all mapped zones** — The wake schedule popup now shows every zone mapped to a probe, not just the first mapped zone per schedule. Each entry displays the zone number, expected run time, and schedule label.
- **Wake schedule popup — keep-awake display** — When consecutive mapped zones are close together (gap between them ≤ probe sleep duration), the popup shows "Keep Awake" with an eye icon and blue "AWAKE" badge instead of a separate wake time, indicating the probe will stay awake through both zones rather than sleeping and re-waking.
- **Wake schedule popup — saturation skip display** — When all mapped zones are set to skip due to soil saturation, the popup shows a clear explanation ("All mapped zones are set to skip — probe will not wake to monitor watering") instead of the generic "No schedule calculated" message. Individual skipped zones show a red "SKIP" badge with strikethrough text.
- **Homeowner dashboard clock timezone** — The dashboard clock now uses the homeowner's timezone (derived from their US state) instead of the browser's local time. The wake schedule popup's NEXT marker also uses the homeowner's timezone for accurate comparison.
- **Management dashboard wake schedule timezone** — The NEXT marker in the management wake schedule popup now uses the customer's timezone (from their state field) instead of the manager's browser time.

### Fixed

- **Timeline recalculation delay on zone mapping changes** — Adding or removing zones from a probe's mappings now immediately recalculates the irrigation timeline. Previously, changes only took effect after the periodic evaluation cycle (5+ minutes). The `calculate_irrigation_timeline()` function is now called directly in the probe create, update, delete, and sleep duration endpoints.
- **Stale skip badges after zone unmapping** — Removing a zone from a probe's mappings now immediately clears the "Skip" badge from the schedule card. Previously, stale `adjusted_durations` entries from the last `apply_adjusted_durations()` call kept showing skip for unmapped zones. The probe update endpoint now re-applies adjusted durations (when factors are active) or cleans stale entries (when factors are off) immediately after zone mapping changes.
- **Wake schedule entries not sorted** — Wake schedule popup entries are now sorted chronologically by target wake time. Previously, entries could appear in arbitrary order when spanning multiple schedules.

---

## [1.1.11] — 2026-02-09

### Changed

- **Probe card cleanup** — Removed verbose per-zone factor detail lines (e.g., "Z3: Weather 1.00x × Moisture 1.50x = 1.50x ✓ Applied") from probe cards on both dashboards. The compact zone badges (e.g., "Z3 1.50x") remain and are sufficient.
- **Probe card header** — Reduced font size and gaps so the device name and zone badges fit on one line without wrapping.
- **Zone badges always visible** — Zones mapped to a probe now always show a badge, even when the moisture multiplier is exactly 1.00x (shown with a neutral border style). Previously, only non-1.0 multipliers showed badges.
- **Schedule card probe indicator** — Zones with a mapped moisture probe now show a 💧 indicator badge in the schedule card even when the combined multiplier is 1.0x, so users can immediately see which zones are probe-monitored.
- **Wake schedule always visible** — The probe card now always shows the "Wake Schedule" section with probe wake times and mapped zone run times, instead of hiding them behind a collapsed toggle. Each entry shows when the probe will wake and which zone it will monitor, with the next upcoming wake highlighted. When no zones are mapped or no schedule is calculated yet, a helpful message is shown instead.
- **Root Zone = Mid Sensor clarification** — All threshold labels, settings inputs, help text tables, and README now explicitly state that "Root Zone" refers to the **mid sensor** (where grass roots live). Threshold labels show "(mid)" and descriptions explain the mid sensor is the primary decision driver for all watering decisions.
- **Solar charging indicator** — Probe cards now show the solar charging state (☀️ Charging / 🌙 No Solar) alongside WiFi, battery, and sleep status when a solar charging entity is detected on the device.
- **Device keyword filter expanded** — The device dropdown for adding probes now also matches devices with "moisture" in the name, not just "gophr". This ensures ESPHome devices named "Moisture Sensor Device..." are shown automatically.

### Added

- **Solar charging autodetect** — The probe autodetect now detects `binary_sensor.*_solar_charging` entities and stores them in `extra_sensors.solar_charging`. The solar charging state is shown on probe cards on both dashboards. The autodetect summary shows a "Solar" badge when the entity is found.
- **Update Entities button** — Existing probes in the Manage Probes section now have an "Update Entities" button that re-runs the autodetect and updates sensor/extra_sensor mappings. This is useful when new entities are enabled in HA after the probe was initially configured, or when the device was re-adopted in ESPHome.
- **Autodetect diagnostic info** — When depth sensor detection fails, the autodetect response now includes diagnostic info (sensor count, filtered count, registry match count, disabled entity list, and a human-readable hint). The UI displays this info so users can understand WHY detection failed and what to fix.

### Fixed

- **Sleep disabled autodetect** — The probe autodetect now matches both `sleep_disabled` and `disable_sleep` entity name patterns. Previously, ESPHome devices with `disable_sleep` in the entity name (e.g., `switch.*_disable_sleep`) were not detected, preventing the Disable Sleep button from appearing on the probe card.
- **Autodetect entity prefix fallback** — If the HA entity registry reports a different device_id for control entities (switches, numbers, lights) than for sensor entities on the same physical device, the autodetect now falls back to matching by entity name prefix. This ensures the disable_sleep switch, status LED, sleep duration control, and solar charging entity are always detected when they share the same entity naming pattern as the device's moisture sensors.
- **Autodetect summary badges** — The probe setup screen now shows detection badges for Sleep Toggle, Status LED, Sleep Control, and Solar entities in addition to WiFi, Battery, and Sleep, so users can verify all device entities were detected before adding the probe.
- **Autodetect disabled entity detection** — When sensor entities are disabled in Home Assistant (common with newly added ESPHome devices), the autodetect now explicitly detects and reports them, telling the user exactly which entities need to be enabled. Previously, disabled entities were silently skipped, making the autodetect appear to fail for no reason.
- **Schedule timeline start time parsing** — The timeline calculator now correctly handles 12-hour time formats with AM/PM (e.g., "5:00 AM", "1:00 PM", "9:00 PM") in addition to 24-hour format. Previously, the parser only handled "HH:MM" format, causing all schedule start times to fail parsing when the irrigation controller uses 12-hour time format. This broke the probe wake schedule calculation completely.
- **SyntaxWarning escape sequence** — Fixed an invalid `\d` escape sequence in a JavaScript regex within a Python triple-quoted string. Python 3.12+ treats this as a SyntaxWarning; now properly escaped as `\\d`.
- **CPU optimization: `get_entities_by_ids()`** — For batches of 20 or fewer entity IDs, the function now fetches individual entity states in parallel instead of loading ALL entity states from HA. This dramatically reduces CPU and network overhead for timeline calculations, moisture evaluations, and other operations that only need a few entity states.
- **CPU optimization: schedule timeline debounce** — When multiple schedule entities change state rapidly (e.g., after an HA restart or bulk update), timeline recalculations are now debounced with a 3-second delay. Previously, each entity change triggered an immediate recalculation, causing 69+ concurrent recalculations that each made HTTP calls to HA.

---

## [1.1.10] — 2026-02-09

### Added

- **Probe-Aware Irrigation (Schedule Timeline)** — Complete rework of how Gophr moisture probes interact with scheduled irrigation runs. The system now calculates when each zone will run based on schedule start times and zone durations, then automatically reprograms the probe's sleep duration so it wakes ~10 minutes before its mapped zone. On wake, if the soil is saturated the zone is skipped (disabled via the enable_zone switch before it starts) and the system advances to the next zone. If not saturated, sleep is disabled to keep the probe awake for continuous mid-run monitoring. Between non-consecutive mapped zones, the probe sleeps and is reprogrammed to wake before the next mapped zone. After the last mapped zone finishes, the original sleep duration is restored and any skipped zones are re-enabled for the next run.
- **Schedule Timeline JSON** — New persistent file (`/data/irrigation_schedule.json`) stores the calculated zone execution timeline, probe-to-zone mappings, probe prep timing, and prep state machine. Timeline recalculates automatically whenever schedule start times, zone durations, zone enable states, probe sleep duration, or probe mappings change.
- **Schedule Timeline UI** — Probe cards on both homeowner and management dashboards now show a "Schedule Timeline" section with expected zone start times, which zones have mapped probes, and the probe's target wake time. Probe status indicators show current prep state (Waking for zone, Monitoring zone, Between zones).
- **Schedule Timeline API** — `GET /admin/api/homeowner/moisture/schedule-timeline` returns the current timeline; `POST /admin/api/homeowner/moisture/schedule-timeline/recalculate` forces a recalculation.
- **Skip-and-Advance** — When mid-run moisture monitoring detects saturation, the current zone is shut off and the system automatically starts the next enabled zone with auto advance enabled, preventing schedule gaps.
- **Schedule Entity Watching** — WebSocket watcher expanded to detect changes to schedule start times (`text.*_start_time_*`), zone run durations (`number.*_run_duration`), and zone enable states (`switch.*_enable_zone_*`), triggering an automatic timeline recalculation.

### Changed

- **Deprecated `sync_schedule_times_to_probes()`** — The old system that synced irrigation schedule times to probe ESPHome entities has been replaced by the new probe-aware timeline system. The old sync endpoint returns a deprecation warning.
- **Periodic evaluation** — `_periodic_moisture_evaluation()` now calls `calculate_irrigation_timeline()` instead of the deprecated `sync_schedule_times_to_probes()`.

### Fixed

- **Management dashboard map** — Properties without address data now show "Map unavailable — no address configured" instead of silently hiding the map div. Geocoding failures also show appropriate messages instead of blank space.

---

## [1.1.9] — 2026-02-08

### Added

- **Expansion Board Zone Filtering** — Controllers with expansion boards pre-create entities for up to 32 zones (3 expansion boards × 8 zones + 8 base). The system now reads the `detected_zones` sensor to determine how many zones are physically connected and automatically filters zone tiles, schedule durations, zone enables, and zone modes throughout the dashboard to only show connected zones. Controllers without expansion board support are unaffected.
- **Auto Advance Toggle on Zone Card** — The Auto Advance toggle has been moved from the Schedule "System Controls" section to the Zone card header, where it belongs. Auto Advance controls whether manually running zones automatically advance to the next zone, which is a zone behavior, not a schedule setting.
- **Default Zone Naming** — Zones are now displayed as "Zone 1", "Zone 2", etc. by default instead of using the raw HA entity friendly name. User-created aliases override the default name and are never overwritten.

### Changed

- **Zone display names** — Zones without an alias now show "Zone N" instead of the HA entity friendly name (which was often unwieldy, e.g., "Irrigation System Zone 1")
- **Auto Advance placement** — Moved from Schedule card System Controls section to Zone card header on both homeowner and management dashboards
- **Schedule Card Factor Preview** — The schedule card now always shows the projected adjusted duration next to each zone's run duration input, even when "Apply Factors to Schedule" is not enabled. The badge shows what the duration would be given the current combined watering factor (weather × moisture). When factors are actively applied, the badge shows the applied value as before. The "Apply Factors" toggle also now shows the current combined factor breakdown (e.g., "Current factor: 0.64x (W:0.80 × M:0.80)").
- **Pump/Master Valve zone ordering** — Zones configured as Pump Start Relay or Master Valve are now sorted to appear after all normal irrigation zones in both the zone card tiles and the schedule card zone settings table
- **Moisture card cleanup** — Removed the Zone Multipliers section from the moisture probe card for a cleaner layout; per-zone multiplier data remains accessible via the API and is reflected in schedule card factor badges

### Fixed

- **System Status watering factor** — The system status tile now shows the combined watering factor (weather × moisture) instead of only the weather factor. When moisture probes are enabled, the breakdown shows both components (e.g., "W: 0.80x · M: 0.90x"). The `/api/system/status` endpoint now includes `weather_multiplier`, `moisture_multiplier`, `combined_multiplier`, `moisture_enabled`, and `moisture_probe_count` fields, fixing the management dashboard which was missing moisture data.
- **Moisture multiplier lost during Gophr sleep** — Gophr devices sleep between readings, causing HA to mark sensor entities as "unavailable". Previously this made the algorithm fall back to 1.0x (neutral), effectively erasing the moisture adjustment every sleep cycle. Now the last known good sensor values are cached (in memory and on disk) and used transparently when sensors are unavailable. The stale reading threshold still applies — if cached values are older than the threshold they are treated as stale. Cache survives add-on restarts.
- **Status tile zone count with expansion boards** — The system status tile "Zones" count now respects the detected zone count from expansion boards, showing e.g. "16 zones" instead of "32 zones" when only 2 expansion boards are connected.
- **Watering factor mismatch between status tile and schedule card** — The status tile and the schedule card per-zone duration badges could show different multiplier values (e.g., 0.84 vs 0.88) because they used different calculation paths — the status tile used a system-wide overall multiplier while per-zone badges used a zone-specific multiplier. Now both use the same system-wide overall multiplier for consistency. All zones see the same combined factor, matching the status tile.

---

## [1.1.8] — 2026-02-07

### Added

- **Issue Reporting System** — Homeowners can report issues directly from their dashboard with three severity levels (Clarification, Annoyance, Severe Issue) and a description field; management company receives color-coded alerts on property cards and a persistent alert badge in the management header
- **Management Alert Badge** — Real-time notification badge in the management header showing total active issues across all properties; click to view all issues grouped by customer in a dedicated alerts panel
- **Browser Notifications** — Configurable push notifications for management when new issues are reported; notification preferences per severity level stored in localStorage
- **Upcoming Service Banner** — When management schedules a service date, a green banner appears on the homeowner dashboard showing the date and any management notes; tap the banner to add the service appointment directly to your device's calendar app with the date, address, and notes pre-filled
- **Clickable Addresses** — Property addresses are now clickable on both the homeowner and management dashboards; opens in Apple Maps on iOS/Mac or Google Maps on other devices for easy navigation
- **Issue Acknowledge & Schedule** — Management can acknowledge issues with a note and optionally schedule a service date; issue status flows through open → acknowledged → scheduled → resolved → dismissed
- **Issue Dismiss** — Resolved issues remain visible to the homeowner so they can see management's response and notes; homeowner clicks "Dismiss" to remove the resolved issue from their dashboard
- **HA Issue Notifications** — Send push notifications through Home Assistant's notification service (mobile app, SMS, etc.) when customers report new issues; configurable per-severity filters and a test button to verify the setup; settings persist server-side in `/data/notification_config.json`
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

- **Rain Sensor Card** — Dedicated dashboard card for rain sensor hardware entities. Groups rain sensor status (Dry/Rain Detected), rain sensor enable/disable toggle, sensor type selector (NC/NO), rain delay enable/disable, rain delay duration (1-72 hours), and rain delay active status into a single card with a color-coded status badge. Automatically appears when rain sensor entities are detected on the controller; hidden otherwise. Available on both homeowner and management dashboards.
- **Expansion Board Card** — Dedicated dashboard card for I2C expansion board status. Shows total detected zone count, connected expansion board I2C addresses with zone ranges, and a Rescan button to trigger I2C bus re-detection. When no expansion boards are connected, displays "No expansion boards connected" with the base zone count. Available on both homeowner and management dashboards.
- **Probe Device Status Sensors** — Moisture probe cards on both homeowner and management dashboards now show WiFi signal strength, battery percentage, and sleep duration alongside the three moisture depth readings; device sensors are auto-detected from entity names at probe creation time and stored for efficient lookup
- **Probe Auto-Detection** — New `/devices/{id}/autodetect` API endpoint automatically maps Gophr device sensors to depth assignments (moisture 3 → shallow, moisture 2 → mid, moisture 1 → deep) and detects WiFi, battery percentage, and sleep duration sensors; raw voltage entities are skipped entirely in favor of percentage readings; AHT20 ambient humidity/temperature sensors are excluded from moisture detection
- **Device-Based Probe Setup** — Both the Configuration page and Homeowner Dashboard "Manage Probes" section now use a device picker with auto-detection instead of the old entity-based "Discover Probes" flow; select a Gophr device and sensors are automatically mapped
- **Gophr-Only Device Filtering** — Device picker dropdowns only show devices with "gophr" in the name by default; "Show all devices" toggle available as fallback
- **Homeowner Probe Zone Assignment** — Homeowners can now assign zones to probes directly from the dashboard probe cards via checkbox-based zone picker with Select All/None and friendly zone names
- **Management Probe Zone Assignment** — Management companies can now assign and edit zone-to-probe mappings directly from the management dashboard detail view; uses the same checkbox-based zone picker
- **Moisture Multiplier Badge** — The Moisture Probes card header now shows a multiplier badge (same style as the weather badge) reflecting the current overall moisture factor
- **Watering Factor Tile** — System Status card on both dashboards shows the combined watering factor (weather × moisture) with a breakdown of individual multipliers
- **Run History Factor Columns** — Run history table shows a "Watering Factor" column (weather multiplier) and a "Probe Factor" column (moisture multiplier, only visible when probe data exists); probe factor includes moisture % readings and which sensor depth (T/M/B) drove the adjustment; CSV export includes watering_multiplier, moisture_multiplier, and combined_multiplier columns

### Changed

- **Uptime Sensor Formatting** — Controller uptime sensor now displays as a cascading breakdown (e.g. "4 days 13 hrs 48 min") instead of a raw number with a unit; seconds removed for cleaner display; leading zero segments (years, months, weeks) are hidden when not applicable; sensor name shortened from "Irrigation System Irrigation Controller Uptime" to "Irrigation Controller Uptime"
- **Sensor Tile Targeted Updates** — Sensor tiles no longer rebuild the entire grid on every 30-second refresh; tiles are built once and only individual values are updated in place, eliminating flicker
- **Advanced Moisture Algorithm** — Replaced the simple weighted-average moisture algorithm with a gradient-based approach that uses each sensor depth as a distinct signal: the mid sensor (root zone) is the primary watering decision driver, the shallow sensor detects recent rain via wetting front analysis combined with weather forecast data, and the deep sensor guards against over-irrigation by detecting water pooling below the root zone
- **Moisture Probe Configuration on Configuration Page** — Probes are now configured from the Configuration page using a device picker dropdown (instead of keyword-based sensor scanning); select your Gophr device from a filtered list, map its sensors to shallow/mid/deep depths, and add the probe; the Homeowner Dashboard shows the moisture card once probes are added and enabled
- **Gophr Logo** — The Gophr logo is displayed next to the Moisture Probes card header on the Configuration page, Homeowner Dashboard, and Management Dashboard; uses `var(--text-primary)` fill for dark/light mode support
- **Collapsible Device Entities** — The device entity list on the Configuration page (zones, sensors, controls) is now collapsed by default; click to expand and see the full list
- **Smart Device Filtering** — The device selection dropdown on the Configuration page now filters to show only irrigation-related devices by default (matching keywords like "Flux", "irrigation", "sprinkler", or "ESPHome"); click "Show all devices" to see the full list if needed
- **ESPHome Schedule Control** — System pause/resume now disables/restores ESPHome schedule programs on the controller, preventing the controller from starting runs while paused
- **Weather settings moved to control pages** — Weather configuration is now accessible from the homeowner and management control interfaces
- **Unit conversion improvements** — Better handling of temperature and wind speed units across weather integrations
- **Improved management dashboard** — Contact name, phone, and address displayed on property cards; revoked status detection and display; sort order includes revoked state
- **Apply Factors to Schedule** — Replaced the manual 3-button Duration Controls (Capture/Apply/Restore) with a single "Apply Factors to Schedule" toggle in the Schedule card, positioned directly below the Schedule Enable toggle. When enabled, the system automatically captures base run durations, applies the combined watering factor (weather × moisture), and keeps durations updated as conditions change. Each zone's Run Duration input shows the base duration (what the user sets) and a badge shows the adjusted duration with the factor (e.g. "24 min (0.80x)"). Setting a duration via the Set button always updates the base, even while factors are active — no need to disable factors first. Disabling the toggle immediately restores original durations.
- **Configuration Change Log** — Persistent log of all configuration changes with rolling 1000-entry buffer. Shows who made each change (Homeowner or Management), when (date/time), the category (Schedule, Weather Rules, Moisture Probes, System, Zone Control, Device Config, Connection Key), and a human-readable description with old → new values for every changed property. Click the **Log** button in the property detail view (management) or 📋 icon (homeowner) to view the changelog modal. Export to CSV. Records cannot be deleted. Management company changes are tracked via the X-Actor header. Available on both homeowner and management dashboards.
- **QR Code Scanning** — Management dashboard can now scan a homeowner's QR code to add a property. Click "Scan QR Code" in the Add Property form to open the camera, point it at the homeowner's QR code, and the connection key is filled in automatically. Uses the device camera via the html5-qrcode library; camera permission is requested on first use.
- **Customer Local Time** — The management dashboard detail view shows the customer's local time in 12-hour format with timezone abbreviation (e.g., "2:30 PM EST"), derived from the customer's state; updates every 30 seconds
- **Dashboard Layout** — Schedule card is now positioned directly under Zones on both homeowner and management dashboards for quicker access to schedule settings
- **Mobile Responsive Improvements** — Zone settings table adapts to narrow screens (mobile-only media query: `table-layout: fixed`, smaller inputs, wrapping duration cells); customer cards are more compact on mobile (reduced padding, font sizes, and gaps) to show more properties at once
- **Collapsible Weather Rules** — The Weather Rules section on both homeowner and management dashboards is now collapsed by default with a chevron indicator; click to expand and view/edit rules; action buttons (Test Rules Now, Export Log, Clear Log) remain visible in the collapsed header
- **Watering Factor tile conditional breakdown** — The Watering Factor tile on the System Status card now only shows the moisture multiplier (M: x.xx) when moisture probes are enabled and configured; otherwise it only shows the weather multiplier (W: x.xx)
- **Detailed Change Log Entries** — All changelog entries now show the exact property changed with old → new values (e.g., "Humidity Threshold (%): 80 -> 90", "Phone: (empty) -> 555-1234", "Zone alias Zone 1: Front Yard -> Front Garden"). Applies to weather rules, entity set operations, general settings, moisture settings (thresholds, depth weights, stale reading threshold, apply factors toggle), zone aliases, moisture probe updates (sensor mappings, zone assignments), and connection key contact info (name, phone, address, city, state, ZIP, URL)

### Fixed

- **Homeowner Dashboard Clock** — The homeowner dashboard now shows a live clock (e.g. "3:45 PM CST") matching the management dashboard's format, instead of only the timezone abbreviation
- **Management Dark Mode Toggle** — The dark mode toggle button on the management dashboard now correctly shows ☀️ in dark mode and 🌙 in light mode (previously always showed 🌙 due to incorrect element selector)
- **Modal z-index on mobile** — Changelog, help, QR code, and revoke confirmation modals on the homeowner and admin dashboards were rendered behind the Leaflet map on mobile (z-index:999 vs Leaflet's ~1000). Fixed by bumping all modal z-index to 10000 (matching management dashboard which already worked correctly)
- **Apply Factors to Schedule — "applied to 0 zones" / "no run duration entities"** — Completely rewrote duration entity discovery to support all ESPHome naming conventions (e.g. `number.*_run_duration`, `number.irrigation_system_zone_N`, `number.duration_zone_N`); zone-to-duration mapping now uses zone number extraction instead of substring matching; added fallback to re-resolve device entities if config is empty; values sent as float to match HA expectations
- **Apply Factors toggle flashing** — The toggle is now rendered inline as part of the schedule card HTML using the already-fetched duration data (`duration_adjustment_active`), eliminating the separate async API call that caused visible flicker; controls/schedule section only loads once on initial page load (homeowner) or per customer view (management) instead of every refresh cycle
- **Watering Factor tile always showing 1x** — Weather and moisture multiplier fetching are now fully isolated in the status endpoint; previously both were in a single try/except block, so any moisture probe error would cause the weather multiplier to also default to 1.0; weather multiplier is now read directly from the weather rules file in its own independent block
- **Durations not restoring when multiplier returns to 1.0x** — Weather rules save and evaluate now run the moisture duration re-application synchronously (not in background) so that by the time the frontend refreshes, the HA entities and duration data reflect the updated multiplier; schedule card now also refreshes after saving/evaluating weather rules; schedule card now shows the computed adjusted value from stored data instead of the live HA entity state (eliminates propagation delay)
- **Factor badge always orange** — The factor badge in the schedule card now shows green text when the combined multiplier is 1.0x (no adjustment) and orange when the multiplier differs from 1.0x
- **Weather card flicker eliminated** — Weather card now uses targeted DOM updates instead of full innerHTML rebuilds; the card structure is built once and only individual text values/styles are updated on refresh; cache key uses only visible data (not timestamps) so unchanged weather doesn't trigger any DOM work
- **Weather rules not applied until next check** — Saving weather rules now immediately re-evaluates conditions and updates the watering multiplier badge; previously the multiplier only updated on the periodic check (up to 15 minutes later) or when clicking "Test Rules Now"
- **Button entity names** — Device control tiles for button entities no longer show the device name suffix (e.g. "Irrigation System Restart irrigation_controller" → "Irrigation System Restart") and the action button reads "PRESS"
- Run history "hours" parameter parsing error when the select dropdown value was empty — now uses `parseInt` with a fallback to 24 hours
- Phone number not visible on management dashboard even when set in connection key
- Zone 5 (and other disabled entities) not appearing — entities with `disabled_by` set are now properly filtered, and the auto-refresh task picks up newly enabled entities automatically
- Connection key regeneration after revoke no longer silently fails — fixed schema validation, stale API key reuse, and HA token corruption issues that prevented the revoke → regenerate → reconnect flow from working
- Management dashboard no longer incorrectly shows "Access Revoked" when the API key is simply stale — only the explicit revoked flag from the homeowner triggers revoked status
- HA Long-Lived Access Token validation prevents generating broken Nabu Casa connection keys when the token is missing or corrupted
- Homeowner dashboard JavaScript fatal error caused by unescaped single quotes in moisture probe onclick handlers — prevented all dashboard functionality from loading
- **Base durations corrupted by manual Set or crash recovery** — Setting a run duration via the Set button now always updates the stored base duration (regardless of whether Apply Factors is active); if factors are active, the new base is immediately multiplied by the current factor; crash recovery no longer re-captures base durations from HA entities (which may contain adjusted values); uses stored base values instead and only captures fresh if no stored base exists
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
