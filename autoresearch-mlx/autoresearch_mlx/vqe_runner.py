"""
Local VQE runner for autoresearch-mlx.
Directly uses qiskit_aer — no HTTP calls to the backend.
Mirrors the interface of vqe_executor.py in the main backend.
"""
from __future__ import annotations

import logging
import numpy as np
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

try:
    from qiskit.quantum_info import SparsePauliOp, Statevector
    from qiskit.circuit.library import EfficientSU2, RealAmplitudes, TwoLocal
    from qiskit_aer import AerSimulator
    from qiskit_aer.primitives import EstimatorV2 as AerEstimatorV2
    from qiskit_algorithms import VQE
    from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver
    from qiskit_algorithms.optimizers import SPSA, COBYLA, L_BFGS_B, SLSQP
    from qiskit_algorithms.utils import algorithm_globals
    from qiskit import transpile
    QISKIT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Qiskit not available: {e}")
    QISKIT_AVAILABLE = False

# Predefined Hamiltonians (keep in sync with backend vqe_executor)
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
    ],
    'lih_exact': -7.882,
}

# Ansatz catalog
ANSATZ_CATALOG = {
    'efficient_su2': lambda n, r: EfficientSU2(n, reps=r),
    'real_amplitudes': lambda n, r: RealAmplitudes(n, reps=r),
    'two_local_ry_cz': lambda n, r: TwoLocal(n, ['ry'], 'cz', reps=r),
    'two_local_ryrz_cz': lambda n, r: TwoLocal(n, ['ry', 'rz'], 'cz', reps=r),
}

# Optimizer catalog
OPTIMIZER_CATALOG = {
    'spsa': lambda m: SPSA(maxiter=m),
    'cobyla': lambda m: COBYLA(maxiter=m),
    'l_bfgs_b': lambda m: L_BFGS_B(maxiter=m),
    'slsqp': lambda m: SLSQP(maxiter=m),
}


def meyer_wallach_score(circuit) -> float:
    """Meyer-Wallach global entanglement score."""
    if not QISKIT_AVAILABLE:
        return 0.5
    
    n = circuit.num_qubits
    bound = (circuit.assign_parameters(np.random.uniform(0, 2*np.pi, circuit.num_parameters))
             if circuit.num_parameters > 0 else circuit)
    arr = Statevector(bound).data.reshape([2] * n)
    Q = sum(
        2.0 * (1.0 - float(np.real(np.trace(
            (rho := np.tensordot(arr, arr.conj(),
                                 axes=([i for i in range(n) if i != k],
                                       [i for i in range(n) if i != k]))) @ rho
        ))))
        for k in range(n)
    )
    return Q / n


def run_vqe_local(
    hamiltonian: str = 'h2',
    ansatz_type: str = 'real_amplitudes',
    ansatz_reps: int = 2,
    optimizer: str = 'spsa',
    optimizer_maxiter: int = 300,
    seed: int = 42,
    on_iteration: Optional[Callable] = None,
    **kwargs
) -> Dict[str, Any]:
    """Run VQE locally with Aer simulation."""
    
    if not QISKIT_AVAILABLE:
        return {
            'error': 'Qiskit not available',
            'eigenvalue': None,
        }
    
    algorithm_globals.random_seed = seed
    
    # Get Hamiltonian
    h_list = HAMILTONIANS.get(hamiltonian, hamiltonian)
    if isinstance(h_list, float):
        raise ValueError(f"Cannot use {hamiltonian}_exact as hamiltonian - use the list version")
    
    H = SparsePauliOp.from_list(h_list)
    n = H.num_qubits
    
    # Build ansatz
    ansatz = ANSATZ_CATALOG[ansatz_type](n, ansatz_reps)
    # Decompose to basic gates for Aer
    _tmp_sim = AerSimulator(method='statevector')
    ansatz = transpile(ansatz, backend=_tmp_sim, optimization_level=1)
    mw = meyer_wallach_score(ansatz)
    
    # Classical reference
    ref = NumPyMinimumEigensolver().compute_minimum_eigenvalue(H)
    ref_energy = float(ref.eigenvalue.real)
    
    # Setup simulation
    sim = AerSimulator(method='statevector' if n <= 24 else 'matrix_product_state')
    estimator = AerEstimatorV2()
    opt = OPTIMIZER_CATALOG[optimizer](optimizer_maxiter)
    
    # Convergence tracking
    convergence = []

    def callback(i, p, m, metadata):
        # In qiskit-algorithms 0.4+, the 4th arg is metadata dict
        convergence.append({'i': int(i), 'e': float(m)})
        if on_iteration:
            on_iteration(int(i), float(m))
    
    # Run VQE
    vqe = VQE(estimator, ansatz, opt, callback=callback)
    result = vqe.compute_minimum_eigenvalue(H)
    ev = float(result.eigenvalue.real)
    
    return {
        'eigenvalue': ev,
        'reference_energy': ref_energy,
        'error_from_reference': abs(ev - ref_energy),
        'optimal_parameters': result.optimal_point.tolist(),
        'cost_function_evals': int(result.cost_function_evals or 0),
        'convergence_trace': convergence,
        'circuit_stats': {
            'num_qubits': n,
            'depth': ansatz.depth(),
            'num_parameters': ansatz.num_parameters,
            'ansatz_type': ansatz_type,
            'ansatz_reps': ansatz_reps,
        },
        'entanglement_score': mw,
        'simulation_backend': sim.name,
        'optimizer': optimizer,
        'hamiltonian_terms': len(h_list),
        'seed': seed,
    }
