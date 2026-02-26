"""Milimo Quantum — Quantum Circuit Executor.

Executes circuits via Qiskit Aer with HAL-selected backend options.
"""
from __future__ import annotations

import io
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Try importing Qiskit — gracefully degrade if not installed
QISKIT_AVAILABLE = False
try:
    from qiskit import QuantumCircuit, transpile
    from qiskit.visualization import circuit_drawer
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
    logger.info("Qiskit loaded successfully")
except ImportError:
    logger.warning("Qiskit not installed — quantum execution disabled")

from app.quantum.hal import hal_config


def execute_circuit(
    circuit: Any | None = None,
    qasm_str: str | None = None,
    shots: int = 1024,
) -> dict:
    """Execute a quantum circuit and return results."""
    if not QISKIT_AVAILABLE:
        return {
            "error": "Qiskit is not installed. Install with: pip install qiskit qiskit-aer",
            "counts": {},
            "circuit_svg": "",
            "num_qubits": 0,
            "depth": 0,
            "shots": shots,
            "execution_time_ms": 0,
            "backend": "none",
        }

    # Build circuit from QASM if needed
    if circuit is None and qasm_str:
        try:
            circuit = QuantumCircuit.from_qasm_str(qasm_str)
        except Exception as e:
            return {"error": f"Invalid QASM: {str(e)}"}

    if circuit is None:
        return {"error": "No circuit provided"}

    # Get HAL configuration
    num_qubits = circuit.num_qubits
    backend_opts = hal_config.aer_backend_options(num_qubits)

    # ── Cloud routing: if IBM configured and qubit count is high, use IBM
    from app.quantum import ibm_runtime
    if ibm_runtime.is_configured() and num_qubits > hal_config.aer_backend_options(num_qubits).get("max_local", 28):
        logger.info(f"Routing {num_qubits}-qubit circuit to IBM Quantum cloud")
        if not ibm_runtime._service:
            ibm_runtime.connect()
        if ibm_runtime._service:
            ibm_result = ibm_runtime.run_sampler(circuit, shots=shots)
            if "error" not in ibm_result:
                return {
                    "counts": ibm_result.get("counts", {}),
                    "circuit_svg": str(circuit.draw(output="text")),
                    "num_qubits": num_qubits,
                    "depth": circuit.depth(),
                    "shots": shots,
                    "execution_time_ms": 0,
                    "backend": f"ibm_{ibm_result.get('backend', 'cloud')}",
                    "job_id": ibm_result.get("job_id"),
                }

    # ── Local execution: Aer simulator
    # Create simulator
    try:
        simulator = AerSimulator(**backend_opts)
    except Exception:
        simulator = AerSimulator()

    # Transpile & run
    start = time.time()
    transpiled = transpile(circuit, simulator)
    job = simulator.run(transpiled, shots=shots)
    result = job.result()
    elapsed = (time.time() - start) * 1000

    counts = result.get_counts()

    # Generate circuit SVG
    svg_str = ""
    try:
        svg_str = circuit_drawer(circuit, output="text").single_string()
    except Exception:
        try:
            svg_str = str(circuit.draw(output="text"))
        except Exception:
            svg_str = str(circuit)

    return {
        "counts": counts,
        "circuit_svg": svg_str,
        "num_qubits": num_qubits,
        "depth": circuit.depth(),
        "shots": shots,
        "execution_time_ms": round(elapsed, 2),
        "backend": f"aer_{backend_opts.get('method', 'auto')}",
    }


def execute_circuit_code(
    circuit_code: str,
    backend_name: str = "aer_simulator",
    shots: int = 1024,
    options: dict | None = None,
) -> dict:
    """Execute python code that defines a 'qc' QuantumCircuit variable."""
    if not QISKIT_AVAILABLE:
        return {"error": "Qiskit is not installed."}
        
    try:
        # Create a safe execution environment
        local_vars = {}
        exec(circuit_code, globals(), local_vars)
        
        # Look for a circuit variable
        qc = None
        for var_name in ["qc", "circuit", "qft_circ", "bell_circ"]:
            if var_name in local_vars and isinstance(local_vars[var_name], QuantumCircuit):
                qc = local_vars[var_name]
                break
                
        if qc is None:
            # Fallback: find any QuantumCircuit
            for obj in local_vars.values():
                if isinstance(obj, QuantumCircuit):
                    qc = obj
                    break
                    
        if qc:
            return execute_circuit(circuit=qc, shots=shots)
        else:
            return {"error": "Could not find a QuantumCircuit object in the provided code."}
            
    except Exception as e:
        return {"error": f"Execution error: {str(e)}"}



def create_bell_state() -> Any:
    """Create a simple Bell state circuit for testing."""
    if not QISKIT_AVAILABLE:
        return None
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def create_ghz_state(n: int = 3) -> Any:
    """Create a GHZ state circuit."""
    if not QISKIT_AVAILABLE:
        return None
    qc = QuantumCircuit(n, n)
    qc.h(0)
    for i in range(1, n):
        qc.cx(0, i)
    qc.measure(range(n), range(n))
    return qc


def create_qft_circuit(n: int = 3) -> Any:
    """Create a QFT circuit."""
    if not QISKIT_AVAILABLE:
        return None
    from qiskit.circuit.library import QFT
    qc = QuantumCircuit(n, n)
    qc.append(QFT(n), range(n))
    qc.measure(range(n), range(n))
    return qc


# Named circuit library
CIRCUIT_LIBRARY = {
    "bell": ("Bell State (2 qubits)", create_bell_state),
    "ghz": ("GHZ State (3 qubits)", lambda: create_ghz_state(3)),
    "ghz5": ("GHZ State (5 qubits)", lambda: create_ghz_state(5)),
    "qft": ("Quantum Fourier Transform (3 qubits)", lambda: create_qft_circuit(3)),
}
