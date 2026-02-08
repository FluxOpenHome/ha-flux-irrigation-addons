"""
Flux Open Home - Issue Reporting API
======================================
Allows homeowners to report issues to their management company.
Issues are stored locally on the homeowner device and accessed
by management through the proxy architecture.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

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
    """Generate an .ics calendar file for a scheduled service date.

    Returns Content-Type: text/calendar so the device's default calendar
    app opens automatically (Apple Calendar, Google Calendar, Outlook, etc.).
    """
    issue = issue_store.get_issue(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    if not issue.get("service_date"):
        raise HTTPException(status_code=404, detail="No service date scheduled for this issue")

    svc_date = issue["service_date"]  # YYYY-MM-DD
    dt_start = svc_date.replace("-", "")
    dt_end_date = datetime.strptime(svc_date, "%Y-%m-%d") + timedelta(days=1)
    dt_end = dt_end_date.strftime("%Y%m%d")
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    uid = f"flux-svc-{issue['id']}@flux-irrigation"

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
        description += f"\\nNote from management: {note_clean}"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Flux Open Home//Irrigation Service//EN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{stamp}",
        f"DTSTART;VALUE=DATE:{dt_start}",
        f"DTEND;VALUE=DATE:{dt_end}",
        f"SUMMARY:{title}",
        f"DESCRIPTION:{description}",
    ]
    if location:
        lines.append(f"LOCATION:{location}")
    lines += [
        "STATUS:CONFIRMED",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    ics_content = "\r\n".join(lines)

    return Response(
        content=ics_content,
        media_type="text/calendar",
    )


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
