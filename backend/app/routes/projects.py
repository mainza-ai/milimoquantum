"""Milimo Quantum — Project Management Routes.

Full CRUD for quantum computing projects.
Projects organize conversations, experiments, and results.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["projects"])

PROJECTS_DIR = Path.home() / ".milimoquantum" / "projects"


def _ensure_dir():
    """Ensure the projects directory exists."""
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_project(project_id: str) -> dict | None:
    """Load a project from disk."""
    filepath = PROJECTS_DIR / f"{project_id}.json"
    if not filepath.exists():
        return None
    try:
        return json.loads(filepath.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _save_project(project: dict) -> None:
    """Save a project to disk."""
    _ensure_dir()
    filepath = PROJECTS_DIR / f"{project['id']}.json"
    project["updated_at"] = datetime.utcnow().isoformat()
    filepath.write_text(json.dumps(project, indent=2, default=str), encoding="utf-8")


@router.get("/")
async def list_projects():
    """List all projects."""
    _ensure_dir()
    projects = []
    for filepath in sorted(PROJECTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            projects.append({
                "id": data["id"],
                "name": data.get("name", "Untitled"),
                "description": data.get("description", ""),
                "tags": data.get("tags", []),
                "conversation_ids": data.get("conversation_ids", []),
                "conversation_count": len(data.get("conversation_ids", [])),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
            })
        except (json.JSONDecodeError, OSError, KeyError):
            continue

    # Ensure default project exists
    if not projects:
        default = _create_default_project()
        projects.append({
            "id": default["id"],
            "name": default["name"],
            "description": default["description"],
            "tags": default.get("tags", []),
            "conversation_ids": [],
            "conversation_count": 0,
            "created_at": default["created_at"],
            "updated_at": default["updated_at"],
        })

    return {"projects": projects}


@router.post("/")
async def create_project(data: dict):
    """Create a new project."""
    project_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    project = {
        "id": project_id,
        "name": data.get("name", "New Project"),
        "description": data.get("description", ""),
        "tags": data.get("tags", []),
        "conversation_ids": [],
        "created_at": now,
        "updated_at": now,
    }
    _save_project(project)
    logger.info(f"Created project {project_id}: {project['name']}")
    return project


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get a project by ID."""
    project = _load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}")
async def update_project(project_id: str, data: dict):
    """Update a project."""
    project = _load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if "name" in data:
        project["name"] = data["name"]
    if "description" in data:
        project["description"] = data["description"]
    if "tags" in data:
        project["tags"] = data["tags"]

    _save_project(project)
    logger.info(f"Updated project {project_id}")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    filepath = PROJECTS_DIR / f"{project_id}.json"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    filepath.unlink()
    logger.info(f"Deleted project {project_id}")
    return {"deleted": True}


@router.post("/{project_id}/conversations/{conversation_id}")
async def add_conversation_to_project(project_id: str, conversation_id: str):
    """Associate a conversation with a project."""
    project = _load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if conversation_id not in project.get("conversation_ids", []):
        project.setdefault("conversation_ids", []).append(conversation_id)
        _save_project(project)
    return {"added": True}


@router.delete("/{project_id}/conversations/{conversation_id}")
async def remove_conversation_from_project(project_id: str, conversation_id: str):
    """Remove a conversation from a project."""
    project = _load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if conversation_id in project.get("conversation_ids", []):
        project["conversation_ids"].remove(conversation_id)
        _save_project(project)
    return {"removed": True}


def _create_default_project() -> dict:
    """Create the default project if none exists."""
    project = {
        "id": "default",
        "name": "My Quantum Lab",
        "description": "Default quantum computing workspace",
        "tags": ["general"],
        "conversation_ids": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    _save_project(project)
    return project
