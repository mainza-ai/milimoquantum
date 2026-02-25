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
from app.quantum import ibm_runtime
from app.quantum import braket_provider, azure_provider
from app.models.schemas import CircuitRequest

router = APIRouter(prefix="/api/quantum", tags=["quantum"])


@router.get("/status")
async def quantum_status():
    """Get quantum engine status and platform info."""
    return {
        "qiskit_available": QISKIT_AVAILABLE,
        "ibm_quantum": ibm_runtime.get_status(),
        "braket": braket_provider.get_status(),
        "azure_quantum": azure_provider.get_status(),
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


# ── Fault-Tolerant Simulation ──────────────────────────
@router.post("/ft/threshold")
async def threshold_analysis(
    distances: str = "3,5,7", error_rates: str = "0.0001,0.001,0.005,0.01"
):
    """Run error threshold analysis for surface codes."""
    from app.quantum.fault_tolerant import run_threshold_analysis

    try:
        dist_list = [int(d) for d in distances.split(",")]
        err_list = [float(e) for e in error_rates.split(",")]
    except ValueError:
        return {"error": "Invalid input format. Use comma-separated numbers."}

    return run_threshold_analysis(dist_list, err_list)


@router.get("/ft/resource-estimation")
async def resource_estimation(
    algorithm: str, size: int, error_rate: float = 1e-3
):
    """Estimate physical resources for a fault-tolerant algorithm.

    algorithm: 'shor', 'grover', 'chemistry'
    """
    from app.quantum.fault_tolerant import estimate_resources

    try:
        return estimate_resources(algorithm, size, error_rate)
    except ValueError as e:
        return {"error": str(e)}


@router.get("/ft/surface-code")
async def get_surface_code(distance: int = 3):
    """Generate a surface code lattice circuit."""
    from app.quantum.fault_tolerant import generate_surface_code

    try:
        import qiskit.qasm2
        qc = generate_surface_code(distance)
        return {
            "name": qc.name,
            "num_qubits": qc.num_qubits,
            "qasm": qiskit.qasm2.dumps(qc),
            "description": f"Rotated Surface Code d={distance} Cycle",
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/providers")
async def list_providers():
    """List all available quantum backend providers and devices."""
    providers = {
        "aer": {
            "name": "Qiskit Aer (Local Simulator)",
            "available": QISKIT_AVAILABLE,
            "type": "local",
        },
        "ibm_quantum": ibm_runtime.get_status(),
        "amazon_braket": {
            **braket_provider.get_status(),
            "devices": braket_provider.list_devices(),
        },
        "azure_quantum": {
            **azure_provider.get_status(),
            "targets": azure_provider.list_targets(),
        },
    }
    return {"providers": providers}


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


@router.post("/mitigate/{circuit_name}")
async def execute_with_mitigation(circuit_name: str, method: str = "zne", shots: int = 4096):
    """Execute a circuit with error mitigation.

    Methods: 'zne' (Zero-Noise Extrapolation) or 'measurement' (calibration-based).
    """
    if not QISKIT_AVAILABLE:
        return {"error": "Qiskit is not installed"}

    if circuit_name not in CIRCUIT_LIBRARY:
        return {"error": f"Unknown circuit: {circuit_name}"}

    from app.quantum.mitigation import apply_zne, apply_measurement_mitigation

    _, factory = CIRCUIT_LIBRARY[circuit_name]
    circuit = factory()
    if circuit is None:
        return {"error": "Failed to create circuit"}

    if method == "zne":
        return apply_zne(circuit, shots=shots)
    elif method == "measurement":
        return apply_measurement_mitigation(circuit, shots=shots)
    else:
        return {"error": f"Unknown method: {method}. Use 'zne' or 'measurement'."}

