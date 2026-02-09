# Flux Open Home Irrigation Control

> **This add-on requires the Flux Open Home Irrigation Controller.**
> Purchase yours at [www.fluxopenhome.com](https://www.fluxopenhome.com).

A Home Assistant add-on that provides dual-mode irrigation management for the Flux Open Home Irrigation Controller. Homeowners get a local dashboard with zone control, scheduling, weather intelligence, and sensor monitoring. Management companies get a multi-property dashboard to monitor and control all their customers' irrigation systems from a single interface.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Homeowner Setup](#homeowner-setup)
  - [Step 1: Install and Start](#step-1-install-and-start)
  - [Step 2: Select Your Irrigation Device](#step-2-select-your-irrigation-device)
  - [Step 3: One-Time configuration.yaml Setup (Nabu Casa Only)](#step-3-one-time-configurationyaml-setup-nabu-casa-only)
  - [Step 4: Create a Long-Lived Access Token (Nabu Casa Only)](#step-4-create-a-long-lived-access-token-nabu-casa-only)
  - [Step 5: Generate a Connection Key](#step-5-generate-a-connection-key)
  - [Step 6: Set Up Weather-Based Control (Optional)](#step-6-set-up-weather-based-control-optional)
  - [Revoking Management Access](#revoking-management-access)
- [Management Company Setup](#management-company-setup)
- [Features](#features)
- [Weather-Based Irrigation Control](#weather-based-irrigation-control)
- [Connection Methods](#connection-methods)
- [Configuration Reference](#configuration-reference)
- [API Endpoints](#api-endpoints)
- [HA Events](#ha-events)
- [Troubleshooting](#troubleshooting)

---

## Requirements

- **Home Assistant** 2024.1 or newer
- **Flux Open Home Irrigation Controller** connected to your Home Assistant instance ([purchase here](https://www.fluxopenhome.com))
- For remote management connectivity (choose one):
  - **Nabu Casa** subscription (recommended — easiest setup)
  - Cloudflare Tunnel
  - Port forwarding + DuckDNS
  - Tailscale / WireGuard VPN

---

## Installation

1. Open Home Assistant
2. Go to **Settings → Add-ons → Add-on Store**
3. Click the **⋮** (three dots) menu → **Repositories**
4. Paste: `https://github.com/FluxOpenHome/ha-flux-irrigation-addons`
5. Click **Add → Close**
6. Find **Flux Open Home Irrigation Control** in the store and click **Install**
7. After installation, go to the add-on's **Configuration** tab
8. Enable **Show in sidebar** if desired, then click **Start**

---

## Homeowner Setup

### Step 1: Install and Start

Install the add-on from the repository (see [Installation](#installation) above) and start it. Open the add-on panel — you will see the **Homeowner Dashboard** by default.

Click **Configuration** in the top navigation to access the settings page.

### Step 2: Select Your Irrigation Device

On the Configuration page:

1. Find the **Irrigation Controller Device** section
2. Select your **Flux Open Home Irrigation Controller** from the dropdown — the list is automatically filtered to show only irrigation-related devices (matching keywords like "Flux", "irrigation", "sprinkler", or "ESPHome")
3. If your controller doesn't appear, click **Show all devices** below the dropdown to see every device in Home Assistant
4. The add-on will automatically discover all zones (switches/valves) and sensors belonging to that device

> **Important:** Only entities belonging to the selected device are exposed through the API. No other Home Assistant devices, entities, or data are accessible.

### Step 3: One-Time configuration.yaml Setup (Nabu Casa Only)

If you plan to use **Nabu Casa** for remote management connectivity, you need to add the following to your Home Assistant `configuration.yaml` file **once**:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

**How to edit configuration.yaml:**
1. In Home Assistant, go to **Settings → Add-ons**
2. Install and open the **File Editor** add-on (or use **Studio Code Server**)
3. Open `/config/configuration.yaml`
4. Add the two lines above (if `homeassistant:` already exists, just add the `packages:` line under it)
5. **Restart Home Assistant** (Settings → System → Restart)

The add-on automatically creates a proxy configuration file in `/config/packages/` that enables Nabu Casa connectivity. This only needs to be done once — the file is regenerated automatically on each add-on startup.

> **Note:** If you are using **Direct Connection** mode (port forwarding, Cloudflare Tunnel, etc.), you can skip this step.

### Step 4: Create a Long-Lived Access Token (Nabu Casa Only)

If using Nabu Casa, you need a Home Assistant Long-Lived Access Token:

1. In Home Assistant, click your **user profile** (bottom-left of the sidebar — your name/avatar)
2. Click the **Security** tab at the top of the profile page
3. Scroll down to **Long-Lived Access Tokens**
4. Click **Create Token**
5. Name it `Irrigation Management` (or any name you prefer)
6. **Copy the token immediately** — it is only shown once
7. Paste it into the **HA Long-Lived Access Token** field on the Configuration page

> **Note:** This token is only used for the Nabu Casa proxy connection. It is never shared with the management company. If using Direct Connection mode, you can skip this step.

### Step 5: Generate a Connection Key

On the Configuration page, in the **Connection Key for Management Company** section:

1. **Choose your connection method:**
   - **Nabu Casa** (recommended) — Enter your Nabu Casa URL (find it at Settings → Home Assistant Cloud → Remote Control)
   - **Direct Connection** — Enter your externally accessible URL (e.g., `https://your-domain.duckdns.org:8099`)

2. Fill in **Property Label**, **Street Address**, **City**, **State**, and **ZIP Code** (used for display on the management dashboard and map)

3. Click **Generate Connection Key**

4. **Copy the connection key** and send it to your management company. They will paste this into their Flux Open Home Irrigation Control add-on to connect to your system.

> **Tip:** You can send the connection key via the **Email** button or display it as a **QR code**. Your management company can scan the QR code directly from their dashboard when adding a property.

> **Note:** Once a connection key has been generated, the Generate button is locked to prevent accidental regeneration. To generate a new key (which invalidates the old one), click **Unlock to Regenerate** and confirm.

### Step 6: Set Up Weather-Based Control (Recommended)

We recommend the **NWS (National Weather Service)** integration for the most accurate weather data. It is free and the government does not charge for this service or issue API keys.

1. In Home Assistant, go to **Settings → Devices & Services**. Click the **+ Add Integration** button in the bottom-right corner. Search for **NWS** (National Weather Service).
2. **API Key** — The NWS does not issue API keys. You can type any value here (e.g., `123456789`).
3. **Latitude & Longitude** — Home Assistant will pre-fill these with your current location. If you are not at the same location as your irrigation controller, go to [latlong.net](https://www.latlong.net/convert-address-to-lat-long.html) and type in the controller's address to get the correct coordinates.
4. **METAR Station** — METAR is a weather station that reports local conditions. Home Assistant will pre-fill this with the closest station to your location. If you want to verify or change it, go to the [Turbli METAR Map](https://turbli.com/maps/world-metar-map/) and find the closest circle to your property — hover over it to see the **4-letter station code** (e.g., KMCO, KORL).
5. **Area** — Assign it to an area in Home Assistant (e.g., "Outdoors" or your home name).
6. Come back to the **Configuration** page in the add-on. Scroll down to **Weather-Based Control**, enable the toggle, and select your new weather entity from the dropdown. It will match the METAR station code you entered (e.g., `weather.kmco`).
7. Configure the weather rules to your preference and click **Save Weather Settings**.

See [Weather-Based Irrigation Control](#weather-based-irrigation-control) below for full details on all supported weather integrations and rule configuration.

### Revoking Management Access

You can disconnect a management company at any time from the Configuration page:

1. Scroll to the **Management Access** section (visible when a connection key has been generated)
2. Click the **Revoke Access** button
3. A confirmation dialog will appear warning you that your management company will immediately lose access to your irrigation system
4. Click **Yes, Revoke Access** to confirm

**What happens when you revoke:**
- The management company's API key is immediately deleted — they can no longer control or monitor your system
- The old connection key becomes invalid and cannot be reused
- Your HA Long-Lived Access Token, name, address, phone, and other settings are preserved — you do not need to re-enter them
- The URL field is cleared so you must generate a new connection key if you want to re-enable access

**On the management side:**
- The property card will show an **Access Revoked** status (gray dot) on the next health check
- The management company cannot restore access on their own — the homeowner must generate and share a new connection key

**Re-enabling access after revoke:**
1. Enter your URL again on the Configuration page (all other fields are still filled in)
2. Click **Generate Connection Key** — a new API key will be created automatically
3. Send the new connection key to your management company
4. On the management side, they can click the **Update Key** button on the existing property card and paste the new key — all notes, aliases, and metadata are preserved

---

## Management Company Setup

1. Install the same add-on on your Home Assistant instance (see [Installation](#installation))
2. Open the add-on panel and click **Switch to Management** (or go to the add-on's Configuration tab and set **mode** to `management`, then restart)
3. Click **+ Add Property**
4. Either **paste the connection key** provided by a homeowner, or click **Scan QR Code** to scan the homeowner's QR code with your camera
5. The property will appear in the dashboard with live status, zone control, sensors, schedules, and weather conditions

The management dashboard automatically checks connectivity to all properties every 5 minutes and shows online/offline status.

**Updating a connection key:** If a homeowner regenerates their connection key, you don't need to delete and re-add the property. Click the **Update Key** button on the property card, paste the new key, and all your notes, aliases, and metadata are preserved.

---

## Features

### Homeowner

- 🏠 **Homeowner Dashboard** — Full local control with zone start/stop (timed or manual), auto advance, sensor monitoring, schedule management, run history, and weather conditions
- ☀️ **Weather-Based Control** — 9 configurable weather rules that automatically pause, reduce, or increase irrigation based on real-time conditions and forecasts
- 🔐 **Connection keys** — Simple encoded key shares the API URL and credentials for easy setup (send via copy, email, or QR code)
- 🔒 **Connection key regeneration lock** — The Generate button is locked when an active key exists, requiring an explicit unlock to prevent accidental invalidation
- 🔓 **Revoke access** — Instantly revoke management company access with one click, with a confirmation dialog to prevent accidents
- 📚 **Run history** — JSONL-based local storage of zone run events with weather conditions captured at run time; CSV export
- ✏️ **Zone aliases** — Zones default to "Zone 1", "Zone 2", etc.; give zones friendly display names with aliases that persist across refreshes
- 🔩 **Zone head details** — Click the ℹ icon on any zone to document every sprinkler head in the zone: head type (pop-up spray, rotary, gear rotor, impact, micro-spray, bubbler, drip, strip), brand & model from a filtered picklist of 65+ real sprinkler models (with GPM auto-fill), mount type, spray arc, throw radius, pop-up height, PSI, and a name/location for each head; total zone GPM is calculated automatically and displayed prominently on each zone card; model database stored in an easily-editable `sprinkler_models.json` file
- 📍 **Location map** — Leaflet map on the dashboard shows property location with re-center button
- 🌱 **Gophr Moisture Probes** — Select Gophr devices from a filtered device picker and map sensors to irrigation zones (many-to-many); moisture multiplier adjusts both API timed runs and ESPHome scheduled durations; combined weather × moisture multiplier; probe cards show WiFi signal, battery level, solar charging status, sleep duration, and estimated next wake time alongside moisture readings; the **mid sensor (root zone)** drives all watering decisions — shallow detects rain, deep guards against over-irrigation; Gophr logo displayed on all dashboard Moisture Probes card headers with dark/light mode support
- 🌧️ **Rain Sensor Card** — Dedicated card for rain sensor hardware entities showing sensor state (Dry/Rain Detected), enable/disable, sensor type (NC/NO), rain delay controls, and delay duration; auto-detected from controller entities
- 🔌 **Expansion Board Card** — Dedicated card for I2C expansion board status showing detected zone count, board I2C addresses with zone ranges, and rescan button; automatically filters all zone-related entities (tiles, durations, enables, modes) to only show the physically connected zones — firmware pre-creates up to 32 zone entities but only connected zones are displayed
- ⚠️ **Issue Reporting** — Report issues to your management company with three severity levels (Clarification, Annoyance, Severe Issue); track issue status (Submitted, Acknowledged, Service Scheduled) and see management notes
- 📅 **Upcoming Service** — When your management company schedules a service visit, a green banner appears at the top of the dashboard showing the date and any notes from management; tap the banner to add the appointment directly to your device's calendar app
- 📍 **Clickable Address** — Tap your property address to open it in Apple Maps (iOS/Mac) or Google Maps (Android/other) for directions
- ▶ **Auto Advance** — Toggle at the top of the zone card. To manually run zones with auto advance: start the first zone (timed), then enable Auto Advance — each zone will automatically advance to the next enabled zone when its timer expires
- ⏸️ **System pause/resume** — Emergency pause that stops all active zones and suspends ESPHome schedule programs
- 🌙 **Dark mode** — Toggle between light and dark themes; preference is saved per-device and applied instantly
- 📄 **PDF System Report** — Generate a comprehensive, professionally branded PDF report covering your entire system: status, zones, zone head/nozzle details, schedule, weather settings & active adjustments, moisture probes, sensors, estimated water usage (gallons), and run history. Select a time range (24h, 7d, 30d, 90d, or 1yr) for history and usage data. Branded with Flux Open Home and Gophr logos
- ⚡ **Pump Monitor** — Automatically detected when a zone is configured as "Pump Start Relay"; displays a dedicated card alongside Estimated Gallons showing total pump cycles, run hours, power used (kWh), and estimated electricity cost; configurable time range (24h, 30d, 90d, 1yr); settings gear for pump specs (brand, HP/kW with auto-conversion, voltage, year installed, electricity cost $/kWh, peak rate); pump age calculated automatically from year installed; when no pump relay is detected, the Estimated Gallons card stays full-width
- ❓ **In-app help** — Button on every page opens a condensed, page-specific help modal covering the features and controls visible on that screen. For the complete documentation, see this README

### Management

- 🏢 **Management Dashboard** — Multi-property grid view with click-to-expand detail cards for each property
- 📷 **QR code scanning** — Scan a homeowner's QR code with your camera to add a property instantly, instead of pasting the connection key
- 🔐 **Update connection key** — Swap a customer's connection key without losing notes, aliases, or metadata
- 🔍 **Customer search and filtering** — Search properties by name, contact, address, phone, or notes; filter by status (online, offline, revoked) and by state or city
- 📝 **Customer notes** — Add and edit notes on property cards
- 🔄 **Live contact sync** — Homeowner name, phone, and address are synced automatically on every health check, even if added after the connection key was generated
- 🕐 **Customer local time** — Property detail view shows the customer's local time and timezone abbreviation (e.g., "2:30 PM EST"), derived from the customer's state address
- 💧 **Remote zone control** — Start, stop, and emergency-stop zones on any connected property; Auto Advance toggle at the top of the zone card lets you start the first zone and have it automatically advance through all enabled zones
- 🔩 **Remote zone head details** — View and edit sprinkler head inventory on customer zones: head type, brand & model from a filtered picklist with GPM auto-fill, mount, spray arc, radius, pop-up height, PSI, and location notes; total zone flow calculated automatically and displayed on zone cards; model database in `sprinkler_models.json` for easy extension
- ☀️ **Remote weather management** — View and configure weather rules on customer systems
- 🌱 **Remote moisture management** — Configure Gophr moisture probe settings (enable/disable, thresholds, depth weights), view live probe data with device status (WiFi, battery, sleep), assign zones to probes, and manage duration adjustments on customer systems
- 🌧️ **Remote rain sensor management** — View and control rain sensor settings (enable/disable, sensor type, rain delay) on customer systems
- 🔌 **Remote expansion board status** — View detected zones, expansion board I2C addresses, and trigger rescans on customer controllers
- ⚠️ **Issue Management** — View and manage homeowner-reported issues across all properties; color-coded alerts on property cards; dedicated alerts panel with all active issues; acknowledge issues with notes and schedule service dates; browser notifications and HA push notifications (mobile app, SMS, etc.) when new issues are reported
- 📍 **Clickable Addresses** — Click any property address on cards or detail views to open it in Apple Maps or Google Maps for easy navigation to the property
- 📅 **Remote schedule management** — View and update irrigation schedules (entity-based, driven by the Flux Open Home controller's ESPHome configuration)
- 📚 **Run history and CSV export** — View and export zone run history and weather logs for each property
- 📄 **PDF System Report** — Generate a branded PDF system report for any customer property: system status, zones with head details, schedule, weather, moisture, sensors, estimated gallons, and run history with selectable time range (24h–1yr)
- ⚡ **Remote Pump Monitor** — View pump usage statistics on customer properties with a pump start relay: total cycles, run hours, power consumption (kWh), and estimated cost; configure pump settings (brand, HP/kW, voltage, year installed, electricity rates) remotely; pump age displayed automatically
- 📖 **Interactive API docs** — Built-in Swagger UI accessible from the management dashboard for API testing and exploration
- 🌙 **Dark mode** — Toggle between light and dark themes; preference is saved per-device independently from the homeowner dashboard
- ❓ **In-app help** — Button opens a condensed help modal covering all management features on that page. For full documentation and setup guides, see this README

### Platform

- 🔀 **Dual-mode operation** — Same add-on works for homeowners and management companies
- 🛡️ **Scoped access** — Only irrigation zones and sensors are exposed — no access to lights, locks, cameras, or any other HA entities
- 🔐 **Management access control** — Generate a connection key that grants your management company full access to all devices (irrigation zones, moisture probes, weather, schedules, sensors); revoke access instantly with one click
- 📋 **Audit logging** — Every API action is logged with timestamp, API key, action, and details
- ⚡ **Rate limiting** — Configurable request limits to protect the homeowner's HA instance
- 🔄 **Entity auto-refresh** — Background task runs every 5 minutes to detect newly enabled or disabled entities in Home Assistant without requiring an add-on restart
- 🌱 **Moisture probe integration** — Gophr probes are added via a device picker (filtered for Gophr devices only); auto-detection maps percentage sensors to shallow/mid/deep depths and detects WiFi, battery, sleep duration, sleep control, and solar charging entities; gradient-based algorithm uses the **mid sensor (root zone — where grass roots live)** as the primary decision driver, shallow sensor for rain detection, and deep sensor for over-irrigation guard; per-zone moisture multipliers only affect zones with mapped probes (unmapped zones use weather-only); mid-run moisture monitoring checks every 30s and can shut off a zone early when saturation is detected; crash recovery restores base durations on add-on restart
- ⏰ **Probe-aware irrigation (Schedule Timeline)** — The system calculates when each zone will run based on schedule start times and zone durations, then automatically reprograms probe sleep duration so the probe wakes ~10 minutes before its mapped zone. On wake, if the soil is saturated the zone is skipped (disabled before it starts) and the system advances to the next zone. If not saturated, sleep is disabled to keep the probe awake for continuous mid-run monitoring. After the last mapped zone finishes, the original sleep duration is restored and any skipped zones are re-enabled. The timeline recalculates automatically when schedule start times, zone durations, zone enable states, or probe mappings change. Uses factored durations when "Apply Factors to Schedule" is active.
- 📋 **Configuration change log** — Every configuration change is logged with old → new values, who made the change, when, and what category; rolling 1000-entry buffer with CSV export; available on all dashboards
- ☀️ **Weather event logging** — All weather rule evaluations and actions are logged with CSV export and clearing from both dashboards
- 📄 **PDF system reports** — Server-side PDF generation using fpdf2 (pure Python, zero system dependencies); produces a professional, branded report with cover page, section headers, alternating-row tables, and page numbering; works on all architectures (amd64, aarch64, armv7)
- 🌙 **Dark mode** — All pages (homeowner dashboard, configuration, management dashboard) support dark mode with a 🌙/☀️ toggle; preferences are saved per-device in localStorage
- ❓ **In-app help** — Every page has a ❓ help button that opens a condensed, page-specific help modal. The in-app help covers only the features and controls on the current page, while this README serves as the full reference documentation with setup guides, integration details, and architecture information

---

## Weather-Based Irrigation Control

The add-on can automatically adjust irrigation based on weather conditions using your existing Home Assistant weather integration. No additional API keys or subscriptions are needed — it uses whatever `weather.*` entity you already have in HA.

### Supported Weather Integrations

Any Home Assistant weather integration that provides a `weather.*` entity will work. No separate API keys are configured in this add-on — you simply select the `weather.*` entity that your integration creates.

Below are the most common integrations and how to set them up:

#### National Weather Service (NWS) — Free, US Only (Recommended)

The NWS integration is free, provides the most accurate weather data for US locations, and the government does not charge for this service or issue API keys.

1. Go to **Settings → Devices & Services → + Add Integration**
2. Search for **National Weather Service (NWS)**
3. **API Key** — Type any value (e.g., `123456789`). The NWS does not issue or require real API keys.
4. **Latitude & Longitude** — Home Assistant will pre-fill these with your current location. If you are not at the same location as your irrigation controller, go to [latlong.net](https://www.latlong.net/convert-address-to-lat-long.html) and type in the controller's address to get the correct coordinates.
5. **METAR Station** — METAR is a weather station that reports local conditions. Home Assistant will pre-fill this with the closest station to your location. If you want to verify or change it, go to the [Turbli METAR Map](https://turbli.com/maps/world-metar-map/) and find the closest circle to your property — hover over it to see the **4-letter station code** (e.g., KMCO, KORL).
6. **Area** — Assign it to an area (e.g., "Outdoors").
7. Click **Submit** — a weather entity matching your METAR code will be created (e.g., `weather.kmco`)

> **Best for:** US-based users who want the most accurate, free, no-signup weather source.

#### OpenWeatherMap — Free Tier Available, Worldwide

OpenWeatherMap provides global coverage with a generous free tier (1,000 API calls/day).

1. Go to [openweathermap.org](https://openweathermap.org) and create a free account
2. Navigate to **My API Keys** in your account dashboard
3. Copy your **API key** (a new key may take a few hours to activate)
4. In Home Assistant, go to **Settings → Devices & Services → + Add Integration**
5. Search for **OpenWeatherMap**
6. Paste your API key, select your **mode** (free = `onecall_daily`), and confirm your location
7. Click **Submit** — a `weather.openweathermap` entity will be created

> **Best for:** Users outside the US, or anyone who wants global coverage with a free account.

#### Met.no — Free, No API Key, Worldwide

Met.no (Norwegian Meteorological Institute) is the default weather integration that comes pre-installed with many Home Assistant setups.

1. Go to **Settings → Devices & Services → + Add Integration**
2. Search for **Meteorologisk institutt (Met.no)**
3. Confirm your **location** and **elevation**
4. Click **Submit** — a `weather.forecast_home` (or similar) entity will be created

> **Best for:** Users who want a zero-configuration weather source. If you see a `weather.*` entity already in your HA, it may be Met.no.

#### Weather Underground — Personal Weather Station

Weather Underground provides hyper-local data from nearby personal weather stations.

1. Go to [wunderground.com](https://www.wunderground.com) and create a free account
2. If you have a personal weather station, register it to get an **API key**
3. Alternatively, apply for a free API key at the [Weather Underground API portal](https://www.wunderground.com/member/api-keys)
4. In Home Assistant, install the **Weather Underground** integration via HACS (Home Assistant Community Store), as this is a custom integration
5. Enter your API key and station ID during setup

> **Best for:** Users with a personal weather station who want the most accurate local data.

#### AccuWeather — Free Tier Available, Worldwide

1. Go to [developer.accuweather.com](https://developer.accuweather.com) and create a free account
2. Create an **app** in the developer portal to get an API key (free tier: 50 calls/day)
3. In Home Assistant, go to **Settings → Devices & Services → + Add Integration**
4. Search for **AccuWeather**
5. Paste your API key and confirm your location
6. Click **Submit**

> **Best for:** Users who prefer AccuWeather forecasts. Note the free tier has a low daily call limit.

#### Other Integrations

Any HA weather integration that creates a `weather.*` entity will work, including **Tomorrow.io**, **Pirate Weather**, **Environment Canada**, and others. Check the [Home Assistant Integrations directory](https://www.home-assistant.io/integrations/#weather) for a full list.

#### Verify Your Weather Entity

After installing any weather integration:

1. Go to **Settings → Devices & Services** and confirm your weather integration is loaded
2. Go to **Developer Tools → States** and search for `weather.` — you should see your entity with attributes like `temperature`, `humidity`, `wind_speed`, and `forecast`
3. In the Flux Open Home **Configuration** page, your entity will appear in the **Weather Entity** dropdown

### Weather Rules

The add-on evaluates 9 configurable rules on a regular interval (default: every 15 minutes):

| Rule | What It Does | Default |
|------|-------------|---------|
| **Rain Detection** | Pauses irrigation when it is currently raining. Auto-resumes after a configurable delay. | Enabled, 2-hour resume delay |
| **Rain Forecast** | Skips watering if rain probability exceeds a threshold in the forecast. | Enabled, 60% threshold |
| **Precipitation Threshold** | Skips watering if expected rainfall exceeds a threshold (mm). | Enabled, 6mm threshold |
| **Freeze Protection** | Skips watering when temperature is at or below freezing. | Enabled, 35°F / 2°C |
| **Cool Temperature** | Reduces watering percentage when temperature is cool. | Enabled, below 60°F, reduce 25% |
| **Hot Temperature** | Increases watering percentage during extreme heat. | Enabled, above 95°F, increase 25% |
| **Wind Speed** | Skips watering when wind is too high (water is wasted to wind drift). | Enabled, 20 mph / 32 km/h |
| **High Humidity** | Reduces watering when humidity is high (soil retains more moisture). | Enabled, above 80%, reduce 20% |
| **Seasonal Adjustment** | Monthly multiplier for watering duration (0 = off, 1 = normal, 1.2 = +20%). | Disabled by default |

**How rules interact:**
- **Pause/Skip rules** (rain, freeze, wind) take highest priority — if any triggers, irrigation stops immediately
- **Adjustment rules** (cool, hot, humidity, seasonal) stack multiplicatively into a single watering multiplier
- The watering multiplier is displayed on both the homeowner and management dashboards

**Weather pause vs. manual pause:**
- When weather triggers a pause, the system records it as a "weather pause"
- When conditions clear, the system **automatically resumes** only if the pause was weather-triggered
- Manual pauses (from the dashboard or API) are never auto-resumed by weather

### Weather Setup

1. Make sure you have a weather integration installed in Home Assistant (check **Settings → Devices & Services** for a `weather.*` entity)
2. On the **Configuration** page, scroll to the **Weather-Based Control** card
3. **Enable** the toggle
4. **Select your weather entity** from the dropdown (e.g., `weather.home`, `weather.forecast_home`)
5. Review and adjust the **weather rules** and thresholds to your preference
6. Set the **check interval** (how often the rules are evaluated, 5-60 minutes)
7. Click **Save Weather Settings**
8. Optionally click **Test Weather Rules Now** to see which rules would trigger with current conditions

The weather card will appear on the **Homeowner Dashboard** showing current conditions, forecast, watering multiplier, and any active weather adjustments. Management companies will also see this information in each customer's detail view.

---

## Connection Methods

### Nabu Casa (Recommended)

The easiest way to connect homeowners to management companies. Uses your existing Nabu Casa subscription — no port forwarding, no DNS setup, no firewall changes needed.

**Required one-time setup on the homeowner side:**

1. Add to `configuration.yaml`:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
2. Restart Home Assistant
3. Create a Long-Lived Access Token (see [Step 4](#step-4-create-a-long-lived-access-token-nabu-casa-only))

**How it works:** The add-on writes a proxy file to `/config/packages/` that creates `rest_command` services in HA. The management company's requests are routed through the HA REST API → `rest_command` → the add-on running on `localhost:8099`. All traffic goes through Nabu Casa's encrypted tunnel.

### Direct Connection

For users who have their own external access set up. The management company connects directly to the add-on's port (8099).

**Options include:**
- **Port forwarding** on your router + DuckDNS for dynamic DNS
- **Cloudflare Tunnel** pointed to `localhost:8099`
- **Tailscale / WireGuard** VPN between both HA instances

**Setup:** Make sure port 8099 is enabled in the add-on's **Network** configuration (Configuration tab in the add-on settings). Use the **Test URL** button on the Configuration page to verify connectivity.

---

## Configuration Reference

All settings can be managed through the add-on's web UI. The underlying options are stored in `/data/options.json`:

```yaml
# Operating mode
mode: "homeowner"                    # "homeowner" or "management"

# Homeowner identity (for connection key and management contact)
homeowner_url: ""                    # External URL (Nabu Casa or direct)
homeowner_label: ""                  # Property display name
homeowner_first_name: ""             # Homeowner first name
homeowner_last_name: ""              # Homeowner last name
homeowner_phone: ""                  # Homeowner phone number
homeowner_address: ""                # Street address
homeowner_city: ""                   # City
homeowner_state: ""                  # State
homeowner_zip: ""                    # ZIP code
homeowner_ha_token: ""               # HA Long-Lived Access Token (Nabu Casa only)
homeowner_connection_mode: "direct"  # "nabu_casa" or "direct"

# API keys (auto-managed, can also be created manually)
api_keys:
  - key: "auto-generated-key"
    name: "Management Company (Connection Key)"
    permissions:
      - zones.read
      - zones.control
      - schedule.read
      - schedule.write
      - sensors.read
      - entities.read
      - entities.control
      - history.read
      - system.control

# Device selection
irrigation_device_id: ""             # Set via admin panel device picker

# General settings
rate_limit_per_minute: 60            # API rate limit (1-300)
log_retention_days: 365              # Audit log retention (1-730)
enable_audit_log: true               # Enable/disable audit logging

# Connection state (managed automatically)
connection_revoked: false            # Set to true when homeowner revokes access

# Weather-based control
weather_entity_id: ""                # HA weather entity (e.g., "weather.home")
weather_enabled: false               # Enable weather-based control
weather_check_interval_minutes: 15   # Evaluation interval (5-60 minutes)
```

---

## API Endpoints

These are the external API endpoints that management companies connect to via connection keys. All authenticated endpoints require an `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" https://your-ha-instance:8099/api/zones
```

> **Note:** The homeowner and management dashboards use additional internal endpoints (under `/admin/api/`) for their UIs. These are not intended for external use and are accessible from the Swagger UI on the management dashboard.

### Zones
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/zones` | zones.read | List all zones with status |
| GET | `/api/zones/{zone_id}` | zones.read | Get a single zone's status |
| POST | `/api/zones/{zone_id}/start` | zones.control | Start a zone (optional `duration_minutes`) |
| POST | `/api/zones/{zone_id}/stop` | zones.control | Stop a zone |
| POST | `/api/zones/stop_all` | zones.control | Emergency stop all zones |

### Sensors
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/sensors` | sensors.read | All sensor readings + system health |
| GET | `/api/sensors/{sensor_id}` | sensors.read | Single sensor reading |

### Device Control Entities
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/entities` | entities.read | All device control entities |
| POST | `/api/entities/{entity_id}/set` | entities.control | Set an entity value |

> **Note:** Schedule configuration (day toggles, start times, zone enables, run durations) is managed through the Flux Open Home controller's ESPHome entities via the `/api/entities` endpoint.

### History
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/history/runs` | history.read | Zone run history (JSONL-based, includes weather conditions at run time) |
| GET | `/api/history/audit` | history.read | API audit log |

### System
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/system/health` | (none) | Health check (includes `revoked` flag) |
| GET | `/api/system/status` | zones.read | Full system overview |
| POST | `/api/system/pause` | system.control | Pause entire system |
| POST | `/api/system/resume` | system.control | Resume after pause |

---

## HA Events

The add-on fires custom events that your HA automations can listen for:

| Event | Description |
|-------|-------------|
| `flux_irrigation_system_paused` | System was paused (manual) |
| `flux_irrigation_system_resumed` | System was resumed (manual) |
| `flux_irrigation_weather_pause` | System was paused by weather rules |
| `flux_irrigation_weather_resume` | System was auto-resumed after weather cleared |

---

## Troubleshooting

### "No entities found on this device"

- Make sure your **Flux Open Home Irrigation Controller** is connected and online in Home Assistant
- Check **Settings → Devices & Services** and verify the controller shows entities
- If the controller just came online, restart the add-on — it retries entity resolution up to 3 times on startup

### Connection key doesn't work for management company

- **Nabu Casa:** Make sure you completed [Step 3](#step-3-one-time-configurationyaml-setup-nabu-casa-only) (configuration.yaml) and restarted HA
- **Nabu Casa:** Verify the Long-Lived Access Token is entered and valid — the add-on will reject key generation if the token is missing or truncated
- **Direct:** Verify port 8099 is enabled in the add-on's Network settings and is accessible externally
- Use the **Test URL** button on the Configuration page to diagnose connectivity

### Connection key stopped working after regeneration

- If you revoked access and then generated a new key but the management company still can't connect:
  - Make sure the management company is using the **new** connection key (not the old one)
  - On the management side, click **Update Key** on the property card and paste the new key
  - If the error mentions the HA token, re-enter your Long-Lived Access Token on the Configuration page and regenerate the connection key

### Management dashboard shows "Access Revoked" but homeowner didn't revoke

- This can happen if the management company's API key is stale (e.g., the homeowner regenerated a new connection key)
- Ask the homeowner for their latest connection key and use the **Update Key** button on the property card
- The "Access Revoked" status only appears when the homeowner has explicitly clicked "Revoke Access" — a stale key shows as "Offline" with a message to request the updated key

### Weather rules not triggering

- Make sure **Weather-Based Control** is enabled and a weather entity is selected
- Verify your weather entity is working: check **Settings → Devices & Services** for your weather integration
- Click **Test Weather Rules Now** on the Configuration page to see current conditions and which rules match
- Check the add-on logs for `[WEATHER]` messages

### Homeowner dashboard shows "Failed to load" after switching modes

- This is normal and temporary — the dashboard auto-refreshes every 30 seconds and will recover
- The homeowner API endpoints work regardless of which mode the UI is set to

### A zone was enabled in HA but isn't showing up

- The add-on runs an entity auto-refresh task every 5 minutes — newly enabled entities will appear automatically
- If you need them immediately, restart the add-on

### Map not showing on the homeowner dashboard

- Make sure the property address is filled in on the Configuration page
- The map uses OpenStreetMap geocoding, which requires an internet connection
- Try refreshing the page — geocoding results are cached after the first load

---

## License

MIT License — [Flux Open Home](https://www.fluxopenhome.com)
