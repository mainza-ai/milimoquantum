"""Milimo Quantum — Async Jobs Router.

Endpoints for interacting with the Celery worker cluster.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Depends
from celery.result import AsyncResult

from app.worker.tasks import app
from app.worker.tasks import execute_quantum_circuit
from app.models.schemas import CircuitRequest
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/jobs", 
    tags=["jobs", "celery"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/execute")
async def async_execute_circuit(request: CircuitRequest):
    """Submit a quantum circuit for asynchronous background execution.
    
    Returns a job_id for polling.
    """
    try:
        task = execute_quantum_circuit.delay(
            circuit_code=request.code or request.qasm,
            backend_name=request.backend,
            shots=request.shots,
            transpile_options={},
        )
        return {
            "job_id": task.id,
            "status": "QUEUED",
            "message": "Quantum circuit queued for execution",
        }
    except Exception as e:
        logger.error(f"Failed to queue job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-code")
async def async_execute_code(data: dict):
    """Submit arbitrary python code for background sandbox execution.
    
    Returns a job_id for polling.
    """
    code = data.get("code", "")
    if not code.strip():
        return {"error": "No code provided"}

    from app.worker.tasks import run_code_sandbox
    try:
        task = run_code_sandbox.delay(code=code)
        return {
            "job_id": task.id,
            "status": "QUEUED",
            "message": "Arbitrary code queued for sandbox execution",
        }
    except Exception as e:
        logger.error(f"Failed to queue sandbox job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """Poll the status of a specific AsyncResult job."""
    task = AsyncResult(job_id, app=app)
    
    response = {
        "job_id": job_id,
        "status": task.status,
        "successful": task.successful(),
    }
    
    if task.state == "PENDING":
        response["message"] = "Job is waiting in queue"
    elif task.state == "RUNNING":
        response["message"] = task.info.get("status", "Running...") if isinstance(task.info, dict) else "Running..."
    elif task.state == "SUCCESS":
        response["result"] = task.get()
    elif task.state == "FAILURE":
        response["error"] = str(task.info)
    
    return response


@router.delete("/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Attempt to revoke a running or pending job."""
    app.control.revoke(job_id, terminate=True)
    return {"job_id": job_id, "status": "REVOKED"}
