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
    """Append an immutable log entry to the database."""
    from app.db import get_session
    from app.db.models import AuditLog
    
    session = get_session()
    try:
        log = AuditLog(
            user_id=user,
            action=action,
            resource_type="system",
            resource_id=resource,
            details=details or {},
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        session.add(log)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save audit log: {e}")
    finally:
        session.close()


async def get_logs(limit: int = 50):
    """Retrieve recent audit logs (reverse chronological)."""
    from app.db import get_session
    from app.db.models import AuditLog
    
    session = get_session()
    try:
        logs = session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        return [
            {
                "timestamp": l.timestamp.isoformat(),
                "user": l.user_id,
                "action": l.action,
                "resource": l.resource_id,
                "details": l.details,
            }
            for l in logs
        ]
    except Exception as e:
        logger.error(f"Failed to fetch audit logs: {e}")
        return []
    finally:
        session.close()
