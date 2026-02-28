"""Milimo Quantum — Benchmarking Routes."""
from __future__ import annotations
from app.auth import get_current_user
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.quantum.benchmarking import BenchmarkEngine

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"], dependencies=[Depends(get_current_user)])


class BenchmarkRequest(BaseModel):
    name: str = "random_circuit"
    size: int = 5
    shots: int = 1024
    backend: str = "aer_simulator"


@router.post("/run")
async def run_benchmark(request: BenchmarkRequest):
    """Run a quantum benchmark comparison.
    
    name: 'random_circuit', 'qft', 'grover'
    size: Number of qubits (default 5)
    """
    return BenchmarkEngine.run_benchmark(
        name=request.name,
        size=request.size,
        shots=request.shots,
        backend_name=request.backend
    )


@router.get("/history")
async def benchmark_history(limit: int = 20):
    """Get recent benchmark results."""
    return {"history": BenchmarkEngine.get_history(limit)}
