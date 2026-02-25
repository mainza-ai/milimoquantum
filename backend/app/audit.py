"""Milimo Quantum — Audit Logging.

Immutable tracking of sensitive operations for enterprise compliance.
"""
from __future__ import annotations

import logging
import json
import datetime
from pathlib import Path

from fastapi import Request

STORAGE_DIR = Path.home() / ".milimoquantum"
AUDIT_LOG_FILE = STORAGE_DIR / "audit.log"

logger = logging.getLogger("audit")


def _ensure_log_file():
    if not AUDIT_LOG_FILE.parent.exists():
        AUDIT_LOG_FILE.parent.mkdir(parents=True)


async def log_action(user: str, action: str, resource: str, details: dict = None):
    """Append an immutable log entry."""
    _ensure_log_file()
    
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "user": user,
        "action": action,
        "resource": resource,
        "details": details or {},
    }
    
    # Append line to file (JSONL format)
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


async def get_logs(limit: int = 50):
    """Retrieve recent audit logs (reverse chronological)."""
    if not AUDIT_LOG_FILE.exists():
        return []
        
    logs = []
    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    
    return list(reversed(logs))[:limit]
