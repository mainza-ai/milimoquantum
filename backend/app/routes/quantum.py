"""Milimo Quantum — Quantum Execution Routes."""
from __future__ import annotations

import json
from fastapi import APIRouter

from app.quantum.executor import (
    CIRCUIT_LIBRARY,
    QISKIT_AVAILABLE,
    execute_circuit,
    create_bell_state,
)
from app.quantum.hal import hal_config
from app.models.schemas import CircuitRequest

router = APIRouter(prefix="/api/quantum", tags=["quantum"])


@router.get("/status")
async def quantum_status():
    """Get quantum engine status and platform info."""
    return {
        "qiskit_available": QISKIT_AVAILABLE,
        "platform": {
            "os": hal_config.os_name,
            "arch": hal_config.arch,
            "torch_device": hal_config.torch_device,
            "aer_device": hal_config.aer_device,
            "llm_backend": hal_config.llm_backend,
            "gpu_available": hal_config.gpu_available,
            "gpu_name": hal_config.gpu_name,
        },
    }


@router.get("/circuits")
async def list_circuits():
    """List available pre-built circuits."""
    return {
        "circuits": {
            key: {"name": name}
            for key, (name, _) in CIRCUIT_LIBRARY.items()
        }
    }


@router.post("/execute")
async def execute_quantum(request: CircuitRequest):
    """Execute a quantum circuit."""
    if not QISKIT_AVAILABLE:
        return {"error": "Qiskit is not installed"}

    if request.qasm:
        result = execute_circuit(qasm_str=request.qasm, shots=request.shots)
    else:
        return {"error": "Provide QASM string in 'qasm' field"}

    return result


@router.get("/execute/{circuit_name}")
async def execute_named_circuit(circuit_name: str, shots: int = 1024):
    """Execute a named circuit from the library."""
    if circuit_name not in CIRCUIT_LIBRARY:
        return {"error": f"Unknown circuit: {circuit_name}. Available: {list(CIRCUIT_LIBRARY.keys())}"}

    _, factory = CIRCUIT_LIBRARY[circuit_name]
    circuit = factory()
    if circuit is None:
        return {"error": "Failed to create circuit (Qiskit may not be installed)"}

    return execute_circuit(circuit, shots=shots)
