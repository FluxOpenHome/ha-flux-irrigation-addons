#!/bin/bash
# ==============================================================================
# Flux Open Home - Irrigation Management API
# Starts the FastAPI server for irrigation management access
# ==============================================================================

echo "[INFO] Starting Flux Irrigation Management API..."

# Export environment variables for the app
# SUPERVISOR_TOKEN is set by the HA Supervisor automatically
export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"

# Load add-on options from the standard HA path
if [ -f /data/options.json ]; then
    export ADDON_OPTIONS="$(cat /data/options.json)"
else
    export ADDON_OPTIONS="{}"
fi

# Start the FastAPI server
cd /app
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8099 --log-level info
