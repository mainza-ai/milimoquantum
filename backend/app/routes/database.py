"""Milimo Quantum — Database Routes.

API endpoints for database management, health check, and migration status.
"""
from __future__ import annotations

from app.auth import get_current_user
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/db", tags=["database"], dependencies=[Depends(get_current_user)])


@router.get("/status")
async def db_status():
    """Get database connection status and stats."""
    from app.db import get_database_url, is_postgres, get_session
    from app.db.models import Conversation, Experiment, User, AuditLog

    url = get_database_url()
    db_type = "PostgreSQL" if is_postgres() else "SQLite"

    try:
        session = get_session()
        stats = {
            "conversations": session.query(Conversation).count(),
            "experiments": session.query(Experiment).count(),
            "users": session.query(User).count(),
            "audit_logs": session.query(AuditLog).count(),
        }
        session.close()
        connected = True
    except Exception as e:
        stats = {}
        connected = False

    return {
        "database": db_type,
        "connected": connected,
        "url_masked": url[:20] + "..." if len(url) > 20 else url,
        "stats": stats,
    }


@router.post("/init")
async def init_database():
    """Initialize database tables (development only)."""
    from app.db import init_db
    init_db()
    return {"status": "ok", "message": "Database tables created/verified"}


@router.get("/migrations")
async def migration_status():
    """Get Alembic migration status."""
    import subprocess
    try:
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True, text=True, timeout=10,
            cwd="/Users/mck/Desktop/milimoquantum/backend",
        )
        return {
            "current": result.stdout.strip(),
            "error": result.stderr.strip() if result.returncode != 0 else None,
        }
    except FileNotFoundError:
        return {"current": "alembic not found", "error": "Run: pip install alembic"}
    except Exception as e:
        return {"current": None, "error": str(e)}
