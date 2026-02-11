# Flux Open Home — Home Assistant Add-ons

Custom Home Assistant add-on repository for [Flux Open Home](https://www.fluxopenhome.com) products.

> **This add-on is designed exclusively for the Flux Open Home Irrigation Controller.** Purchase yours at [www.fluxopenhome.com](https://www.fluxopenhome.com).

## Add-ons

### Flux Irrigation Control API

A secure REST API and homeowner dashboard for your Flux Open Home irrigation system. Provides full local control of zones, schedules, weather-based smart irrigation, Gophr moisture probe integration, rain sensor management, pump monitoring, expansion board support, PDF system reports, and more — all without exposing your Home Assistant to the internet.

**For irrigation management companies:** The companion [Flux Management Server](https://github.com/FluxOpenHome/flux-management-server) provides a cloud-based multi-property dashboard that connects to homeowner add-ons via connection keys.

## Installation

1. Open Home Assistant
2. Go to **Settings → Add-ons → Add-on Store**
3. Click the **⋮** (three dots) menu in the top right
4. Click **Repositories**
5. Paste this URL: `https://github.com/FluxOpenHome/ha-flux-irrigation-addons`
6. Click **Add → Close**
7. The Flux Irrigation Control API will appear in the add-on store

## Requirements

- Home Assistant 2024.1 or newer
- A **Flux Open Home Irrigation Controller** connected to your Home Assistant ([purchase here](https://www.fluxopenhome.com))
- For remote management: a Nabu Casa subscription (recommended) or other external access method

## Documentation

See the [add-on README](flux-irrigation-api/README.md) for full setup instructions, configuration options, weather control setup, moisture probes, and API documentation.

## License

MIT License — [Flux Open Home](https://www.fluxopenhome.com)
