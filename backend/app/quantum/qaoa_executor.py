"""
Real QAOA execution using Qiskit Aer SamplerV2.
"""
from __future__ import annotations

import logging
import numpy as np
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

try:
    from qiskit.quantum_info import SparsePauliOp
    from qiskit_aer.primitives import SamplerV2 as AerSamplerV2
    from qiskit_algorithms import QAOA
    from qiskit_algorithms.optimizers import COBYLA, SPSA
    from qiskit_algorithms.utils import algorithm_globals
    QAOA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"QAOA dependencies not available: {e}")
    QAOA_AVAILABLE = False

from .hal import select_aer_backend


def build_maxcut_hamiltonian(edges: List[tuple], num_nodes: int) -> 'SparsePauliOp':
    """
    Build Max-Cut cost Hamiltonian from graph edges.
    H = sum_{(i,j) in E} (I - Z_i Z_j) / 2
    """
    if not QAOA_AVAILABLE:
        raise ImportError("Qiskit not available for QAOA")
    
    terms = []
    for i, j in edges:
        pauli = ['I'] * num_nodes
        pauli[i] = 'Z'
        pauli[j] = 'Z'
        terms.append((''.join(reversed(pauli)), -0.5))
    terms.append(('I' * num_nodes, 0.5 * len(edges)))
    
    return SparsePauliOp.from_list(terms).simplify()


def run_qaoa(
    cost_hamiltonian: List[tuple] | str = 'maxcut',
    reps: int = 2,
    optimizer: str = 'cobyla',
    optimizer_maxiter: int = 200,
    seed: int = 42,
    edges: Optional[List[tuple]] = None,
    num_nodes: Optional[int] = None,
    on_iteration: Optional[callable] = None,
) -> Dict[str, Any]:
    """
    Run QAOA with Aer SamplerV2.

    Args:
        cost_hamiltonian: List of (pauli_str, coeff) tuples, or 'maxcut'.
        reps: QAOA circuit depth (p parameter).
        optimizer: 'cobyla' or 'spsa'.
        optimizer_maxiter: Maximum optimizer iterations.
        seed: Random seed.
        edges: For Max-Cut: list of (i, j) tuples.
        num_nodes: For Max-Cut: number of nodes.
        on_iteration: Optional callback for progress updates.
    """
    if not QAOA_AVAILABLE:
        return {'error': 'QAOA dependencies not available'}
    
    algorithm_globals.random_seed = seed
    
    # Build Hamiltonian
    if cost_hamiltonian == 'maxcut':
        if edges is None or num_nodes is None:
            raise ValueError("Max-Cut requires 'edges' and 'num_nodes'")
        H = build_maxcut_hamiltonian(edges, num_nodes)
    else:
        H = SparsePauliOp.from_list(cost_hamiltonian)
    
    num_qubits = H.num_qubits
    logger.info(f"QAOA | Hamiltonian: {num_qubits} qubits")
    
    # Create sampler
    sampler = AerSamplerV2()
    
    # Build optimizer
    if optimizer == 'cobyla':
        opt = COBYLA(maxiter=optimizer_maxiter)
    else:
        opt = SPSA(maxiter=optimizer_maxiter)
    
    # Convergence tracking
    convergence = []
    
    def callback(eval_count, params, mean, std):
        entry = {
            'iteration': int(eval_count),
            'cost': float(mean),
        }
        convergence.append(entry)
        if on_iteration:
            on_iteration(eval_count, float(mean))
    
    # Run QAOA
    logger.info(f"QAOA | Starting optimization with {optimizer}, reps={reps}")
    qaoa = QAOA(sampler, opt, reps=reps, callback=callback)
    
    try:
        result = qaoa.compute_minimum_eigenvalue(H)
    except Exception as e:
        logger.error(f"QAOA failed: {e}")
        return {'error': str(e)}
    
    eigenvalue = float(result.eigenvalue.real)
    logger.info(f"QAOA | Converged: eigenvalue={eigenvalue:.6f}")
    
    return {
        'eigenvalue': eigenvalue,
        'best_measurement': result.best_measurement if hasattr(result, 'best_measurement') else None,
        'optimal_parameters': result.optimal_point.tolist() if result.optimal_point is not None else [],
        'cost_function_evals': int(result.cost_function_evals or 0),
        'convergence_trace': convergence,
        'reps': reps,
        'optimizer': optimizer,
        'num_qubits': num_qubits,
    }
