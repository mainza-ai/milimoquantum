"""Milimo Quantum — IBM Quantum Runtime Integration.

Provides access to IBM Quantum hardware via qiskit-ibm-runtime.
Gated behind API token configuration.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ── Runtime State ───────────────────────────────────────
_service = None
_backend = None
IBM_AVAILABLE = False

try:
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2, EstimatorV2
    IBM_AVAILABLE = True
except ImportError:
    logger.info("qiskit-ibm-runtime not installed — IBM hardware disabled")


def is_configured() -> bool:
    """Check if IBM Quantum credentials are configured."""
    return bool(os.environ.get("IBM_QUANTUM_TOKEN") or os.environ.get("QISKIT_IBM_TOKEN"))


def get_status() -> dict:
    """Get IBM Quantum Runtime status."""
    return {
        "sdk_installed": IBM_AVAILABLE,
        "configured": is_configured(),
        "connected": _service is not None,
        "backend": str(_backend) if _backend else None,
    }


def connect(token: str | None = None, channel: str = "ibm_quantum") -> dict:
    """Connect to IBM Quantum Runtime."""
    global _service, _backend

    if not IBM_AVAILABLE:
        return {"error": "qiskit-ibm-runtime is not installed. Install with: pip install qiskit-ibm-runtime"}

    token = token or os.environ.get("IBM_QUANTUM_TOKEN") or os.environ.get("QISKIT_IBM_TOKEN")
    if not token:
        return {"error": "No IBM Quantum token provided. Set IBM_QUANTUM_TOKEN environment variable."}

    try:
        _service = QiskitRuntimeService(channel=channel, token=token)
        backends = _service.backends()
        backend_names = [b.name for b in backends[:10]]

        # Select least busy backend
        if backends:
            _backend = _service.least_busy(min_num_qubits=2)

        logger.info(f"Connected to IBM Quantum — {len(backends)} backends available")
        return {
            "status": "connected",
            "backends": backend_names,
            "selected_backend": str(_backend) if _backend else None,
            "channel": channel,
        }
    except Exception as e:
        logger.error(f"IBM Quantum connection failed: {e}")
        return {"error": str(e)}


def list_backends() -> list[dict]:
    """List available IBM Quantum backends."""
    if not _service:
        return []

    try:
        backends = _service.backends()
        return [
            {
                "name": b.name,
                "num_qubits": b.num_qubits if hasattr(b, 'num_qubits') else None,
                "status": "online" if b.status().operational else "offline",
            }
            for b in backends[:20]
        ]
    except Exception as e:
        logger.error(f"Failed to list backends: {e}")
        return []


def run_sampler(circuit: Any, shots: int = 4096, backend_name: str | None = None) -> dict:
    """Run a circuit via IBM SamplerV2."""
    if not _service:
        return {"error": "Not connected to IBM Quantum. Call connect() first."}

    try:
        backend = _service.backend(backend_name) if backend_name else _backend
        if not backend:
            return {"error": "No backend selected"}

        sampler = SamplerV2(backend)
        job = sampler.run([circuit], shots=shots)
        result = job.result()

        # Extract counts from SamplerV2 result
        pub_result = result[0]
        counts = pub_result.data.meas.get_counts() if hasattr(pub_result.data, 'meas') else {}

        return {
            "counts": counts,
            "job_id": job.job_id(),
            "backend": str(backend),
            "shots": shots,
            "status": "completed",
        }
    except Exception as e:
        return {"error": f"Sampler execution failed: {str(e)}"}


def run_estimator(circuit: Any, observable: Any, backend_name: str | None = None) -> dict:
    """Run a circuit + observable via IBM EstimatorV2."""
    if not _service:
        return {"error": "Not connected to IBM Quantum. Call connect() first."}

    try:
        backend = _service.backend(backend_name) if backend_name else _backend
        if not backend:
            return {"error": "No backend selected"}

        estimator = EstimatorV2(backend)
        job = estimator.run([(circuit, observable)])
        result = job.result()

        pub_result = result[0]
        return {
            "expectation_value": float(pub_result.data.evs),
            "std_error": float(pub_result.data.stds) if hasattr(pub_result.data, 'stds') else None,
            "job_id": job.job_id(),
            "backend": str(backend),
            "status": "completed",
        }
    except Exception as e:
        return {"error": f"Estimator execution failed: {str(e)}"}
