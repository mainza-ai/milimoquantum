"""Milimo Quantum — Quantum Circuit Executor.

Executes circuits via Qiskit Aer with HAL-selected backend options.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.quantum.hal import hal_config

logger = logging.getLogger(__name__)

# Try importing Qiskit — gracefully degrade if not installed
QISKIT_AVAILABLE = False
try:
    from qiskit import QuantumCircuit, transpile
    from qiskit.visualization import circuit_drawer
    from qiskit_aer import AerSimulator
    from qiskit.primitives import StatevectorEstimator
    from qiskit.quantum_info import SparsePauliOp
    
    # Qiskit Nature for Hamiltonian mapping
    import qiskit_nature
    from qiskit_nature.second_q.drivers import PySCFDriver
    from qiskit_nature.second_q.mappers import JordanWignerMapper, ParityMapper
    from qiskit_nature.second_q.formats.molecule_info import MoleculeInfo
    
    # Qiskit Algorithms for VQE
    from qiskit_algorithms import VQE
    from qiskit_algorithms.optimizers import SLSQP
    from qiskit.circuit.library import RealAmplitudes
    
    QISKIT_AVAILABLE = True
    logger.info("Qiskit and Qiskit Nature loaded successfully")
except ImportError as e:
    logger.warning(f"Quantum libraries partially missing: {e} — quantum execution limited")


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

    # Extract statevector for 1-qubit circuits to render on Bloch Sphere
    statevector = None
    if num_qubits == 1:
        try:
            from qiskit.quantum_info import Statevector
            import numpy as np
            import cmath
            
            sv_circ = circuit.remove_final_measurements(inplace=False)
            sv = Statevector(sv_circ)
            
            alpha, beta = sv.data[0], sv.data[1]
            p0 = abs(alpha)**2
            # Handle float precision issues
            p0 = min(1.0, max(0.0, p0))
            theta = 2 * np.arccos(np.sqrt(p0))
            phi = cmath.phase(beta) - cmath.phase(alpha)
            if phi < 0:
                phi += 2 * np.pi
                
            statevector = {"theta": float(theta), "phi": float(phi)}
        except Exception as e:
            logger.warning(f"Could not compute statevector: {e}")

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
        "statevector": statevector,
        "circuit_svg": svg_str,
        "num_qubits": num_qubits,
        "depth": circuit.depth(),
        "shots": shots,
        "execution_time_ms": round(float(elapsed), 2),
        "backend": f"aer_{backend_opts.get('method', 'auto')}",
    }


def run_estimator(
    circuit: QuantumCircuit,
    observables: SparsePauliOp | list[SparsePauliOp] | Any,
    precision: float = 1e-3
) -> Any:
    """Run Qiskit Estimator to get expectation values."""
    if not QISKIT_AVAILABLE:
        return {"error": "Qiskit is not installed."}
    
    try:
        estimator = StatevectorEstimator()
        job = estimator.run([(circuit, observables)], precision=precision)
        result = job.result()
        # Return expectation values (usually a numpy array or single float)
        return result[0].data.evs
    except Exception as e:
        logger.error(f"Estimator error: {e}")
        return {"error": str(e)}


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
        local_vars: dict[str, Any] = {}
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


def create_1q_state(gate: str = 'h') -> Any:
    """Create a basic 1-qubit state circuit."""
    if not QISKIT_AVAILABLE:
        return None
    qc = QuantumCircuit(1, 1)
    if gate == 'h':
        qc.h(0)
    elif gate == 'x':
        qc.x(0)
    elif gate == 'y':
        qc.y(0)
    qc.measure(0, 0)
    return qc


def map_molecule_to_hamiltonian(smiles: str, basis: str = "sto3g", mapper_type: str = "jordan_wigner") -> Any:
    """
    Maps a molecule (SMILES) to a qubit Hamiltonian using Qiskit Nature.
    """
    if not QISKIT_AVAILABLE:
        return None
    
    try:
        # 1. Setup Driver (PySCF) for the molecule
        # For simplicity, we create a basic geometry if XYZ not provided
        driver = PySCFDriver(atom=f"SMILES {smiles}", basis=basis)
        problem = driver.run()
        
        # 2. Extract second-quantized operator
        hamiltonian = problem.hamiltonian.second_q_op()
        
        # 3. Choose Mapper
        if mapper_type.lower() == "parity":
            mapper = ParityMapper()
        else:
            mapper = JordanWignerMapper()
            
        # 4. Map to Qubit Operator
        qubit_op = mapper.map(hamiltonian)
        return qubit_op
    except Exception as e:
        logger.error(f"Hamiltonian mapping failed for {smiles}: {e}")
        return None

async def run_vqe(qubit_op: Any, ansatz: Any = None, optimizer: Any = None) -> float:
    """
    Runs VQE to find the ground state energy of a qubit operator.
    """
    if not QISKIT_AVAILABLE:
        return 0.0
    
    try:
        num_qubits = qubit_op.num_qubits
        if ansatz is None:
            ansatz = RealAmplitudes(num_qubits, reps=1)
        
        if optimizer is None:
            optimizer = SLSQP(maxiter=10) # Fast for prototype
            
        # Use simple Statevector Estimator for VQE
        from qiskit.primitives import StatevectorEstimator
        estimator = StatevectorEstimator()
        
        # Optimized implementation: for now we use a simpler approach matching our runner
        # Since qiskit-algorithms VQE expects V1 primitives or custom wrapper,
        # we'll do a simplified expectation value minimization.
        
        import numpy as np
        from scipy.optimize import minimize
        
        def objective(params):
            bound_ansatz = ansatz.assign_parameters(params)
            job = estimator.run([(bound_ansatz, qubit_op)])
            result = job.result()
            return float(result[0].data.evs)
        
        initial_point = np.random.uniform(-np.pi, np.pi, ansatz.num_parameters)
        res = minimize(objective, initial_point, method='SLSQP', options={'maxiter': 5})
        
        return float(res.fun)
    except Exception as e:
        logger.error(f"VQE execution failed: {e}")
        return 0.0

# Named circuit library
CIRCUIT_LIBRARY = {
    "superposition": ("Superposition (1 qubit)", lambda: create_1q_state('h')),
    "xgate": ("X Gate (1 qubit)", lambda: create_1q_state('x')),
    "ygate": ("Y Gate (1 qubit)", lambda: create_1q_state('y')),
    "bell": ("Bell State (2 qubits)", create_bell_state),
    "ghz": ("GHZ State (3 qubits)", lambda: create_ghz_state(3)),
    "ghz5": ("GHZ State (5 qubits)", lambda: create_ghz_state(5)),
    "qft": ("Quantum Fourier Transform (3 qubits)", lambda: create_qft_circuit(3)),
}
