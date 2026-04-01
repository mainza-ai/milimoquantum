"""
Real VQE execution using Qiskit Aer simulation.
Replaces the mock VQE implementation.
"""
from __future__ import annotations

import logging
import numpy as np
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

try:
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit.circuit.library import EfficientSU2, RealAmplitudes, TwoLocal
    from qiskit_aer.primitives import EstimatorV2 as AerEstimatorV2
    from qiskit_algorithms import VQE
    from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver
    from qiskit_algorithms.optimizers import SPSA, COBYLA, L_BFGS_B, SLSQP
    from qiskit_algorithms.utils import algorithm_globals
    QISKIT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Qiskit not fully available: {e}")
    QISKIT_AVAILABLE = False

from .hal import select_aer_backend

# Predefined Hamiltonians
HAMILTONIANS = {
    'h2': [
        ("II", -1.052373245772859),
        ("IZ", 0.39793742484318045),
        ("ZI", -0.39793742484318045),
        ("ZZ", -0.01128010425623538),
        ("XX", 0.18093119978423156),
    ],
    'h2_exact': -1.85728,
    'lih': [
        ("IIII", -7.499763400876443),
        ("IIIZ", -0.0920519843788469),
        ("IIZI", -0.09205198437884688),
        ("IIZZ", 0.09872239219922697),
        ("IZII", -0.0920519843788469),
        ("IZIZ", 0.09872239219922697),
        ("IZZI", 0.09872239219922697),
        ("ZIII", -0.09205198437884688),
        ("ZIIZ", 0.09872239219922697),
        ("ZIZI", 0.09872239219922697),
        ("ZZII", 0.09872239219922697),
        ("XXXX", 0.043215),  # Simplified
        ("YYYY", 0.043215),
    ],
    'lih_exact': -7.882,
}

# Ansatz catalog
ANSATZ_CATALOG = {
    'efficient_su2': lambda n, reps=2: EfficientSU2(n, reps=reps),
    'real_amplitudes': lambda n, reps=2: RealAmplitudes(n, reps=reps),
    'two_local_ry_cz': lambda n, reps=2: TwoLocal(
        n, rotation_blocks=['ry'], entanglement_blocks='cz', reps=reps
    ),
    'two_local_ryrz_cz': lambda n, reps=2: TwoLocal(
        n, rotation_blocks=['ry', 'rz'], entanglement_blocks='cz', reps=reps
    ),
    'two_local_full': lambda n, reps=2: TwoLocal(
        n, rotation_blocks=['ry', 'rz'], entanglement_blocks='cx',
        entanglement='full', reps=reps
    ),
}

# Optimizer catalog
OPTIMIZER_CATALOG = {
    'spsa': lambda maxiter=300: SPSA(maxiter=maxiter),
    'cobyla': lambda maxiter=200: COBYLA(maxiter=maxiter),
    'l_bfgs_b': lambda maxiter=100: L_BFGS_B(maxiter=maxiter),
    'slsqp': lambda maxiter=100: SLSQP(maxiter=maxiter),
}


def meyer_wallach_score(circuit) -> float:
    """
    Compute the Meyer-Wallach global entanglement measure for a circuit.
    Returns a value in [0, 1] where:
    0 = fully separable (no entanglement)
    1 = maximally entangled

    Reference: Meyer & Wallach (2002), J. Math. Phys. 43, 4273.
    """
    if not QISKIT_AVAILABLE:
        return 0.5
    
    n = circuit.num_qubits
    
    if circuit.num_parameters > 0:
        bound = circuit.assign_parameters(
            np.random.uniform(0, 2 * np.pi, circuit.num_parameters)
        )
    else:
        bound = circuit
    
    sv = Statevector(bound).data
    arr = sv.reshape([2] * n)
    
    Q = 0.0
    for k in range(n):
        other_axes = [i for i in range(n) if i != k]
        rho_k = np.tensordot(arr, arr.conj(), axes=(other_axes, other_axes))
        Q += 2.0 * (1.0 - float(np.real(np.trace(rho_k @ rho_k))))
    
    return Q / n


def run_vqe(
    hamiltonian: str | List[tuple],
    ansatz_type: str = 'efficient_su2',
    ansatz_reps: int = 2,
    optimizer: str = 'spsa',
    optimizer_maxiter: int = 300,
    seed: int = 42,
    on_iteration: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Run VQE with full Aer simulation. This is NOT a mock.

    Args:
        hamiltonian: Preset name ('h2', 'lih') or list of (pauli_str, coeff) tuples.
        ansatz_type: Key from ANSATZ_CATALOG.
        ansatz_reps: Number of ansatz repetitions (depth).
        optimizer: Key from OPTIMIZER_CATALOG.
        optimizer_maxiter: Maximum optimizer iterations.
        seed: Random seed for reproducibility.
        on_iteration: Optional callback(eval_count, energy) for SSE streaming.

    Returns:
        Dict with eigenvalue, convergence_trace, circuit stats, entanglement score.
    """
    if not QISKIT_AVAILABLE:
        return {
            'error': 'Qiskit not available - cannot run VQE',
            'eigenvalue': None,
        }
    
    algorithm_globals.random_seed = seed
    
    # Build Hamiltonian
    if isinstance(hamiltonian, str):
        h_list = HAMILTONIANS.get(hamiltonian)
        if h_list is None or isinstance(h_list, float):
            raise ValueError(f"Unknown Hamiltonian preset '{hamiltonian}'. Options: {list(HAMILTONIANS)}")
    else:
        h_list = hamiltonian
    
    H = SparsePauliOp.from_list(h_list)
    num_qubits = H.num_qubits
    logger.info(f"VQE | Hamiltonian: {num_qubits} qubits, {len(h_list)} Pauli terms")
    
    # Reference value (exact classical)
    try:
        numpy_solver = NumPyMinimumEigensolver()
        ref = numpy_solver.compute_minimum_eigenvalue(H)
        reference_energy = float(ref.eigenvalue.real)
    except Exception:
        reference_energy = None
    
    # Build ansatz
    ansatz_factory = ANSATZ_CATALOG.get(ansatz_type, ANSATZ_CATALOG['efficient_su2'])
    ansatz = ansatz_factory(num_qubits, ansatz_reps)
    # Decompose to basic gates for Aer compatibility
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    _basis_sim = AerSimulator(method='statevector')
    ansatz = transpile(ansatz, backend=_basis_sim, optimization_level=1)
    logger.info(f"VQE | Ansatz: {ansatz_type}, reps={ansatz_reps}, "
                f"depth={ansatz.depth()}, params={ansatz.num_parameters}")
    
    # Compute entanglement score before optimization
    mw_score = meyer_wallach_score(ansatz)
    logger.info(f"VQE | Meyer-Wallach entanglement score: {mw_score:.4f}")
    
    # Select Aer backend
    sim = select_aer_backend(num_qubits)
    estimator = AerEstimatorV2()
    
    # Build optimizer
    optimizer_factory = OPTIMIZER_CATALOG.get(optimizer, OPTIMIZER_CATALOG['spsa'])
    optimizer_instance = optimizer_factory(maxiter=optimizer_maxiter)
    
    # Convergence tracking
    convergence_trace = []

    def callback(eval_count, params, mean, metadata):
        # In qiskit-algorithms 0.4+, the 4th arg is metadata dict, not std
        std_val = metadata.get('std') if isinstance(metadata, dict) else metadata
        entry = {
            'iteration': int(eval_count),
            'energy': float(mean),
            'std': float(std_val) if std_val is not None else None,
        }
        convergence_trace.append(entry)
        if on_iteration:
            on_iteration(eval_count, float(mean))
        if eval_count % 20 == 0:
            logger.debug(f"VQE iter {eval_count}: energy={mean:.6f}")
    
    # Run VQE
    logger.info(f"VQE | Starting optimization with {optimizer}, maxiter={optimizer_maxiter}")
    vqe = VQE(estimator, ansatz, optimizer_instance, callback=callback)
    
    try:
        result = vqe.compute_minimum_eigenvalue(H)
    except Exception as e:
        logger.error(f"VQE failed: {e}")
        raise RuntimeError(f"VQE simulation failed: {e}") from e
    
    eigenvalue = float(result.eigenvalue.real)
    logger.info(f"VQE | Converged: energy={eigenvalue:.6f} "
                f"(reference={reference_energy:.6f})" if reference_energy else
                f"VQE | Converged: energy={eigenvalue:.6f}")
    
    return {
        'eigenvalue': eigenvalue,
        'reference_energy': reference_energy,
        'error_from_reference': abs(eigenvalue - reference_energy) if reference_energy else None,
        'optimal_parameters': result.optimal_point.tolist() if result.optimal_point is not None else [],
        'cost_function_evals': int(result.cost_function_evals or 0),
        'convergence_trace': convergence_trace,
        'circuit_stats': {
            'num_qubits': num_qubits,
            'depth': ansatz.depth(),
            'num_parameters': ansatz.num_parameters,
            'ansatz_type': ansatz_type,
            'ansatz_reps': ansatz_reps,
        },
        'entanglement_score': mw_score,
        'simulation_backend': str(sim.name) if sim else 'aer',
        'optimizer': optimizer,
        'hamiltonian_terms': len(h_list),
        'seed': seed,
    }


def run_vqe_stream(request: Dict, queue):
    """
    Run VQE and push convergence updates to a queue for SSE streaming.
    Call from a Celery task or asyncio background task.
    """
    def on_iter(eval_count, energy):
        queue.put({
            'type': 'vqe_progress',
            'eval_count': eval_count,
            'energy': energy,
        })
    
    result = run_vqe(**request, on_iteration=on_iter)
    queue.put({'type': 'vqe_complete', 'result': result})
