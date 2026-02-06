"""
History endpoints.
View irrigation run history, water usage, and activity logs.
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional
from auth import require_permission, ApiKeyConfig
from config import get_config
import ha_client
import audit_log


router = APIRouter(prefix="/history", tags=["History"])


class ZoneRunEvent(BaseModel):
    entity_id: str
    zone_name: str
    state: str
    timestamp: str
    duration_seconds: Optional[float] = None


class HistoryResponse(BaseModel):
    zone_id: Optional[str] = None
    period_start: str
    period_end: str
    events: list[ZoneRunEvent]
    total_run_events: int


class AuditLogEntry(BaseModel):
    timestamp: str
    api_key_name: str
    action: str
    method: str
    path: str
    details: dict = {}
    status_code: int = 200


def _zone_name(entity_id: str) -> str:
    """Derive zone name from entity_id by stripping the 'switch.' domain."""
    return entity_id.removeprefix("switch.")


@router.get(
    "/runs",
    response_model=HistoryResponse,
    dependencies=[Depends(require_permission("history.read"))],
    summary="Get irrigation run history",
)
async def get_run_history(
    request: Request,
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    hours: int = Query(24, ge=1, le=720, description="Hours of history to retrieve"),
):
    """Get the irrigation run history for all zones or a specific zone."""
    config = get_config()
    key_config: ApiKeyConfig = request.state.api_key_config

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    events = []

    if zone_id:
        # Single zone history
        entity_id = f"switch.{zone_id}"
        if entity_id not in config.allowed_zone_entities:
            raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found.")

        history = await ha_client.get_history(
            entity_id=entity_id,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
        )

        if history and len(history) > 0:
            prev_event = None
            for entry in history[0]:
                event = ZoneRunEvent(
                    entity_id=entity_id,
                    zone_name=zone_id,
                    state=entry.get("state", "unknown"),
                    timestamp=entry.get("last_changed", ""),
                )

                # Calculate duration for "on" periods
                if prev_event and prev_event.state == "on" and event.state == "off":
                    try:
                        on_time = datetime.fromisoformat(prev_event.timestamp)
                        off_time = datetime.fromisoformat(event.timestamp)
                        event.duration_seconds = (off_time - on_time).total_seconds()
                    except ValueError:
                        pass

                events.append(event)
                prev_event = event
    else:
        # All zones history
        zone_entities = await ha_client.get_entities_by_ids(
            config.allowed_zone_entities
        )

        for entity in zone_entities:
            entity_id = entity["entity_id"]
            zone_name = _zone_name(entity_id)

            history = await ha_client.get_history(
                entity_id=entity_id,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
            )

            if history and len(history) > 0:
                prev_event = None
                for entry in history[0]:
                    event = ZoneRunEvent(
                        entity_id=entity_id,
                        zone_name=zone_name,
                        state=entry.get("state", "unknown"),
                        timestamp=entry.get("last_changed", ""),
                    )

                    if prev_event and prev_event.state == "on" and event.state == "off":
                        try:
                            on_time = datetime.fromisoformat(prev_event.timestamp)
                            off_time = datetime.fromisoformat(event.timestamp)
                            event.duration_seconds = (off_time - on_time).total_seconds()
                        except ValueError:
                            pass

                    events.append(event)
                    prev_event = event

    # Sort all events by timestamp
    events.sort(key=lambda e: e.timestamp, reverse=True)

    audit_log.log_action(
        api_key_name=key_config.name,
        method="GET",
        path="/api/history/runs",
        action="get_run_history",
        details={"zone_id": zone_id, "hours": hours, "event_count": len(events)},
        client_ip=request.client.host if request.client else None,
    )

    return HistoryResponse(
        zone_id=zone_id,
        period_start=start_time.isoformat(),
        period_end=end_time.isoformat(),
        events=events,
        total_run_events=len([e for e in events if e.state == "on"]),
    )


@router.get(
    "/audit",
    response_model=list[AuditLogEntry],
    dependencies=[Depends(require_permission("history.read"))],
    summary="Get API audit log",
)
async def get_audit_log(
    request: Request,
    limit: int = Query(50, ge=1, le=500, description="Number of entries to return"),
):
    """Get the audit log of all API actions taken by management companies."""
    key_config: ApiKeyConfig = request.state.api_key_config

    logs = audit_log.get_recent_logs(limit=limit)

    entries = [
        AuditLogEntry(
            timestamp=log.get("timestamp", ""),
            api_key_name=log.get("api_key_name", ""),
            action=log.get("action", ""),
            method=log.get("method", ""),
            path=log.get("path", ""),
            details=log.get("details", {}),
            status_code=log.get("status_code", 200),
        )
        for log in logs
    ]

    return entries
