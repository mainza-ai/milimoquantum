"""Milimo Quantum — Project Management Routes."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/")
async def list_projects():
    """List all projects (placeholder)."""
    return {
        "projects": [
            {
                "id": "default",
                "name": "My Quantum Lab",
                "description": "Default quantum computing workspace",
                "conversation_count": 0,
            }
        ]
    }
