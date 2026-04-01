"""Milimo Quantum — HPC Routes."""
from __future__ import annotations

import uuid
from app.auth import get_current_user
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.quantum.hpc import HPCAdapter
from app.quantum.hal import hal_config

router = APIRouter(prefix="/api/hpc", tags=["hpc"], dependencies=[Depends(get_current_user)])

class HPCJobRequest(BaseModel):
    qasm: str
    shots: int = 10000
    use_mpi: bool = False
    use_gpu: bool = False


@router.get("/status")
async def hpc_status():
    """Get HPC cluster capabilities."""
    # Dynamically check MPI availability
    mpi_available = False
    try:
        import subprocess
        result = subprocess.run(['which', 'mpirun'], capture_output=True, text=True)
        mpi_available = result.returncode == 0
    except Exception:
        pass
    
    return {
        "hpc_ready": True,
        "gpu_nodes_available": hal_config.gpu_available,
        "mpi_available": mpi_available,
        "active_jobs": len([j for j in HPCAdapter.HPC_JOBS.values() if j["status"] in ["QUEUED", "RUNNING"]])
    }


@router.post("/jobs")
async def submit_hpc_job(request: HPCJobRequest):
    job_id = f"hpc-{uuid.uuid4().hex[:8]}"
    
    # In a real app this would trigger a Celery task.
    # Currently it blocks, but updates the dict.
    return HPCAdapter.submit_job(
        circuit_qasm=request.qasm,
        job_id=job_id,
        shots=request.shots,
        use_mpi=request.use_mpi,
        use_gpu=request.use_gpu
    )


@router.get("/jobs/{job_id}")
async def get_hpc_job(job_id: str):
    job = HPCAdapter.get_job_status(job_id)
    if not job:
        return {"error": "Job not found", "status": "NOT_FOUND"}
    return job
