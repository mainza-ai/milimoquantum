"""Milimo Quantum — Project Management Routes.

Full CRUD for quantum computing projects via PostgreSQL.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime

from app.auth import get_current_user
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.db import get_session
from app.db.models import Project

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["projects"], dependencies=[Depends(get_current_user)])

class ProjectCreate(BaseModel):
    name: str = "New Project"
    description: str = ""
    tags: List[str] = []

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


def _create_default_project(session: Session, tenant_id: str) -> dict:
    """Create the default project if none exists for the tenant."""
    project = Project(
        id=f"default-{tenant_id}",
        tenant_id=tenant_id,
        name="My Quantum Lab",
        description="Default quantum computing workspace",
        tags=["general"],
        conversation_ids=[]
    )
    session.add(project)
    session.commit()
    return _format_project(project)


def _format_project(p: Project) -> dict:
    # Ensure tags and arrays are always lists
    tags = p.tags if isinstance(p.tags, list) else (list(p.tags) if p.tags else [])
    # Sync: Get conversation IDs from the direct relationship
    convs = [c.id for c in p.conversations]
    
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "tags": tags,
        "conversation_ids": convs,
        "conversation_count": len(convs),
        "created_at": p.created_at.isoformat() if p.created_at else "",
        "updated_at": p.updated_at.isoformat() if p.updated_at else "",
    }


@router.get("/")
async def list_projects(current_user: dict = Depends(get_current_user)):
    """List all projects for the current tenant."""
    session = get_session()
    tenant_id = current_user.get("sub", "default-tenant")
    try:
        projects = session.query(Project).filter_by(tenant_id=tenant_id).order_by(Project.updated_at.desc()).all()
        if not projects:
            default = _create_default_project(session, tenant_id)
            return {"projects": [default]}
        return {"projects": [_format_project(p) for p in projects]}
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail="Database Error")
    finally:
        session.close()


@router.post("/")
async def create_project(data: ProjectCreate, current_user: dict = Depends(get_current_user)):
    """Create a new project."""
    session = get_session()
    tenant_id = current_user.get("sub", "default-tenant")
    try:
        now = datetime.utcnow()
        project = Project(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            tags=data.tags,
            conversation_ids=[],
            created_at=now,
            updated_at=now
        )
        session.add(project)
        session.commit()
        logger.info(f"Created project {project.id}: {project.name} for tenant {tenant_id}")
        return _format_project(project)
    finally:
        session.close()


@router.get("/{project_id}")
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get a project by ID with tenant isolation."""
    session = get_session()
    tenant_id = current_user.get("sub", "default-tenant")
    try:
        project = session.query(Project).filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return _format_project(project)
    finally:
        session.close()


@router.put("/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate, current_user: dict = Depends(get_current_user)):
    """Update a project with tenant isolation."""
    session = get_session()
    tenant_id = current_user.get("sub", "default-tenant")
    try:
        project = session.query(Project).filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description
        if data.tags is not None:
            project.tags = data.tags
            
        project.updated_at = datetime.utcnow()
        session.commit()
        logger.info(f"Updated project {project_id}")
        return _format_project(project)
    finally:
        session.close()


@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a project with tenant isolation."""
    session = get_session()
    tenant_id = current_user.get("sub", "default-tenant")
    try:
        project = session.query(Project).filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        session.delete(project)
        session.commit()
        logger.info(f"Deleted project {project_id}")
        return {"deleted": True}
    finally:
        session.close()


@router.post("/{project_id}/conversations/{conversation_id}")
async def add_conversation_to_project(project_id: str, conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Associate a conversation with a project."""
    session = get_session()
    tenant_id = current_user.get("sub", "default-tenant")
    try:
        project = session.query(Project).filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # JSON fields in SQLAlchemy can be tricky, sometimes require reassignment
        convs = project.conversation_ids if project.conversation_ids else []
        if isinstance(convs, list) and conversation_id not in convs:
            new_convs = list(convs)
            new_convs.append(conversation_id)
            project.conversation_ids = new_convs
            project.updated_at = datetime.utcnow()
            
            # Strong Linkage: Update the conversation record directly
            from app.db.models import Conversation
            conv_record = session.query(Conversation).filter_by(id=conversation_id).first()
            if conv_record:
                conv_record.project_id = project_id
            
            session.commit()
        return {"added": True}
    finally:
        session.close()


@router.delete("/{project_id}/conversations/{conversation_id}")
async def remove_conversation_from_project(project_id: str, conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Remove a conversation from a project."""
    session = get_session()
    tenant_id = current_user.get("sub", "default-tenant")
    try:
        project = session.query(Project).filter_by(id=project_id, tenant_id=tenant_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        convs = project.conversation_ids if project.conversation_ids else []
        if isinstance(convs, list) and conversation_id in convs:
            new_convs = list(convs)
            new_convs.remove(conversation_id)
            project.conversation_ids = new_convs
            project.updated_at = datetime.utcnow()
            
            # Strong Linkage: Unlink the conversation
            from app.db.models import Conversation
            conv_record = session.query(Conversation).filter_by(id=conversation_id).first()
            if conv_record and conv_record.project_id == project_id:
                conv_record.project_id = None
                
            session.commit()
        return {"removed": True}
    finally:
        session.close()
