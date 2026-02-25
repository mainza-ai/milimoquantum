"""Milimo Quantum — Audit Routes."""
from __future__ import annotations
from fastapi import APIRouter, Depends

from app.audit import get_logs

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/log")
async def audit_log(limit: int = 50):
    """View system audit logs (Admin only in prod)."""
    return {"logs": await get_logs(limit)}
