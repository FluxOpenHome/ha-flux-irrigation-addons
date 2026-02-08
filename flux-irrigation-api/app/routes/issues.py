"""
Flux Open Home - Issue Reporting API
======================================
Allows homeowners to report issues to their management company.
Issues are stored locally on the homeowner device and accessed
by management through the proxy architecture.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

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
