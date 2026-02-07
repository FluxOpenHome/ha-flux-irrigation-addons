# Flux Irrigation Management API

A Home Assistant add-on that provides dual-mode irrigation management for Flux Open Home. Homeowners expose a secure API for their irrigation system; management companies monitor and control multiple properties from a single dashboard.

## How It Works

This add-on runs in one of two modes:

### Homeowner Mode
The homeowner installs the add-on on their Home Assistant instance. They select their irrigation controller device, and the add-on exposes a secure REST API scoped only to irrigation entities. The homeowner generates a **connection key** and shares it with their management company.

### Management Company Mode
The management company installs the same add-on on their own Home Assistant instance and switches it to management mode. They paste connection keys from homeowners into their dashboard, which gives them a single interface to monitor and control all their customers' irrigation systems.

## Quick Start

### For Homeowners

1. Add this repository to your Home Assistant add-on store
2. Install the "Flux Irrigation Management API" add-on
3. Start the add-on and open the admin panel
4. Select your irrigation controller device from the dropdown
5. In the "Connection Key" section, enter your external API URL and click **Generate Connection Key**
6. Share the connection key with your management company

### For Management Companies

1. Install the same add-on on your Home Assistant instance
2. In the HA add-on Configuration tab, change **mode** to "management"
3. Restart the add-on and open the admin panel
4. Click **+ Add Property** and paste the connection key from a homeowner
5. The dashboard will show all connected properties with live status

## Features

- **Dual-mode operation** — Same add-on works for homeowners and management companies
- **Connection keys** — Simple base64 key encodes the API URL and credentials for easy sharing
- **Scoped access** — Only irrigation zones and sensors are exposed. No access to lights, locks, cameras, or any other HA entities.
- **API key authentication** — Each management company gets their own API key with configurable permissions.
- **Granular permissions** — Control what each API key can do: read zones, control zones, modify schedules, read sensors, view history.
- **Audit logging** — Every API action is logged with timestamp, API key, action, and details.
- **Rate limiting** — Configurable request limits to protect the homeowner's HA instance.
- **Management dashboard** — Grid view of all properties with live status, zone control, sensors, schedules, and run history.
- **Schedule management** — View and update irrigation schedules remotely.
- **Rain delay** — Set and cancel rain delays through the API.
- **System pause/resume** — Emergency pause that stops all zones and suspends schedules.
- **Interactive API docs** — Built-in Swagger UI at `/api/docs` for testing and exploration.

## Configuration

```yaml
mode: "homeowner"              # "homeowner" or "management"
homeowner_url: ""              # External URL where API is reachable (homeowner mode)
homeowner_label: ""            # Friendly property name for connection key
api_keys:
  - key: "your-secure-api-key"
    name: "ABC Irrigation Management"
    permissions:
      - zones.read
      - zones.control
      - entities.read
      - entities.write
      - sensors.read
      - history.read
      - system.control
irrigation_device_id: ""       # Set via admin panel device picker
rate_limit_per_minute: 60
log_retention_days: 30
enable_audit_log: true
```

### Device Selection (Homeowner Mode)

Open the admin panel and select your irrigation controller device from the dropdown. The add-on automatically finds all switch entities (zones) and sensor entities belonging to that device.

### Connection Key (Homeowner Mode)

The connection key encodes your external API URL and an auto-generated API key. Your management company pastes this into their dashboard to connect. You can revoke access at any time by deleting the auto-generated API key from the API Keys section.

**External URL**: The management company needs to reach your API over the internet. Options include:
- **Nabu Casa** with port forwarding
- **Cloudflare Tunnel**
- **DuckDNS** with a reverse proxy
- Any other method that makes port 8099 reachable

## API Endpoints (Homeowner Mode)

### Zones
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/zones` | zones.read | List all zones and their status |
| GET | `/api/zones/{zone_id}` | zones.read | Get a single zone's status |
| POST | `/api/zones/{zone_id}/start` | zones.control | Start a zone (optional duration) |
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
| GET | `/api/entities` | entities.read | All device control entities (schedule, switches, numbers, etc.) |
| POST | `/api/entities/{entity_id}/set` | entities.write | Set an entity value |

> **Note:** Schedule configuration (day toggles, start times, zone enables, run durations) is managed
> through the device's ESPHome entities via the `/api/entities` endpoint. The management dashboard
> provides a dedicated Schedule UI that classifies and displays these entities with purpose-built controls.

### History
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/history/runs` | history.read | Zone run history (filterable) |
| GET | `/api/history/audit` | history.read | API audit log |

### System
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/system/health` | (none) | Health check |
| GET | `/api/system/status` | zones.read | Full system overview |
| POST | `/api/system/pause` | system.control | Pause entire system |
| POST | `/api/system/resume` | system.control | Resume after pause |

## Authentication

All endpoints (except `/api/system/health`) require an `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" https://your-ha-instance:8099/api/zones
```

## HA Events

The add-on fires custom events that your HA automations can listen for:

- `flux_irrigation_timed_run` — A zone was started with a duration
- `flux_irrigation_schedule_updated` — Schedule was modified via API
- `flux_irrigation_rain_delay` — Rain delay was set
- `flux_irrigation_rain_delay_cancelled` — Rain delay was cancelled
- `flux_irrigation_system_paused` — System was paused
- `flux_irrigation_system_resumed` — System was resumed

Example automation to handle timed runs:

```yaml
automation:
  - alias: "Handle API timed irrigation run"
    trigger:
      - platform: event
        event_type: flux_irrigation_timed_run
    action:
      - delay:
          minutes: "{{ trigger.event.data.duration_minutes }}"
      - service: switch.turn_off
        target:
          entity_id: "{{ trigger.event.data.entity_id }}"
```

## License

MIT License — Flux Open Home
