"""Milimo Quantum - Workflow Orchestration API.

API for triggering Celery parameter sweeps and parallel quantum executions.
"""
from __future__ import annotations

import logging
from typing import Dict, Any
from app.auth import get_current_user
from fastapi import APIRouter, HTTPException, Depends

logger = logging.getLogger(__name__)

try:
    from app.worker.tasks import run_parameter_sweep as celery_run_parameter_sweep
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery tasks unavailable, workflows will run synchronously or fail.")

router = APIRouter(prefix="/api/workflows", tags=["workflows"], dependencies=[Depends(get_current_user)])

@router.post("/parameter_sweep")
async def trigger_parameter_sweep(payload: Dict[str, Any]):
    """Trigger a parallel parameter sweep over a base circuit."""
    base_code = payload.get("base_code")
    param_grid = payload.get("param_grid")
    
    if not base_code or not param_grid:
        raise HTTPException(status_code=400, detail="Missing base_code or param_grid")

    if not CELERY_AVAILABLE:
        return {"status": "error", "message": "Celery worker not available to distribute sweep."}
    
    # In a full production setup, this would dispatch the task to Celery and return a Task ID.
    try:
        task_id = celery_run_parameter_sweep.delay(base_code, param_grid)
        return {
            "status": "submitted",
            "task_id": str(task_id),
            "message": f"Parameter sweep submitted for {len(param_grid)} variations."
        }
    except Exception as e:
        logger.error(f"Failed to submit sweep task: {e}")
        return {"status": "error", "message": str(e)}

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Query the status of an ongoing distributed workflow task."""
    if not CELERY_AVAILABLE:
        return {"status": "error", "message": "Celery worker not available"}

    from celery.result import AsyncResult
    from app.worker.celery_app import app as celery_app

    res = AsyncResult(task_id, app=celery_app)
    
    result_data = None
    if res.ready():
        result_data = res.result
        if isinstance(res.result, Exception):
            result_data = {"error": str(res.result)}
    
    return {
        "task_id": task_id,
        "status": res.status,
        "result": result_data,
        "traceback": str(res.traceback) if res.failed() else None
    }
@router.post("/submit")
async def submit_dag_workflow(payload: Dict[str, Any]):
    """Submit a complex Directed Acyclic Graph (DAG) for orchestrated execution."""
    tasks = payload.get("tasks", [])
    if not tasks:
        raise HTTPException(status_code=400, detail="Workflow must contain at least one task.")
    
    logger.info(f"Submitting DAG workflow with {len(tasks)} nodes.")
    
    if not CELERY_AVAILABLE:
        return {"status": "error", "message": "Celery worker not available to distribute DAG."}
        
    try:
        from celery import chord, group
        from app.worker.tasks import execute_dag_node, finalize_dag
        import uuid
        
        workflow_id = f"dag_{uuid.uuid4().hex[:8]}"
        
        # Build parallel execution group mapped to a sequential finalize callback
        node_tasks = [execute_dag_node.s(node) for node in tasks]
        workflow_chord = chord(group(*node_tasks), finalize_dag.s(workflow_id=workflow_id))
        
        result = workflow_chord.apply_async()
        
        return {
            "status": "submitted",
            "workflow_id": workflow_id,
            "task_id": str(result.id),
            "message": f"Successfully queued DAG with {len(tasks)} parallel quantum tasks."
        }
    except ImportError as e:
        logger.error(f"Celery missing DAG dependencies: {e}")
        return {"status": "error", "message": "Celery not properly configured."}
    except Exception as e:
        logger.error(f"DAG submission failed: {e}")
        return {"status": "error", "message": str(e)}
