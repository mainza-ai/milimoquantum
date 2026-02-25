"""Milimo Quantum — Azure Quantum Provider.

Provides access to Azure Quantum backends (IonQ, Quantinuum).
Gated behind optional azure-quantum SDK installation.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

AZURE_AVAILABLE = False
try:
    from azure.quantum import Workspace
    from azure.quantum.qiskit import AzureQuantumProvider
    AZURE_AVAILABLE = True
except ImportError:
    logger.info("azure-quantum not installed — Azure backends disabled")


# ── Known Azure Quantum Targets ─────────────────────────
AZURE_TARGETS = {
    "ionq_simulator": {
        "name": "IonQ Simulator",
        "target": "ionq.simulator",
        "type": "Simulator",
        "provider": "IonQ",
        "qubits": 29,
    },
    "ionq_aria": {
        "name": "IonQ Aria",
        "target": "ionq.qpu.aria-1",
        "type": "QPU",
        "provider": "IonQ",
        "qubits": 25,
    },
    "quantinuum_h1": {
        "name": "Quantinuum H1-1",
        "target": "quantinuum.qpu.h1-1",
        "type": "QPU",
        "provider": "Quantinuum",
        "qubits": 20,
    },
    "quantinuum_emulator": {
        "name": "Quantinuum H1 Emulator",
        "target": "quantinuum.sim.h1-1e",
        "type": "Emulator",
        "provider": "Quantinuum",
        "qubits": 20,
    },
    "microsoft_estimator": {
        "name": "Microsoft Resource Estimator",
        "target": "microsoft.estimator",
        "type": "Estimator",
        "provider": "Microsoft",
        "qubits": None,
    },
}

# Runtime state
_workspace = None


def is_configured() -> bool:
    """Check if Azure Quantum credentials are configured."""
    return bool(
        os.environ.get("AZURE_QUANTUM_RESOURCE_ID")
        or (
            os.environ.get("AZURE_QUANTUM_SUBSCRIPTION_ID")
            and os.environ.get("AZURE_QUANTUM_RESOURCE_GROUP")
            and os.environ.get("AZURE_QUANTUM_WORKSPACE_NAME")
        )
    )


def get_status() -> dict:
    """Get Azure Quantum provider status."""
    return {
        "sdk_installed": AZURE_AVAILABLE,
        "configured": is_configured(),
        "connected": _workspace is not None,
        "provider": "Azure Quantum",
        "targets": list(AZURE_TARGETS.keys()),
    }


def connect() -> dict:
    """Connect to Azure Quantum workspace."""
    global _workspace

    if not AZURE_AVAILABLE:
        return {"error": "azure-quantum not installed. Install: pip install azure-quantum[qiskit]"}

    if not is_configured():
        return {"error": "Azure Quantum credentials not set. Set AZURE_QUANTUM_RESOURCE_ID or subscription/group/workspace env vars."}

    try:
        resource_id = os.environ.get("AZURE_QUANTUM_RESOURCE_ID")
        if resource_id:
            _workspace = Workspace(resource_id=resource_id)
        else:
            _workspace = Workspace(
                subscription_id=os.environ["AZURE_QUANTUM_SUBSCRIPTION_ID"],
                resource_group=os.environ["AZURE_QUANTUM_RESOURCE_GROUP"],
                name=os.environ["AZURE_QUANTUM_WORKSPACE_NAME"],
                location=os.environ.get("AZURE_QUANTUM_LOCATION", "eastus"),
            )

        logger.info("Connected to Azure Quantum workspace")
        return {"status": "connected", "provider": "Azure Quantum"}
    except Exception as e:
        logger.error(f"Azure Quantum connection failed: {e}")
        return {"error": str(e)}


def list_targets() -> list[dict]:
    """List available Azure Quantum targets."""
    targets = []
    for target_id, info in AZURE_TARGETS.items():
        available = AZURE_AVAILABLE and (
            info["type"] in ("Simulator", "Emulator", "Estimator") or is_configured()
        )
        targets.append({
            "id": target_id,
            "name": info["name"],
            "target": info["target"],
            "provider": info["provider"],
            "type": info["type"],
            "qubits": info["qubits"],
            "available": available,
        })
    return targets


def run_circuit(
    qiskit_circuit: Any,
    target_id: str = "ionq_simulator",
    shots: int = 1024,
) -> dict:
    """Run a Qiskit circuit on an Azure Quantum target.

    Args:
        qiskit_circuit: A Qiskit QuantumCircuit.
        target_id: Target key from AZURE_TARGETS.
        shots: Number of measurement shots.

    Returns:
        dict with counts, job_id, target info.
    """
    if not AZURE_AVAILABLE:
        return {"error": "azure-quantum not installed"}

    if target_id not in AZURE_TARGETS:
        return {"error": f"Unknown target: {target_id}. Available: {list(AZURE_TARGETS.keys())}"}

    if not _workspace:
        conn = connect()
        if "error" in conn:
            return conn

    target_info = AZURE_TARGETS[target_id]

    try:
        provider = AzureQuantumProvider(workspace=_workspace)
        backend = provider.get_backend(target_info["target"])

        from qiskit import transpile
        transpiled = transpile(qiskit_circuit, backend)
        job = backend.run(transpiled, shots=shots)
        result = job.result()
        counts = result.get_counts()

        return {
            "counts": counts,
            "shots": shots,
            "target": target_info["name"],
            "target_id": target_id,
            "provider": "Azure Quantum",
            "job_id": job.job_id(),
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Azure Quantum execution failed: {e}")
        return {"error": str(e)}
