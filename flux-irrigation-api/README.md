# Flux Irrigation Management API

A Home Assistant add-on that provides a secure, scoped REST API for irrigation management companies to monitor and control Flux Open Home irrigation systems — without accessing any other devices or entities in the homeowner's Home Assistant instance.

## Overview

This add-on acts as a middleware layer between an irrigation management company and the homeowner's Home Assistant. The management company authenticates with API keys and can only interact with irrigation-related entities. All actions are logged in an audit trail visible to the homeowner.

## Features

- **Scoped access** — Only irrigation zones and sensors are exposed. No access to lights, locks, cameras, or any other HA entities.
- **API key authentication** — Each management company gets their own API key with configurable permissions.
- **Granular permissions** — Control what each API key can do: read zones, control zones, modify schedules, read sensors, view history.
- **Audit logging** — Every API action is logged with timestamp, API key, action, and details.
- **Rate limiting** — Configurable request limits to protect the homeowner's HA instance.
- **Schedule management** — Management companies can view and update irrigation schedules.
- **Rain delay** — Set and cancel rain delays through the API.
- **System pause/resume** — Emergency pause that stops all zones and suspends schedules.
- **Interactive API docs** — Built-in Swagger UI at `/api/docs` for testing and exploration.

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "Flux Irrigation Management API" add-on
3. Start the add-on
4. Open the admin panel and select your irrigation controller device
5. Configure API keys for your management company

## Configuration

```yaml
api_keys:
  - key: "your-secure-api-key-here"     # Generate a strong key
    name: "ABC Irrigation Management"    # Friendly name for audit logs
    permissions:
      - zones.read        # View zone status
      - zones.control     # Start/stop zones
      - schedule.read     # View schedules
      - schedule.write    # Modify schedules
      - sensors.read      # Read sensor data
      - history.read      # View run history
      - system.control    # Pause/resume, rain delay

irrigation_device_id: ""    # Set via admin panel device picker
rate_limit_per_minute: 60
log_retention_days: 30
enable_audit_log: true
```

### Device Selection

The add-on discovers irrigation entities by device. Open the admin panel (Irrigation API in the sidebar) and select your irrigation controller device from the dropdown. The add-on will automatically find all switch entities (zones) and sensor entities belonging to that device.

## API Endpoints

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

### Schedule
| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/api/schedule` | schedule.read | Get current schedule programs |
| PUT | `/api/schedule` | schedule.write | Replace all schedule programs |
| POST | `/api/schedule/program` | schedule.write | Add a new program |
| DELETE | `/api/schedule/program/{id}` | schedule.write | Delete a program |
| POST | `/api/schedule/rain_delay` | system.control | Set rain delay (hours) |
| DELETE | `/api/schedule/rain_delay` | system.control | Cancel rain delay |

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
curl -H "X-API-Key: your-api-key" https://your-ha-instance/api/zones
```

## Remote Access

The management company needs to reach the add-on over the internet. Recommended options:

1. **Nabu Casa** — Easiest. Handles SSL and remote access automatically.
2. **Cloudflare Tunnel** — Free, secure tunnel to your HA instance.
3. **Reverse proxy (Nginx/Caddy)** — Full control, requires port forwarding and SSL setup.

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
