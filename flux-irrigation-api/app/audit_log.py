"""
Audit logging for the Irrigation Management API.
Logs all API calls for transparency and troubleshooting.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from config import get_config


LOG_DIR = "/data/audit_logs"
LOG_FILE = os.path.join(LOG_DIR, "audit.jsonl")


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def log_action(
    api_key_name: str,
    method: str,
    path: str,
    action: str,
    details: Optional[dict] = None,
    status_code: int = 200,
    client_ip: Optional[str] = None,
):
    """Write an audit log entry."""
    config = get_config()
    if not config.enable_audit_log:
        return

    _ensure_log_dir()

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_key_name": api_key_name,
        "client_ip": client_ip,
        "method": method,
        "path": path,
        "action": action,
        "details": details or {},
        "status_code": status_code,
    }

    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[AUDIT] Failed to write log: {e}")


def get_recent_logs(limit: int = 100, api_key_name: Optional[str] = None) -> list[dict]:
    """Read recent audit log entries."""
    if not os.path.exists(LOG_FILE):
        return []

    entries = []
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        if api_key_name and entry.get("api_key_name") != api_key_name:
                            continue
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
    except Exception:
        return []

    # Return most recent entries
    return entries[-limit:]


def cleanup_old_logs():
    """Remove audit log entries older than the retention period."""
    config = get_config()
    if not os.path.exists(LOG_FILE):
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=config.log_retention_days)
    cutoff_str = cutoff.isoformat()

    kept_lines = []
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("timestamp", "") >= cutoff_str:
                        kept_lines.append(line)
                except json.JSONDecodeError:
                    continue

        with open(LOG_FILE, "w") as f:
            for line in kept_lines:
                f.write(line + "\n")

    except Exception as e:
        print(f"[AUDIT] Failed to cleanup logs: {e}")
