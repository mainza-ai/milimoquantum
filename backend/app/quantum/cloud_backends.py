"""Milimo Quantum — Cloud Quantum Providers.

Integration with Amazon Braket and Azure Quantum for remote
hardware execution beyond IBM Quantum.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


# ── Amazon Braket ──────────────────────────────────────
def is_braket_available() -> bool:
    """Check if Amazon Braket SDK is installed."""
    try:
        import braket # noqa: F401
        return True
    except ImportError:
        return False


def is_google_available() -> bool:
    """Check if Google Quantum (Cirq) is installed."""
    try:
        import cirq # noqa: F401
        return True
    except ImportError:
        return False


def list_braket_devices() -> list[dict]:
    """List available Amazon Braket devices."""
    try:
        from braket.aws import AwsDevice

        devices = AwsDevice.get_devices(statuses=["ONLINE"])
        return [
            {
                "arn": d.arn,
                "name": d.name,
                "provider": d.provider_name,
                "type": str(d.type),
                "status": d.status,
                "qubits": getattr(d, "qubit_count", None),
            }
            for d in devices
        ]
    except ImportError:
        return [{"error": "Amazon Braket SDK not installed. pip install amazon-braket-sdk"}]
    except Exception as e:
        return [{"error": str(e)}]


def run_on_braket(
    qiskit_code: str,
    device_arn: str = "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
    shots: int = 1000,
) -> dict:
    """Execute a Qiskit circuit on Amazon Braket.

    Transpiles Qiskit circuit to Braket format and submits.
    """
    try:
        from braket.aws import AwsDevice
        from braket.circuits import Circuit as BraketCircuit
        from qiskit import QuantumCircuit

        # Parse Qiskit code to get circuit
        local_ns: dict = {}
        exec(qiskit_code, {"QuantumCircuit": QuantumCircuit}, local_ns)
        qc = None
        for val in local_ns.values():
            if isinstance(val, QuantumCircuit):
                qc = val
                break

        if qc is None:
            return {"error": "No QuantumCircuit found in code"}

        # Convert via OpenQASM 3
        from qiskit.qasm3 import dumps
        qasm_str = dumps(qc)

        # Submit to Braket
        device = AwsDevice(device_arn)
        braket_circuit = BraketCircuit.from_ir(qasm_str)
        task = device.run(braket_circuit, shots=shots)
        result = task.result()

        return {
            "device": device_arn,
            "shots": shots,
            "counts": dict(result.measurement_counts),
            "task_id": task.id,
            "status": "COMPLETED",
        }
    except ImportError:
        return {"error": "Amazon Braket SDK not installed. pip install amazon-braket-sdk"}
    except Exception as e:
        return {"error": str(e)}


# ── Azure Quantum ──────────────────────────────────────
def is_azure_available() -> bool:
    """Check if Azure Quantum SDK is installed."""
    try:
        import azure.quantum  # noqa: F401
        return True
    except ImportError:
        return False


def list_azure_targets() -> list[dict]:
    """List available Azure Quantum targets."""
    try:
        from azure.quantum import Workspace

        resource_id = os.environ.get("AZURE_QUANTUM_RESOURCE_ID", "")
        location = os.environ.get("AZURE_QUANTUM_LOCATION", "eastus")

        if not resource_id:
            return [{"error": "AZURE_QUANTUM_RESOURCE_ID not set"}]

        workspace = Workspace(resource_id=resource_id, location=location)
        targets = workspace.get_targets()

        return [
            {
                "name": t.name,
                "provider": t.provider_id,
                "type": t.target_type,
                "status": t.current_availability,
            }
            for t in targets
        ]
    except ImportError:
        return [{"error": "Azure Quantum SDK not installed. pip install azure-quantum"}]
    except Exception as e:
        return [{"error": str(e)}]


def run_on_azure(
    qiskit_code: str,
    target: str = "ionq.simulator",
    shots: int = 1000,
) -> dict:
    """Execute a Qiskit circuit on Azure Quantum.

    Uses the Azure Quantum Qiskit provider for submission.
    """
    try:
        from azure.quantum.qiskit import AzureQuantumProvider
        from qiskit import QuantumCircuit, transpile

        resource_id = os.environ.get("AZURE_QUANTUM_RESOURCE_ID", "")
        location = os.environ.get("AZURE_QUANTUM_LOCATION", "eastus")

        if not resource_id:
            return {"error": "AZURE_QUANTUM_RESOURCE_ID not set"}

        # Parse circuit
        local_ns: dict = {}
        exec(qiskit_code, {"QuantumCircuit": QuantumCircuit}, local_ns)
        qc = None
        for val in local_ns.values():
            if isinstance(val, QuantumCircuit):
                qc = val
                break

        if qc is None:
            return {"error": "No QuantumCircuit found in code"}

        provider = AzureQuantumProvider(resource_id=resource_id, location=location)
        backend = provider.get_backend(target)
        transpiled = transpile(qc, backend)
        job = backend.run(transpiled, shots=shots)
        result = job.result()

        return {
            "target": target,
            "shots": shots,
            "counts": result.get_counts(),
            "job_id": job.id(),
            "status": "COMPLETED",
        }
    except ImportError:
        return {"error": "Azure Quantum SDK not installed. pip install azure-quantum[qiskit]"}
    except Exception as e:
        return {"error": str(e)}


def get_cloud_quantum_status() -> dict:
    """Overview of available cloud quantum providers."""
    return {
        "ibm_quantum": {
            "available": True,  # Already integrated via routes/ibm.py
            "env_var": "IBM_QUANTUM_TOKEN",
            "configured": bool(os.environ.get("IBM_QUANTUM_TOKEN")),
        },
        "amazon_braket": {
            "available": is_braket_available(),
            "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
            "configured": bool(os.environ.get("AWS_ACCESS_KEY_ID")),
        },
        "azure_quantum": {
            "available": is_azure_available(),
            "env_var": "AZURE_QUANTUM_RESOURCE_ID",
            "configured": bool(os.environ.get("AZURE_QUANTUM_RESOURCE_ID")),
        },
        "google_quantum": {
            "available": is_google_available(),
            "env_vars": ["GOOGLE_APPLICATION_CREDENTIALS"],
            "configured": bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")),
        },
    }
