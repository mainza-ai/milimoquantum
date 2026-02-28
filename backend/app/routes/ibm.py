"""Milimo Quantum — IBM Quantum Runtime Routes.

HTTP endpoints for managing IBM Quantum hardware connections and job execution.
All IBM Runtime logic is delegated to app.quantum.ibm_runtime.
"""
from __future__ import annotations

import logging
from app.auth import get_current_user
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.quantum.ibm_runtime import (
    connect,
    get_status,
    is_configured,
    list_backends,
    run_sampler,
)
from app.audit import log_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quantum/ibm", tags=["ibm-quantum"], dependencies=[Depends(get_current_user)])


class ConnectRequest(BaseModel):
    token: str | None = None
    channel: str = "ibm_quantum"


class RunRequest(BaseModel):
    circuit_qasm: str | None = None
    shots: int = 4096
    backend: str | None = None


# ── Status ─────────────────────────────────────────────
@router.get("/status")
async def ibm_status():
    """Get IBM Quantum Runtime connection status."""
    status = get_status()
    status["token_configured"] = is_configured()
    return status


# ── Connect ────────────────────────────────────────────
@router.post("/connect")
async def ibm_connect(req: ConnectRequest):
    """Connect to IBM Quantum Runtime with an API token."""
    result = connect(token=req.token, channel=req.channel)
    await log_action("user", "ibm_connect", "ibm_quantum",
                     {"channel": req.channel, "status": result.get("status", "error")})
    return result


# ── List Backends ─────────────────────────────────────
@router.get("/backends")
async def ibm_backends():
    """List available IBM Quantum backends (requires connection)."""
    backends = list_backends()
    return {"backends": backends, "count": len(backends)}


# ── Run Circuit ───────────────────────────────────────
@router.post("/run")
async def ibm_run(req: RunRequest):
    """Execute a circuit on IBM Quantum hardware via SamplerV2.

    Requires prior connection via /connect endpoint.
    Accepts either a QASM string or will use the last sandbox circuit.
    """
    if req.circuit_qasm:
        try:
            from qiskit import QuantumCircuit
            circuit = QuantumCircuit.from_qasm_str(req.circuit_qasm)
        except Exception as e:
            return {"error": f"Invalid QASM: {str(e)}"}
    else:
        return {"error": "No circuit provided. Send circuit_qasm in request body."}

    result = run_sampler(circuit, shots=req.shots, backend_name=req.backend)
    return result
