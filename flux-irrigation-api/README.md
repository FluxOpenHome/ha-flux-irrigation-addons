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
2. Select your **Flux Open Home Irrigation Controller** from the dropdown
3. The add-on will automatically discover all zones (switches/valves) and sensors belonging to that device

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

> **Tip:** You can send the connection key via the **Email** button or display it as a **QR code** for easy scanning.

### Step 6: Set Up Weather-Based Control (Optional)

See [Weather-Based Irrigation Control](#weather-based-irrigation-control) below for full details. Quick setup:

1. Install a weather integration in Home Assistant if you don't have one already (e.g., **National Weather Service**, **Weather Underground**, **OpenWeatherMap**)
2. On the Configuration page, scroll to **Weather-Based Control**
3. Enable the toggle and select your `weather.*` entity from the dropdown
4. Configure the weather rules to your preference
5. Click **Save Weather Settings**

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
4. On the management side, they should remove the old property and add the new connection key

---

## Management Company Setup

1. Install the same add-on on your Home Assistant instance (see [Installation](#installation))
2. Open the add-on panel and click **Switch to Management** (or go to the add-on's Configuration tab and set **mode** to `management`, then restart)
3. Click **+ Add Property**
4. Paste the **connection key** provided by a homeowner
5. The property will appear in the dashboard with live status, zone control, sensors, schedules, and weather conditions

The management dashboard automatically checks connectivity to all properties every 5 minutes and shows online/offline status.

---

## Features

- **Homeowner Dashboard** — Full local control with zone start/stop (timed or manual), sensor monitoring, schedule management, run history, and weather conditions
- **Management Dashboard** — Multi-property grid view with click-to-expand detail cards for each property
- **Weather-Based Control** — 9 configurable weather rules that automatically pause, reduce, or increase irrigation based on real-time conditions and forecasts
- **Dual-mode operation** — Same add-on works for homeowners and management companies
- **Connection keys** — Simple encoded key shares the API URL and credentials for easy setup (send via copy, email, or QR code)
- **Revoke access** — Homeowners can instantly revoke management company access with one click, with a confirmation dialog to prevent accidents
- **Live contact sync** — Homeowner name, phone, and address are synced to the management dashboard automatically on every health check, even if added after the connection key was generated
- **Scoped access** — Only irrigation zones and sensors are exposed — no access to lights, locks, cameras, or any other HA entities
- **API key authentication** — Each management company gets their own API key with configurable permissions
- **Granular permissions** — Control what each API key can do: read zones, control zones, modify schedules, read sensors, view history
- **Audit logging** — Every API action is logged with timestamp, API key, action, and details
- **Rate limiting** — Configurable request limits to protect the homeowner's HA instance
- **Schedule management** — View and update irrigation schedules remotely (entity-based, driven by the Flux Open Home controller's ESPHome configuration)
- **System pause/resume** — Emergency pause that stops all active zones and suspends schedules
- **Zone aliases** — Give zones friendly display names on both homeowner and management dashboards
- **Location map** — Leaflet map on the dashboard shows property location
- **Interactive API docs** — Built-in Swagger UI at `/api/docs` for testing and exploration

---

## Weather-Based Irrigation Control

The add-on can automatically adjust irrigation based on weather conditions using your existing Home Assistant weather integration. No additional API keys or subscriptions are needed — it uses whatever `weather.*` entity you already have in HA.

### Supported Weather Integrations

Any Home Assistant weather integration that provides a `weather.*` entity will work. No separate API keys are configured in this add-on — you simply select the `weather.*` entity that your integration creates.

Below are the most common integrations and how to set them up:

#### National Weather Service (NWS) — Free, US Only

The NWS integration is free, requires no API key, and provides excellent forecast data for US locations.

1. Go to **Settings → Devices & Services → + Add Integration**
2. Search for **National Weather Service (NWS)**
3. Enter your **latitude and longitude** (pre-filled from your HA config)
4. Enter a **station ID** (optional — HA will find the nearest one automatically)
5. Click **Submit** — a `weather.home` (or similar) entity will be created

> **Best for:** US-based users who want a reliable, free, no-signup weather source.

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
log_retention_days: 30               # Audit log retention (1-365)
enable_audit_log: true               # Enable/disable audit logging

# Weather-based control
weather_entity_id: ""                # HA weather entity (e.g., "weather.home")
weather_enabled: false               # Enable weather-based control
weather_check_interval_minutes: 15   # Evaluation interval (5-60 minutes)
```

---

## API Endpoints

All authenticated endpoints require an `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" https://your-ha-instance:8099/api/zones
```

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
| GET | `/api/history/runs` | history.read | Zone run history |
| GET | `/api/history/audit` | history.read | API audit log |

### System
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/system/health` | (none) | Health check |
| GET | `/api/system/status` | zones.read | Full system overview |
| POST | `/api/system/pause` | system.control | Pause entire system |
| POST | `/api/system/resume` | system.control | Resume after pause |

---

## HA Events

The add-on fires custom events that your HA automations can listen for:

| Event | Description |
|-------|-------------|
| `flux_irrigation_timed_run` | A zone was started with a duration |
| `flux_irrigation_schedule_updated` | Schedule was modified via API |
| `flux_irrigation_rain_delay` | Rain delay was set |
| `flux_irrigation_rain_delay_cancelled` | Rain delay was cancelled |
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
- **Nabu Casa:** Verify the Long-Lived Access Token is entered and valid
- **Direct:** Verify port 8099 is enabled in the add-on's Network settings and is accessible externally
- Use the **Test URL** button on the Configuration page to diagnose connectivity

### Weather rules not triggering

- Make sure **Weather-Based Control** is enabled and a weather entity is selected
- Verify your weather entity is working: check **Settings → Devices & Services** for your weather integration
- Click **Test Weather Rules Now** on the Configuration page to see current conditions and which rules match
- Check the add-on logs for `[WEATHER]` messages

### Homeowner dashboard shows "Failed to load" after switching modes

- This is normal and temporary — the dashboard auto-refreshes every 30 seconds and will recover
- The homeowner API endpoints work regardless of which mode the UI is set to

### Map not showing on the homeowner dashboard

- Make sure the property address is filled in on the Configuration page
- The map uses OpenStreetMap geocoding, which requires an internet connection
- Try refreshing the page — geocoding results are cached after the first load

---

## License

MIT License — [Flux Open Home](https://www.fluxopenhome.com)
