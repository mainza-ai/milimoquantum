"""Milimo Quantum — Team Collaboration Routes.

Share projects and conversations via token-based links.
"""
from __future__ import annotations

import json
import logging
import secrets
import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/collaboration", tags=["collaboration"])

STORAGE_DIR = Path.home() / ".milimoquantum"
SHARES_DIR = STORAGE_DIR / "shares"


def _ensure_dir():
    SHARES_DIR.mkdir(parents=True, exist_ok=True)


# ── Create Share Link ──────────────────────────────────
@router.post("/share")
async def create_share_link(data: dict):
    """Create a share link for a project or conversation.

    Body: { "resource_type": "project"|"conversation", "resource_id": "...",
            "expires_hours": 72, "permissions": "view"|"edit" }
    """
    _ensure_dir()

    resource_type = data.get("resource_type", "conversation")
    resource_id = data.get("resource_id")
    if not resource_id:
        raise HTTPException(status_code=400, detail="resource_id required")

    expires_hours = data.get("expires_hours", 72)
    permissions = data.get("permissions", "view")

    token = secrets.token_urlsafe(32)
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now + datetime.timedelta(hours=expires_hours)

    share = {
        "token": token,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "permissions": permissions,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "access_count": 0,
    }

    filepath = SHARES_DIR / f"{token}.json"
    filepath.write_text(json.dumps(share, indent=2), encoding="utf-8")

    return {
        "token": token,
        "share_url": f"/shared/{token}",
        "expires_at": expires_at.isoformat(),
        "permissions": permissions,
    }


# ── Access Shared Resource ─────────────────────────────
@router.get("/shared/{token}")
async def access_shared(token: str):
    """Access a shared resource by token."""
    _ensure_dir()

    filepath = SHARES_DIR / f"{token}.json"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    share = json.loads(filepath.read_text(encoding="utf-8"))

    # Check expiration
    expires_at = datetime.datetime.fromisoformat(share["expires_at"])
    if datetime.datetime.now(datetime.timezone.utc) > expires_at:
        filepath.unlink(missing_ok=True)
        raise HTTPException(status_code=410, detail="Share link has expired")

    # Increment access count
    share["access_count"] = share.get("access_count", 0) + 1
    filepath.write_text(json.dumps(share, indent=2), encoding="utf-8")

    # Load the resource
    resource_type = share["resource_type"]
    resource_id = share["resource_id"]

    if resource_type == "conversation":
        from app.storage import load_conversation
        data = load_conversation(resource_id)
        if not data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {
            "type": "conversation",
            "permissions": share["permissions"],
            "data": {
                "id": data.get("id", resource_id),
                "title": data.get("title", "Untitled"),
                "messages": data.get("messages", []),
            },
        }
    elif resource_type == "project":
        from app.routes.projects import _load_project
        project = _load_project(resource_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return {
            "type": "project",
            "permissions": share["permissions"],
            "data": project,
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unknown resource type: {resource_type}")


# ── List Active Shares ─────────────────────────────────
@router.get("/shares")
async def list_shares():
    """List all active (non-expired) share links."""
    _ensure_dir()

    shares = []
    now = datetime.datetime.now(datetime.timezone.utc)

    for filepath in SHARES_DIR.glob("*.json"):
        try:
            share = json.loads(filepath.read_text(encoding="utf-8"))
            expires_at = datetime.datetime.fromisoformat(share["expires_at"])
            if now > expires_at:
                filepath.unlink(missing_ok=True)
                continue
            shares.append({
                "token": share["token"],
                "resource_type": share["resource_type"],
                "resource_id": share["resource_id"],
                "permissions": share["permissions"],
                "created_at": share["created_at"],
                "expires_at": share["expires_at"],
                "access_count": share.get("access_count", 0),
            })
        except (json.JSONDecodeError, KeyError, OSError):
            continue

    return {"shares": shares}


# ── Revoke Share ───────────────────────────────────────
@router.delete("/shared/{token}")
async def revoke_share(token: str):
    """Revoke a share link."""
    _ensure_dir()

    filepath = SHARES_DIR / f"{token}.json"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Share link not found")

    filepath.unlink()
    return {"status": "revoked", "token": token}
