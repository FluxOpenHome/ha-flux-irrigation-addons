"""
Authentication and authorization for the Irrigation Management API.
Validates API keys and checks permissions.
"""

import secrets
from typing import Optional
from fastapi import HTTPException, Security, Request
from fastapi.security import APIKeyHeader
from config import get_config, ApiKeyConfig


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# All available permissions
VALID_PERMISSIONS = {
    "zones.read",       # View zone status
    "zones.control",    # Start/stop zones
    "schedule.read",    # View schedules
    "schedule.write",   # Modify schedules
    "sensors.read",     # Read sensor data
    "entities.read",    # View device control entities (numbers, selects, switches, etc.)
    "entities.control", # Set values on device control entities
    "history.read",     # View run history
    "system.control",   # Pause/resume system, rain delay
}


def _find_api_key(key: str) -> Optional[ApiKeyConfig]:
    """Look up an API key in the configuration."""
    config = get_config()
    for api_key in config.api_keys:
        # Use constant-time comparison to prevent timing attacks
        if secrets.compare_digest(api_key.key, key):
            return api_key
    return None


async def authenticate(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
) -> ApiKeyConfig:
    """
    Validate the API key from the request header.
    Returns the ApiKeyConfig if valid, raises 401/403 otherwise.
    """
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header.",
        )

    key_config = _find_api_key(api_key)
    if key_config is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )

    # Store the key config on the request for downstream use
    request.state.api_key_config = key_config
    return key_config


def require_permission(permission: str):
    """
    Dependency factory that checks if the authenticated API key
    has a specific permission.

    Usage:
        @router.get("/zones", dependencies=[Depends(require_permission("zones.read"))])
    """
    async def _check_permission(
        request: Request,
        key_config: ApiKeyConfig = Security(authenticate),
    ) -> ApiKeyConfig:
        if permission not in key_config.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"API key '{key_config.name}' does not have '{permission}' permission.",
            )
        return key_config

    return _check_permission


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)
