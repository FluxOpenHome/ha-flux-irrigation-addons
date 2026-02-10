"""
Flux Open Home - Issue Reporting Store
========================================
Manages homeowner-reported issues for the management company.
Persists issue data in /data/issues.json.

Issue lifecycle:
  open → acknowledged → scheduled (if service_date set) → resolved → dismissed
"""

import json
import os
import uuid
from datetime import datetime, timezone


ISSUES_FILE = "/data/issues.json"

DEFAULT_DATA = {
    "version": 1,
    "issues": [],
}

VALID_SEVERITIES = ("clarification", "annoyance", "severe")
SEVERITY_ORDER = {"severe": 3, "annoyance": 2, "clarification": 1}


# --- Persistence ---

def _load_data() -> dict:
    """Load issue data from persistent storage."""
    if os.path.exists(ISSUES_FILE):
        try:
            with open(ISSUES_FILE, "r") as f:
                data = json.load(f)
                for key, default in DEFAULT_DATA.items():
                    if key not in data:
                        data[key] = default
                # Backfill missing fields from older versions
                for issue in data.get("issues", []):
                    issue.setdefault("homeowner_dismissed", False)
                    issue.setdefault("service_date_updated_at", None)
                return data
        except (json.JSONDecodeError, IOError):
            pass
    return json.loads(json.dumps(DEFAULT_DATA))  # deep copy


def _save_data(data: dict):
    """Save issue data to persistent storage."""
    os.makedirs(os.path.dirname(ISSUES_FILE), exist_ok=True)
    with open(ISSUES_FILE, "w") as f:
        json.dump(data, f, indent=2)


# --- Issue Operations ---

def create_issue(severity: str, description: str) -> dict:
    """Create a new issue. Returns the created issue dict."""
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity: {severity}")
    if not description or len(description) > 1000:
        raise ValueError("Description must be 1-1000 characters")

    data = _load_data()
    issue = {
        "id": str(uuid.uuid4()),
        "severity": severity,
        "description": description.strip(),
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "acknowledged_at": None,
        "management_note": None,
        "service_date": None,
        "resolved_at": None,
        "homeowner_dismissed": False,
        "service_date_updated_at": None,
    }
    data["issues"].append(issue)
    _save_data(data)
    return issue


def get_all_issues() -> list:
    """Return all issues, newest first."""
    data = _load_data()
    return sorted(data["issues"], key=lambda i: i.get("created_at", ""), reverse=True)


def get_active_issues() -> list:
    """Return issues that are not resolved, newest first."""
    data = _load_data()
    active = [i for i in data["issues"] if i.get("status") != "resolved"]
    return sorted(active, key=lambda i: i.get("created_at", ""), reverse=True)


def get_visible_issues() -> list:
    """Return issues visible to the homeowner: active + resolved-but-not-dismissed.

    This lets homeowners see management's response (note, resolution) before
    dismissing the issue from their dashboard.
    """
    data = _load_data()
    visible = [
        i for i in data["issues"]
        if i.get("status") != "resolved" or not i.get("homeowner_dismissed")
    ]
    return sorted(visible, key=lambda i: i.get("created_at", ""), reverse=True)


def dismiss_issue(issue_id: str) -> dict | None:
    """Homeowner dismisses a resolved issue so it no longer shows on their dashboard."""
    data = _load_data()
    for issue in data["issues"]:
        if issue["id"] == issue_id:
            if issue.get("status") != "resolved":
                return None  # Can only dismiss resolved issues
            issue["homeowner_dismissed"] = True
            _save_data(data)
            return issue
    return None


def get_issue(issue_id: str) -> dict | None:
    """Find a single issue by ID."""
    data = _load_data()
    for issue in data["issues"]:
        if issue["id"] == issue_id:
            return issue
    return None


def acknowledge_issue(issue_id: str, note: str | None = None, service_date: str | None = None) -> dict | None:
    """Acknowledge an issue, optionally setting a note and service date.

    If service_date is provided, status becomes 'scheduled'.
    Otherwise, status becomes 'acknowledged'.
    """
    data = _load_data()
    for issue in data["issues"]:
        if issue["id"] == issue_id:
            if issue["status"] == "resolved":
                return None  # Cannot acknowledge a resolved issue
            issue["status"] = "scheduled" if service_date else "acknowledged"
            issue["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            if note is not None:
                issue["management_note"] = note.strip()[:500] if note else None
            if service_date is not None:
                old_service_date = issue.get("service_date")
                issue["service_date"] = service_date
                # Track whether this is an update (not first-time set)
                if old_service_date is not None and old_service_date != service_date:
                    issue["service_date_updated_at"] = datetime.now(timezone.utc).isoformat()
            _save_data(data)
            return issue
    return None


def resolve_issue(issue_id: str) -> dict | None:
    """Mark an issue as resolved."""
    data = _load_data()
    for issue in data["issues"]:
        if issue["id"] == issue_id:
            issue["status"] = "resolved"
            issue["resolved_at"] = datetime.now(timezone.utc).isoformat()
            _save_data(data)
            return issue
    return None


def get_issue_summary() -> dict:
    """Return a lightweight summary of active issues for health check polling."""
    active = get_active_issues()
    if not active:
        return {"active_count": 0, "max_severity": None, "issues": []}

    max_sev = max(active, key=lambda i: SEVERITY_ORDER.get(i.get("severity", ""), 0))
    return {
        "active_count": len(active),
        "max_severity": max_sev.get("severity"),
        "issues": [
            {
                "id": i["id"],
                "severity": i["severity"],
                "description": i["description"][:200],  # Truncate for summary
                "status": i["status"],
                "created_at": i["created_at"],
            }
            for i in active
        ],
    }
