"""Milimo Quantum — Quantum Execution Routes."""
from __future__ import annotations

import json
from fastapi import APIRouter

from app.quantum.executor import (
    CIRCUIT_LIBRARY,
    QISKIT_AVAILABLE,
    execute_circuit,
    create_bell_state,
    execute_circuit_code,
)
from app.quantum.cudaq_executor import CUDAQ_AVAILABLE
from app.quantum import cudaq_executor
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
        "cudaq_available": CUDA_Q_AVAILABLE,
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
        "cudaq": {
            "name": "NVIDIA CUDA-Q",
            "available": CUDA_Q_AVAILABLE,
            "type": "local/remote",
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
    shots = request.shots
    options = request.options or {}

    if request.backend == "cudaq":
        if not CUDA_Q_AVAILABLE:
            return {"error": "CUDA-Q is not available or installed."}
        result = cudaq_executor.execute_code(request.circuit_code, shots=shots)
    elif request.backend.startswith("braket:"):
        _, device_id = request.backend.split(":", 1)
        result = braket_provider.run_circuit(qasm_str=request.circuit_code, device_id=device_id, shots=shots)
    elif request.backend.startswith("azure:"):
        _, target_id = request.backend.split(":", 1)
        # Azure needs a qiskit circuit. Best effort parse.
        try:
            from qiskit import QuantumCircuit
            qc = QuantumCircuit.from_qasm_str(request.circuit_code)
            result = azure_provider.run_circuit(qiskit_circuit=qc, target_id=target_id, shots=shots)
        except Exception as e:
            return {"error": f"Azure Quantum requires valid QASM to build circuit: {e}"}
    elif request.type == "qasm":
        if not QISKIT_AVAILABLE:
            return {"error": "Qiskit is not installed, cannot execute QASM."}
        result = execute_circuit(qasm_str=request.circuit_code, shots=shots)
    else:
        # Code execution mode (assumes Qiskit for most backends, or specific handling for others)
        if not QISKIT_AVAILABLE and request.backend != "cudaq":
            return {"error": f"Qiskit is not installed, cannot execute code for backend '{request.backend}'."}
        result = execute_circuit_code(request.circuit_code, backend_name=request.backend, shots=shots, options=options)

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

    Methods: 'zne' (Zero-Noise Extrapolation), 'measurement' (calibration-based),
    or 'twirling' (Pauli Twirling).
    """
    if not QISKIT_AVAILABLE:
        return {"error": "Qiskit is not installed"}

    if circuit_name not in CIRCUIT_LIBRARY:
        return {"error": f"Unknown circuit: {circuit_name}"}

    from app.quantum.mitigation import apply_zne, apply_measurement_mitigation, apply_pauli_twirling

    _, factory = CIRCUIT_LIBRARY[circuit_name]
    circuit = factory()
    if circuit is None:
        return {"error": "Failed to create circuit"}

    if method == "zne":
        return apply_zne(circuit, shots=shots)
    elif method == "measurement":
        return apply_measurement_mitigation(circuit, shots=shots)
    elif method == "twirling":
        return apply_pauli_twirling(circuit, shots=shots)
    else:
        return {"success": True, "method": method, "counts": result.get_counts()}


# ── OpenQASM 3 ─────────────────────────────────────────
@router.post("/qasm3/parse")
async def parse_qasm3_endpoint(data: dict):
    """Parse an OpenQASM 3 string into structured gate data."""
    from app.quantum.qasm3 import parse_qasm3
    qasm = data.get("qasm", "")
    if not qasm.strip():
        return {"error": "No QASM string provided"}
    return parse_qasm3(qasm)


@router.post("/qasm3/export")
async def export_to_qasm3(data: dict):
    """Convert Qiskit Python code to OpenQASM 3."""
    from app.quantum.qasm3 import circuit_to_qasm3
    code = data.get("code", "")
    if not code.strip():
        return {"error": "No code provided"}
    try:
        qasm = circuit_to_qasm3(code)
        return {"qasm3": qasm}
    except Exception as e:
        return {"error": str(e)}


@router.post("/qasm3/validate")
async def validate_qasm3_endpoint(data: dict):
    """Validate an OpenQASM 3 string."""
    from app.quantum.qasm3 import validate_qasm3
    qasm = data.get("qasm", "")
    if not qasm.strip():
        return {"error": "No QASM string provided"}
    return validate_qasm3(qasm)


# ── QPY Circuit Store ──────────────────────────────────
@router.get("/circuits/saved")
async def list_saved_circuits():
    """List all saved QPY circuits."""
    from app.quantum.qpy_store import list_saved_circuits as _list
    return {"circuits": _list()}


@router.post("/circuits/save")
async def save_circuit_qpy(data: dict):
    """Save a circuit from code as QPY.

    Body: {code: str, name: str}
    """
    from app.quantum.qpy_store import save_circuit_qpy as _save

    code = data.get("code", "")
    name = data.get("name", "untitled")
    if not code.strip():
        return {"error": "No code provided"}

    try:
        from qiskit import QuantumCircuit
        local_ns: dict = {}
        exec(code, {"QuantumCircuit": QuantumCircuit}, local_ns)
        for val in local_ns.values():
            if isinstance(val, QuantumCircuit):
                return _save(val, name)
        return {"error": "No QuantumCircuit found in code"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/circuits/load/{name}")
async def load_circuit_qpy(name: str):
    """Load a saved QPY circuit by name."""
    from app.quantum.qpy_store import load_circuit_qpy as _load
    return _load(name)


# ── Noise Profiles ─────────────────────────────────────
@router.get("/noise/profiles")
async def list_noise_profiles():
    """List available noise profiles based on real device calibrations."""
    from app.quantum.noise_profiles import list_profiles
    return {"profiles": list_profiles()}


@router.get("/noise/profiles/{name}")
async def get_noise_profile(name: str):
    """Get detailed calibration data for a specific noise profile."""
    from app.quantum.noise_profiles import get_profile
    profile = get_profile(name)
    if not profile:
        return {"error": f"Unknown profile: {name}"}
    return profile


@router.post("/noise/execute")
async def execute_noisy(data: dict):
    """Execute a named circuit with a noise profile.

    Body: {circuit_name: str, profile: str, shots: int}
    """
    from app.quantum.noise_profiles import execute_with_noise

    circuit_name = data.get("circuit_name", "")
    profile_name = data.get("profile", "ibm_brisbane")
    shots = data.get("shots", 4096)

    if circuit_name not in CIRCUIT_LIBRARY:
        return {"error": f"Unknown circuit: {circuit_name}"}

    _, factory = CIRCUIT_LIBRARY[circuit_name]
    circuit = factory()
    if circuit is None:
        return {"error": "Failed to create circuit"}

    return execute_with_noise(circuit, profile_name, shots=shots)


# ── Stim Stabilizer Simulator ─────────────────────────
@router.get("/stim/available")
async def stim_available():
    """Check if Stim is installed."""
    from app.quantum.stim_sim import is_stim_available
    return {"available": is_stim_available()}


@router.post("/stim/circuit")
async def stim_create_circuit(data: dict):
    """Create a stabilizer circuit."""
    from app.quantum.stim_sim import create_stabilizer_circuit
    return create_stabilizer_circuit(
        code_distance=data.get("distance", 3),
        rounds=data.get("rounds", 1),
        noise_rate=data.get("noise_rate", 0.001),
    )


@router.post("/stim/sample")
async def stim_sample(data: dict):
    """Sample detection events from a stabilizer circuit."""
    from app.quantum.stim_sim import sample_stabilizer
    return sample_stabilizer(
        circuit_str=data.get("circuit_str"),
        code_distance=data.get("distance", 3),
        rounds=data.get("rounds", 1),
        noise_rate=data.get("noise_rate", 0.001),
        shots=data.get("shots", 10000),
    )


@router.post("/stim/decode")
async def stim_decode(data: dict):
    """Run a full decode cycle with MWPM."""
    from app.quantum.stim_sim import decode_errors
    return decode_errors(
        code_distance=data.get("distance", 3),
        rounds=data.get("rounds", 3),
        noise_rate=data.get("noise_rate", 0.01),
        shots=data.get("shots", 10000),
    )


@router.post("/stim/threshold")
async def stim_threshold(data: dict):
    """Scan error rates across distances to find threshold."""
    from app.quantum.stim_sim import threshold_scan
    return threshold_scan(
        distances=data.get("distances"),
        noise_rates=data.get("noise_rates"),
        shots=data.get("shots", 5000),
    )


# ── PennyLane Bridge ──────────────────────────────────
@router.get("/pennylane/info")
async def pennylane_info():
    """Get PennyLane version and available devices."""
    from app.quantum.pennylane_bridge import get_pennylane_info
    return get_pennylane_info()


@router.post("/pennylane/vqe")
async def pennylane_vqe(data: dict):
    """Run VQE with PennyLane's autodiff."""
    from app.quantum.pennylane_bridge import run_vqe_pennylane
    return run_vqe_pennylane(
        hamiltonian=data.get("hamiltonian", "H2"),
        num_qubits=data.get("num_qubits", 2),
        layers=data.get("layers", 2),
        steps=data.get("steps", 100),
        step_size=data.get("step_size", 0.4),
    )


@router.post("/pennylane/classifier")
async def pennylane_classifier(data: dict):
    """Train a quantum classifier with PennyLane."""
    from app.quantum.pennylane_bridge import run_qml_classifier
    return run_qml_classifier(
        n_samples=data.get("n_samples", 100),
        n_features=data.get("n_features", 2),
        n_qubits=data.get("n_qubits", 2),
        layers=data.get("layers", 3),
        epochs=data.get("epochs", 50),
    )


@router.post("/pennylane/convert")
async def pennylane_convert(data: dict):
    """Get PennyLane conversion info for a Qiskit circuit."""
    from app.quantum.pennylane_bridge import convert_qiskit_to_pennylane
    return convert_qiskit_to_pennylane(data.get("code", ""))


# ── Cloud Quantum Backends ────────────────────────────
@router.get("/cloud-backends/status")
async def cloud_backends_status():
    """Get status of all cloud quantum providers."""
    from app.quantum.cloud_backends import get_cloud_quantum_status
    return get_cloud_quantum_status()


@router.get("/cloud-backends/braket/devices")
async def braket_devices():
    """List available Amazon Braket devices."""
    from app.quantum.cloud_backends import list_braket_devices
    return {"devices": list_braket_devices()}


@router.post("/cloud-backends/braket/run")
async def braket_run(data: dict):
    """Run a circuit on Amazon Braket."""
    from app.quantum.cloud_backends import run_on_braket
    return run_on_braket(
        qiskit_code=data.get("code", ""),
        device_arn=data.get("device_arn", "arn:aws:braket:::device/quantum-simulator/amazon/sv1"),
        shots=data.get("shots", 1000),
    )


@router.get("/cloud-backends/azure/targets")
async def azure_targets():
    """List available Azure Quantum targets."""
    from app.quantum.cloud_backends import list_azure_targets
    return {"targets": list_azure_targets()}


@router.post("/cloud-backends/azure/run")
async def azure_run(data: dict):
    """Run a circuit on Azure Quantum."""
    from app.quantum.cloud_backends import run_on_azure
    return run_on_azure(
        qiskit_code=data.get("code", ""),
        target=data.get("target", "ionq.simulator"),
        shots=data.get("shots", 1000),
    )


# ── Vector Store (Semantic Search) ────────────────────
@router.get("/vector-store/status")
async def vector_store_status():
    """Get vector store statistics."""
    from app.quantum.vector_store import get_store_stats
    return get_store_stats()


@router.post("/vector-store/index")
async def vector_store_index(data: dict):
    """Index an experiment into the vector store."""
    from app.quantum.vector_store import index_experiment
    return index_experiment(
        experiment_id=data.get("experiment_id", ""),
        content=data.get("content", ""),
        metadata=data.get("metadata"),
    )


@router.post("/vector-store/search")
async def vector_store_search(data: dict):
    """Semantic search over experiments."""
    from app.quantum.vector_store import search_similar
    return search_similar(
        query=data.get("query", ""),
        n_results=data.get("n_results", 5),
        filter_metadata=data.get("filter"),
    )


# ── Citation Export ───────────────────────────────────
@router.post("/citations/bibtex")
async def citations_bibtex(data: dict):
    """Generate BibTeX for algorithms."""
    from app.experiments.citations import generate_bibtex
    bibtex = generate_bibtex(
        algorithms=data.get("algorithms"),
        include_qiskit=data.get("include_qiskit", True),
    )
    return {"bibtex": bibtex}


@router.post("/citations/zotero")
async def citations_zotero(data: dict):
    """Generate Zotero-compatible JSON for algorithms."""
    from app.experiments.citations import generate_zotero_json
    items = generate_zotero_json(
        algorithms=data.get("algorithms"),
        include_qiskit=data.get("include_qiskit", True),
    )
    return {"items": items}


@router.post("/citations/detect")
async def citations_detect(data: dict):
    """Detect algorithms in code and return citations."""
    from app.experiments.citations import detect_algorithms_in_code, generate_experiment_citation
    code = data.get("code", "")
    detected = detect_algorithms_in_code(code)
    citation = generate_experiment_citation(
        title=data.get("title", "Quantum Experiment"),
        author=data.get("author", "Milimo Quantum User"),
        algorithms=detected,
    )
    return citation
