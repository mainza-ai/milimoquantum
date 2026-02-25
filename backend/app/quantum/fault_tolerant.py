"""Milimo Quantum — Fault-Tolerant Circuit Simulator.

Simulates surface code lattices, logical qubit encoding, and resource estimation
for fault-tolerant quantum computing.
"""
from __future__ import annotations

import math
from typing import Dict, List, Literal, Tuple, Any

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister


# ── Surface Code Lattice Generator ─────────────────────
def generate_surface_code(distance: int = 3) -> QuantumCircuit:
    """Generate a rotated surface code lattice of distance d.

    Requires d^2 data qubits and (d^2 - 1) syndrome qubits.
    Total physical qubits: 2d^2 - 1.

    Args:
        distance: Code distance (must be odd, e.g., 3, 5, 7).

    Returns:
        QuantumCircuit representing the syndrome extraction cycle.
    """
    if distance % 2 == 0:
        raise ValueError("Distance must be an odd integer (3, 5, 7, ...)")

    num_data = distance * distance
    num_syndrome = num_data - 1
    total_qubits = num_data + num_syndrome

    qr = QuantumRegister(total_qubits, "q")
    cr = ClassicalRegister(num_syndrome, "syndrome")
    qc = QuantumCircuit(qr, cr, name=f"SurfaceCode_d{distance}")

    # Physical qubit layout (simplified 2D grid mapping)
    # Even indices = data qubits
    # Odd indices = syndrome qubits (measurements)

    # Initialize syndrome qubits to |+>
    # (X-stabilizers need |+>, Z-stabilizers need |0> -> H -> CNOT -> H)
    # For simplicity, we show the structure of interactions.

    # Apply Hadamard to all syndrome qubits to verify X-stabilizers
    syndrome_indices = [
        i for i in range(total_qubits) if i % 2 != 0 and i < total_qubits
    ]
    qc.h(syndrome_indices)

    # Entangle data and syndrome qubits (CNOT lattice)
    # This is a simplified "nearest neighbor" interaction pattern
    # In a real device, this depends on connectivity graph.
    for s_idx in syndrome_indices:
        # Connect to up/down/left/right neighbors if they exist
        neighbors = [s_idx - 1, s_idx + 1, s_idx - distance, s_idx + distance]
        for n_idx in neighbors:
            if 0 <= n_idx < total_qubits and n_idx not in syndrome_indices:
                qc.cx(s_idx, n_idx)

    # Measure syndrome qubits
    qc.h(syndrome_indices)
    qc.measure(syndrome_indices, range(len(syndrome_indices)))

    return qc


# ── Resource Estimation ────────────────────────────────
def estimate_resources(
    algorithm: Literal["shor", "grover", "chemistry"],
    problem_size: int,
    physical_error_rate: float = 1e-3,
) -> Dict[str, Any]:
    """Estimate physical resources needed for a logical algorithm.

    Based on Fowler et al. surface code threshold estimates.

    Args:
        algorithm: 'shor' (factoring), 'grover' (search), or 'chemistry'.
        problem_size: Input bits (Shor), search space bits (Grover), or spin-orbitals (chem).
        physical_error_rate: Gate error rate of physical qubits.

    Returns:
        Dictionary containing logical/physical qubit counts and code distance.
    """
    # 1. Determine required logical qubits
    if algorithm == "shor":
        # Shor's: ~2n + 2 logical qubits for n-bit integer
        logical_qubits = 2 * problem_size + 2
        # T-gate count ~ 48 * n^3 (simplified scaling)
        logical_gates = 48 * (problem_size**3)
    elif algorithm == "grover":
        logical_qubits = problem_size + 1
        # ~  (π/4) * √N iterations
        logical_gates = int((math.pi / 4) * math.sqrt(2**problem_size))
    elif algorithm == "chemistry":
        logical_qubits = problem_size  # 1 qubit per spin-orbital
        logical_gates = problem_size**4  # Naive Jordan-Wigner scaling
    else:
        raise ValueError("Unknown algorithm")

    # 2. Calculate required code distance d
    # We need logical error rate P_L < 1 / logical_gates
    target_logical_error = 1.0 / (logical_gates * 10)  # Safety factor 10

    # P_L approx 0.1 * (100 * p_phys)^((d+1)/2)
    # Inverting for d:
    # log(10 P_L) = ((d+1)/2) * log(100 * p_phys)
    numerator = math.log10(10 * target_logical_error)
    denominator = math.log10(100 * physical_error_rate)

    if denominator >= 0:
        # Error rate too high (> 1%), code doesn't work
        return {
            "error": "Physical error rate too high for error correction (threshold ~1%)"
        }

    d_float = 2 * (numerator / denominator) - 1
    distance = math.ceil(d_float)
    if distance % 2 == 0:
        distance += 1  # Must be odd
    
    distance = max(3, distance) # Minimum distance 3

    # 3. Calculate physical qubits
    # Surface code: 2d^2 physical qubits per logical qubit
    physical_per_logical = 2 * (distance**2)
    total_physical_qubits = logical_qubits * physical_per_logical

    return {
        "algorithm": algorithm,
        "problem_size": problem_size,
        "logical_qubits": logical_qubits,
        "logical_gates_approx": f"{logical_gates:.2e}",
        "code_distance": distance,
        "physical_qubits_per_logical": physical_per_logical,
        "total_physical_qubits": total_physical_qubits,
        "physical_error_rate": physical_error_rate,
        "target_logical_error": f"{target_logical_error:.2e}",
    }


# ── Threshold Analysis ─────────────────────────────────
def run_threshold_analysis(
    distances: List[int] = [3, 5, 7, 9], error_rates: List[float] = [1e-4, 1e-3, 5e-3, 1e-2]
) -> Dict[str, Any]:
    """Simulate logical error rates vs physical error rates for different distances.
    
    Returns data for plotting the threshold crossing.
    """
    results = {}

    for d in distances:
        d_results = []
        for p in error_rates:
            # Simplified analytical model for logical error rate P_L
            # P_L = A * (p / p_th)^((d+1)/2)
            # A ~ 0.1, p_th ~ 1% (0.01)
            p_th = 0.01
            p_L = 0.1 * ((p / p_th) ** ((d + 1) / 2))
            # Cap at 0.5 (max entropy)
            p_L = min(0.5, p_L)
            
            d_results.append({"physical_error": p, "logical_error": p_L})
        
        results[f"d={d}"] = d_results

    return {
        "distances": distances,
        "model": "Surface Code (Rotated)",
        "threshold_estimate": "1.0%",
        "data": results
    }
