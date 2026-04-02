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


def run_on_google(
    qiskit_code: str,
    target: str = "simulator",
    shots: int = 1000
) -> dict:
    """
    Execute circuit on Google Quantum via Cirq.
    
    Targets:
    - simulator: Cirq simulator (default)
    - rainbow: Google Rainbow processor (requires auth)
    - weber: Google Weber processor (requires auth)
    
    Args:
        qiskit_code: Qiskit Python code string
        target: Target backend name
        shots: Number of shots
    
    Returns:
        Execution result with counts
    """
    if not is_google_available():
        return {
            "error": "Cirq not installed. Install with: pip install cirq cirq-google",
            "status": "MISSING_DEPENDENCY"
        }
    
    try:
        import cirq
        from qiskit import QuantumCircuit
        from qiskit.qasm2 import dumps
        
        # Parse Qiskit circuit
        local_ns: dict = {}
        exec(qiskit_code, {"QuantumCircuit": QuantumCircuit}, local_ns)
        
        qc = None
        for val in local_ns.values():
            if isinstance(val, QuantumCircuit):
                qc = val
                break
        
        if qc is None:
            return {"error": "No QuantumCircuit found in code"}
        
        # Convert Qiskit to Cirq
        cirq_circuit = _convert_qiskit_to_cirq(qc)
        
        # Execute on target
        if target == "simulator":
            simulator = cirq.Simulator()
            result = simulator.run(cirq_circuit, repetitions=shots)
            
            # Extract counts
            counts = {}
            for measurement in result.measurements:
                bitstrings = result.measurements[measurement]
                for bitstring in bitstrings:
                    key = ''.join(str(int(b)) for b in bitstring)
                    counts[key] = counts.get(key, 0) + 1
            
            return {
                "target": target,
                "shots": shots,
                "counts": counts,
                "status": "COMPLETED",
                "n_qubits": qc.num_qubits,
                "circuit_depth": qc.depth()
            }
        
        else:
            # Real hardware requires Google Cloud authentication
            return {
                "error": f"Google {target} requires Google Cloud authentication",
                "status": "AUTH_REQUIRED",
                "setup_url": "https://quantumai.google/cirq/google/access",
                "targets_available": ["simulator", "rainbow", "weber"]
            }
            
    except ImportError as e:
        return {"error": f"Import error: {str(e)}", "status": "IMPORT_ERROR"}
    except Exception as e:
        logger.error(f"Google Quantum execution failed: {e}")
        return {"error": str(e), "status": "ERROR"}


def _convert_qiskit_to_cirq(qc) -> "cirq.Circuit":
    """Convert Qiskit circuit to Cirq circuit."""
    import cirq
    import numpy as np
    
    n_qubits = qc.num_qubits
    qubits = [cirq.LineQubit(i) for i in range(n_qubits)]
    operations = []
    
    for instruction in qc.data:
        gate = instruction[0]
        qubit_indices = [q.index for q in instruction[1]]
        params = list(gate.params) if hasattr(gate, 'params') else []
        
        # Gate mapping
        gate_name = gate.name.lower()
        
        if gate_name == 'h':
            operations.append(cirq.H(qubits[qubit_indices[0]]))
        elif gate_name == 'x':
            operations.append(cirq.X(qubits[qubit_indices[0]]))
        elif gate_name == 'y':
            operations.append(cirq.Y(qubits[qubit_indices[0]]))
        elif gate_name == 'z':
            operations.append(cirq.Z(qubits[qubit_indices[0]]))
        elif gate_name == 's':
            operations.append(cirq.S(qubits[qubit_indices[0]]))
        elif gate_name == 't':
            operations.append(cirq.T(qubits[qubit_indices[0]]))
        elif gate_name == 'rx':
            operations.append(cirq.rx(params[0]).on(qubits[qubit_indices[0]]))
        elif gate_name == 'ry':
            operations.append(cirq.ry(params[0]).on(qubits[qubit_indices[0]]))
        elif gate_name == 'rz':
            operations.append(cirq.rz(params[0]).on(qubits[qubit_indices[0]]))
        elif gate_name in ['cx', 'cnot']:
            operations.append(cirq.CNOT(qubits[qubit_indices[0]], qubits[qubit_indices[1]]))
        elif gate_name == 'cz':
            operations.append(cirq.CZ(qubits[qubit_indices[0]], qubits[qubit_indices[1]]))
        elif gate_name == 'swap':
            operations.append(cirq.SWAP(qubits[qubit_indices[0]], qubits[qubit_indices[1]]))
        elif gate_name == 'measure':
            for idx in qubit_indices:
                operations.append(cirq.measure(qubits[idx], key=f'm{idx}'))
        else:
            # Try to decompose or skip unknown gates
            logger.warning(f"Unknown gate {gate_name}, skipping")
    
    return cirq.Circuit(operations)


def dispatch_quantum_job(
    provider_id: str,
    qiskit_code: str,
    shots: int = 1000,
    **kwargs,
) -> dict:
    """Dynamically route a quantum job to the specified cloud provider.

    Args:
        provider_id: One of 'braket', 'azure', 'google', 'local'
        qiskit_code: Qiskit Python code string
        shots: Number of shots
        **kwargs: Additional provider-specific parameters
            - device_arn: Braket device ARN
            - target: Azure target name

    Returns:
        Execution result dict with counts, status, and provider info.
    """
    provider_id = provider_id.lower().strip()

    if provider_id == "braket":
        device_arn = kwargs.get(
            "device_arn",
            "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        )
        return {
            "provider": "amazon_braket",
            **run_on_braket(qiskit_code, device_arn=device_arn, shots=shots),
        }

    if provider_id == "azure":
        target = kwargs.get("target", "ionq.simulator")
        return {
            "provider": "azure_quantum",
            **run_on_azure(qiskit_code, target=target, shots=shots),
        }

    if provider_id == "google":
        return {
            "provider": "google_quantum",
            **run_on_google(qiskit_code, target=kwargs.get("target", "simulator"), shots=shots),
        }

    if provider_id == "local":
        from qiskit import QuantumCircuit
        from qiskit_aer import AerSimulator
        from qiskit import transpile

        local_ns: dict = {}
        exec(qiskit_code, {"QuantumCircuit": QuantumCircuit}, local_ns)
        qc = None
        for val in local_ns.values():
            if isinstance(val, QuantumCircuit):
                qc = val
                break
        if qc is None:
            return {"provider": "local", "error": "No QuantumCircuit found in code"}
        sim = AerSimulator()
        result = sim.run(transpile(qc, sim), shots=shots).result()
        return {
            "provider": "local",
            "counts": result.get_counts(),
            "status": "COMPLETED",
        }

    return {"provider": provider_id, "error": f"Unknown provider: {provider_id}"}


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
