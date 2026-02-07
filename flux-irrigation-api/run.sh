#!/usr/bin/with-contenv bashio
# ==============================================================================
# Flux Open Home Irrigation Control
# Starts the FastAPI server for irrigation management access
# ==============================================================================

echo "[INFO] Starting Flux Open Home Irrigation Control..."
echo "[INFO] SUPERVISOR_TOKEN is available (${#SUPERVISOR_TOKEN} chars)"

# Load add-on options from the standard HA path
if [ -f /data/options.json ]; then
    export ADDON_OPTIONS="$(cat /data/options.json)"
    echo "[INFO] Loaded options from /data/options.json"
else
    export ADDON_OPTIONS="{}"
    echo "[WARN] No /data/options.json found, using defaults"
fi

# Start the FastAPI server
cd /app
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8099 --log-level info
