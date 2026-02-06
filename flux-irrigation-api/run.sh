#!/usr/bin/with-contenv bashio
# ==============================================================================
# Flux Open Home - Irrigation Management API
# Starts the FastAPI server for irrigation management access
# ==============================================================================

bashio::log.info "Starting Flux Irrigation Management API..."

# Export environment variables for the app
export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"
export ADDON_OPTIONS="$(bashio::addon.options)"

# Start the FastAPI server
cd /app
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8099 --log-level info
