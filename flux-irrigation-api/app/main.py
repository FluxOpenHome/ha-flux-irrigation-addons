"""
Flux Open Home - Irrigation Management API
============================================
A Home Assistant add-on that exposes a secure, scoped API for
irrigation management companies to monitor and control Flux Open Home
irrigation systems without accessing any other HA entities.

Author: Brandon / Flux Open Home
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import get_config, async_initialize
from audit_log import cleanup_old_logs
from routes import zones, sensors, schedule, history, system, admin


# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address)


# --- Periodic Tasks ---
async def _periodic_log_cleanup():
    """Run audit log cleanup once per day."""
    while True:
        try:
            cleanup_old_logs()
        except Exception as e:
            print(f"[MAIN] Log cleanup error: {e}")
        await asyncio.sleep(86400)  # 24 hours


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    config = await async_initialize()
    print(f"[MAIN] Flux Irrigation API starting...")
    print(f"[MAIN] Configured API keys: {len(config.api_keys)}")
    print(f"[MAIN] Irrigation device: {config.irrigation_device_id or '(not configured)'}")
    print(f"[MAIN] Resolved zones: {len(config.allowed_zone_entities)}")
    print(f"[MAIN] Resolved sensors: {len(config.allowed_sensor_entities)}")
    print(f"[MAIN] Rate limit: {config.rate_limit_per_minute}/min")
    print(f"[MAIN] Audit logging: {'enabled' if config.enable_audit_log else 'disabled'}")

    # Start background tasks
    cleanup_task = asyncio.create_task(_periodic_log_cleanup())

    yield

    # Shutdown
    cleanup_task.cancel()
    print("[MAIN] Flux Irrigation API shutting down.")


# --- FastAPI App ---
app = FastAPI(
    title="Flux Irrigation Management API",
    description=(
        "Secure API for irrigation management companies to monitor and control "
        "Flux Open Home irrigation systems through Home Assistant. "
        "Only irrigation-related entities are exposed."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# --- Middleware ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten this in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting based on configuration."""
    config = get_config()
    # Rate limiting is handled by slowapi decorators on routes
    response = await call_next(request)
    return response


# --- Routes ---
app.include_router(zones.router, prefix="/api")
app.include_router(sensors.router, prefix="/api")
app.include_router(schedule.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(admin.router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "Flux Irrigation Management API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/system/health",
    }


@app.get("/api", include_in_schema=False)
async def api_root():
    return {
        "endpoints": {
            "zones": "/api/zones",
            "sensors": "/api/sensors",
            "schedule": "/api/schedule",
            "history": "/api/history/runs",
            "audit_log": "/api/history/audit",
            "system_status": "/api/system/status",
            "health": "/api/system/health",
            "docs": "/api/docs",
        }
    }
