# Changelog

All notable changes to the Flux Open Home Irrigation Control add-on are documented here.

---

## [1.1.8] — 2026-02-07

### Added

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
- **Revoke Management Access** — One-click button on the Configuration page to instantly revoke a management company's access, with a confirmation dialog; preserves HA token and all other settings so re-enabling is easy; management dashboard shows "Access Revoked" status with gray styling
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
  - Configuration: 6 sections (overview, device selection, API keys, connection keys, weather settings, revoking access)
  - Management Dashboard: 11 sections (overview, adding properties, property cards, search/filtering, detail view, remote control, schedules, weather rules, run history, notes/aliases, updating keys)

### Changed

- **ESPHome Schedule Control** — System pause/resume now disables/restores ESPHome schedule programs on the controller, preventing the controller from starting runs while paused
- **Weather settings moved to control pages** — Weather configuration is now accessible from the homeowner and management control interfaces
- **Unit conversion improvements** — Better handling of temperature and wind speed units across weather integrations
- **Improved management dashboard** — Contact name, phone, and address displayed on property cards; revoked status detection and display; sort order includes revoked state

### Fixed

- Phone number not visible on management dashboard even when set in connection key
- Zone 5 (and other disabled entities) not appearing — entities with `disabled_by` set are now properly filtered, and the auto-refresh task picks up newly enabled entities automatically
- Connection key regeneration after revoke no longer silently fails — fixed schema validation, stale API key reuse, and HA token corruption issues that prevented the revoke → regenerate → reconnect flow from working
- Management dashboard no longer incorrectly shows "Access Revoked" when the API key is simply stale — only the explicit revoked flag from the homeowner triggers revoked status
- HA Long-Lived Access Token validation prevents generating broken Nabu Casa connection keys when the token is missing or corrupted

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
