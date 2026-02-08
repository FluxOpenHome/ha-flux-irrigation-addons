"""
Flux Open Home - Issue Reporting API
======================================
Allows homeowners to report issues to their management company.
Issues are stored locally on the homeowner device and accessed
by management through the proxy architecture.
"""

from datetime import datetime, timedelta
from typing import Optional
import secrets
import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from icalendar import Calendar, Event

from config import get_config
from config_changelog import log_change, get_actor
import issue_store


router = APIRouter(prefix="/admin/api/homeowner/issues", tags=["Issues"])


# --- Request Models ---

class CreateIssueRequest(BaseModel):
    severity: str = Field(..., description="Issue severity: clarification, annoyance, or severe")
    description: str = Field(..., min_length=1, max_length=1000, description="Issue description")


class AcknowledgeIssueRequest(BaseModel):
    note: Optional[str] = Field(None, max_length=500, description="Management note")
    service_date: Optional[str] = Field(None, description="Scheduled service date (YYYY-MM-DD)")


# --- Endpoints ---

@router.post("/", summary="Report a new issue")
async def create_issue(body: CreateIssueRequest, request: Request):
    """Homeowner reports a new issue to management."""
    if body.severity not in issue_store.VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail=f"Invalid severity. Must be one of: {', '.join(issue_store.VALID_SEVERITIES)}")
    try:
        issue = issue_store.create_issue(body.severity, body.description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    severity_labels = {"clarification": "Clarification", "annoyance": "Annoyance", "severe": "Severe Issue"}
    log_change(get_actor(request), "Issues",
               f"Reported {severity_labels.get(body.severity, body.severity)}: {body.description[:100]}")
    return {"issue": issue}


@router.get("/", summary="List all issues")
async def list_issues():
    """Return all issues, newest first."""
    issues = issue_store.get_all_issues()
    return {"issues": issues, "total": len(issues)}


@router.get("/active", summary="List active issues")
async def list_active_issues():
    """Return issues that are not resolved, newest first."""
    issues = issue_store.get_active_issues()
    return {"issues": issues, "total": len(issues)}


@router.get("/visible", summary="List visible issues for homeowner")
async def list_visible_issues():
    """Return issues visible to the homeowner: active + resolved-but-not-dismissed."""
    issues = issue_store.get_visible_issues()
    return {"issues": issues, "total": len(issues)}


@router.get("/summary", summary="Issue summary for health check")
async def issue_summary():
    """Lightweight summary of active issues, used by management health check polling."""
    return issue_store.get_issue_summary()


@router.get("/{issue_id}/calendar.ics", summary="Download calendar event for scheduled service")
async def issue_calendar_ics(issue_id: str):
    """Generate an RFC 5545 compliant .ics calendar file for a scheduled service date.

    Uses the icalendar library to produce a standards-compliant file that
    calendar applications (Apple Calendar, Google Calendar, Outlook, etc.)
    can natively import.
    """
    issue = issue_store.get_issue(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    if not issue.get("service_date"):
        raise HTTPException(status_code=404, detail="No service date scheduled for this issue")

    svc_date = issue["service_date"]  # YYYY-MM-DD
    dt_start = datetime.strptime(svc_date, "%Y-%m-%d").date()
    dt_end = dt_start + timedelta(days=1)

    # Build location from config address
    config = get_config()
    addr_parts = []
    if config.homeowner_address:
        addr_parts.append(config.homeowner_address)
    city_state = []
    if config.homeowner_city:
        city_state.append(config.homeowner_city)
    if config.homeowner_state:
        city_state.append(config.homeowner_state)
    if city_state:
        line = ", ".join(city_state)
        if config.homeowner_zip:
            line += " " + config.homeowner_zip
        addr_parts.append(line)
    location = ", ".join(addr_parts)

    title = "Irrigation Service"
    if config.homeowner_label:
        title += f" - {config.homeowner_label}"

    description = "Irrigation service visit scheduled by your management company."
    if issue.get("management_note"):
        note_clean = issue["management_note"].replace("\n", " ").replace("\r", " ")
        description += f"\nNote from management: {note_clean}"

    # Build RFC 5545 compliant calendar using icalendar library
    cal = Calendar()
    cal.add("prodid", "-//Flux Open Home//Irrigation Service//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")

    event = Event()
    event.add("uid", f"flux-svc-{issue['id']}@flux-irrigation")
    event.add("dtstamp", datetime.utcnow())
    event.add("dtstart", dt_start)
    event.add("dtend", dt_end)
    event.add("summary", title)
    event.add("description", description)
    if location:
        event.add("location", location)
    event.add("status", "CONFIRMED")
    event.add("transp", "TRANSPARENT")

    cal.add_component(event)
    ics_content = cal.to_ical()

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=irrigation-service-{svc_date}.ics",
        },
    )


# --- Temporary calendar tokens (for direct .ics access bypassing ingress auth) ---
_cal_tokens: dict[str, dict] = {}  # token -> {"issue_id": str, "expires": float}
_CAL_TOKEN_TTL = 300  # 5 minutes


def _cleanup_expired_tokens():
    """Remove expired tokens."""
    now = time.time()
    expired = [t for t, v in _cal_tokens.items() if now > v["expires"]]
    for t in expired:
        _cal_tokens.pop(t, None)


@router.post("/{issue_id}/calendar-token", summary="Generate a temporary calendar download token")
async def create_calendar_token(issue_id: str):
    """Generate a short-lived token that allows the .ics file to be downloaded
    without HA ingress authentication. Used by iOS to open the .ics in Safari
    so that Apple Calendar can handle it natively."""
    issue = issue_store.get_issue(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    if not issue.get("service_date"):
        raise HTTPException(status_code=404, detail="No service date scheduled")

    _cleanup_expired_tokens()
    token = secrets.token_urlsafe(32)
    _cal_tokens[token] = {"issue_id": issue_id, "expires": time.time() + _CAL_TOKEN_TTL}
    return {"token": token}


def get_cal_token_issue_id(token: str) -> str | None:
    """Look up and consume a calendar token. Returns the issue_id or None."""
    _cleanup_expired_tokens()
    entry = _cal_tokens.pop(token, None)
    if entry is None:
        return None
    if time.time() > entry["expires"]:
        return None
    return entry["issue_id"]


@router.put("/{issue_id}/acknowledge", summary="Acknowledge an issue")
async def acknowledge_issue(issue_id: str, body: AcknowledgeIssueRequest, request: Request):
    """Management acknowledges an issue, optionally scheduling a service date."""
    issue = issue_store.acknowledge_issue(issue_id, body.note, body.service_date)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found or already resolved")

    desc = f"Acknowledged issue ({issue['severity']})"
    if body.service_date:
        desc += f", service scheduled for {body.service_date}"
    if body.note:
        desc += f": {body.note[:100]}"
    log_change(get_actor(request), "Issues", desc)
    return {"issue": issue}


@router.put("/{issue_id}/resolve", summary="Resolve an issue")
async def resolve_issue(issue_id: str, request: Request):
    """Management marks an issue as resolved."""
    issue = issue_store.resolve_issue(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    log_change(get_actor(request), "Issues",
               f"Resolved issue ({issue['severity']}): {issue['description'][:100]}")
    return {"issue": issue}


@router.put("/{issue_id}/dismiss", summary="Dismiss a resolved issue")
async def dismiss_issue(issue_id: str, request: Request):
    """Homeowner dismisses a resolved issue from their dashboard."""
    issue = issue_store.dismiss_issue(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found or not yet resolved")

    log_change(get_actor(request), "Issues",
               f"Dismissed resolved issue ({issue['severity']}): {issue['description'][:100]}")
    return {"issue": issue}
