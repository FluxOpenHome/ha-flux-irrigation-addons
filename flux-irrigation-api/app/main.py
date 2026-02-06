"""
Flux Open Home - Irrigation Management API
============================================
A Home Assistant add-on that supports two modes:
- Homeowner: Exposes a secure, scoped API for irrigation management
- Management: Dashboard to monitor and control multiple homeowner systems

Author: Brandon / Flux Open Home
"""

import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import get_config, async_initialize
from audit_log import cleanup_old_logs
from routes import zones, sensors, schedule, history, system, admin, management


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


async def _periodic_customer_health_check():
    """Periodically check connectivity to all customers (management mode only)."""
    while True:
        try:
            config = get_config()
            if config.mode == "management":
                from customer_store import load_customers, update_customer_status
                from management_client import check_homeowner_connection
                from connection_key import ConnectionKeyData

                customers = load_customers()
                for customer in customers:
                    try:
                        conn = ConnectionKeyData(url=customer.url, key=customer.api_key)
                        result = await check_homeowner_connection(conn)
                        update_customer_status(customer.id, result)
                    except Exception as e:
                        print(f"[MAIN] Health check failed for {customer.name}: {e}")
        except Exception as e:
            print(f"[MAIN] Customer health check error: {e}")
        await asyncio.sleep(300)  # Every 5 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    config = await async_initialize()
    print(f"[MAIN] Flux Irrigation API starting in {config.mode.upper()} mode...")

    if config.mode == "homeowner":
        print(f"[MAIN] Configured API keys: {len(config.api_keys)}")
        print(f"[MAIN] Irrigation device: {config.irrigation_device_id or '(not configured)'}")
        print(f"[MAIN] Resolved zones: {len(config.allowed_zone_entities)}")
        print(f"[MAIN] Resolved sensors: {len(config.allowed_sensor_entities)}")
        print(f"[MAIN] Rate limit: {config.rate_limit_per_minute}/min")
        print(f"[MAIN] Audit logging: {'enabled' if config.enable_audit_log else 'disabled'}")
        if config.homeowner_url:
            print(f"[MAIN] External URL: {config.homeowner_url}")
    else:
        from customer_store import load_customers
        customers = load_customers()
        print(f"[MAIN] Management mode: {len(customers)} customer(s) configured")

    # Start background tasks
    cleanup_task = asyncio.create_task(_periodic_log_cleanup())
    health_task = None
    if config.mode == "management":
        health_task = asyncio.create_task(_periodic_customer_health_check())

    yield

    # Shutdown
    cleanup_task.cancel()
    if health_task:
        health_task.cancel()
    print("[MAIN] Flux Irrigation API shutting down.")


# --- FastAPI App ---
app = FastAPI(
    title="Flux Irrigation Management API",
    description=(
        "Dual-mode irrigation management for Flux Open Home. "
        "Homeowners expose a secure API; management companies monitor "
        "and control multiple properties from a single dashboard."
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
async def mode_guard_middleware(request: Request, call_next):
    """Block local irrigation API routes in management mode."""
    config = get_config()
    if config.mode == "management":
        path = request.url.path
        # Block homeowner-only API routes in management mode
        if (
            path.startswith("/api/")
            and not path.startswith("/api/docs")
            and not path.startswith("/api/redoc")
            and not path.startswith("/api/openapi")
        ):
            return Response(
                content=json.dumps({
                    "detail": "This instance is running in management mode. "
                    "Local irrigation API is not available."
                }),
                status_code=404,
                media_type="application/json",
            )
    response = await call_next(request)
    return response


# --- Routes ---
app.include_router(zones.router, prefix="/api")
app.include_router(sensors.router, prefix="/api")
app.include_router(schedule.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(admin.router)
app.include_router(management.router)


@app.get("/", include_in_schema=False)
async def root(request: Request):
    """Redirect root to admin UI, preserving ingress path prefix."""
    # Use a relative redirect so HA ingress path is preserved
    return RedirectResponse(url="admin", status_code=302)


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
