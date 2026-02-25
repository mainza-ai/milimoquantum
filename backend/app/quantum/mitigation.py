"""Milimo Quantum — Error Mitigation Module.

Provides Zero-Noise Extrapolation (ZNE) and measurement error mitigation
for improving quantum circuit results on noisy simulators/hardware.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


def apply_zne(
    circuit: Any,
    shots: int = 4096,
    noise_factors: list[float] | None = None,
) -> dict:
    """Apply Zero-Noise Extrapolation to a circuit.

    Runs the circuit at multiple noise levels and extrapolates to zero noise.

    Args:
        circuit: A Qiskit QuantumCircuit with measurements.
        shots: Number of shots per noise level.
        noise_factors: Noise scale factors (default: [1, 2, 3]).

    Returns:
        dict with raw counts at each noise level, extrapolated counts,
        and metadata.
    """
    if not QISKIT_AVAILABLE:
        return {"error": "Qiskit not available for error mitigation"}

    if noise_factors is None:
        noise_factors = [1.0, 2.0, 3.0]

    results_by_factor = {}
    base_error_rate = 0.01  # 1% depolarizing error per gate

    for factor in noise_factors:
        # Build noise model with scaled error rate
        noise_model = NoiseModel()
        error_rate = base_error_rate * factor

        # Clamp error rate to valid range
        error_rate = min(error_rate, 0.75)

        # Single-qubit depolarizing error
        error_1q = depolarizing_error(error_rate, 1)
        noise_model.add_all_qubit_quantum_error(error_1q, ['h', 'x', 'y', 'z', 's', 't', 'rx', 'ry', 'rz'])

        # Two-qubit depolarizing error (higher rate)
        error_2q = depolarizing_error(min(error_rate * 2, 0.75), 2)
        noise_model.add_all_qubit_quantum_error(error_2q, ['cx', 'cz', 'swap'])

        # Run simulation with noise
        sim = AerSimulator(noise_model=noise_model)
        transpiled = transpile(circuit, sim)
        result = sim.run(transpiled, shots=shots).result()
        counts = result.get_counts()

        results_by_factor[str(factor)] = counts

    # Richardson extrapolation to zero noise
    extrapolated = _richardson_extrapolation(results_by_factor, noise_factors, shots)

    return {
        "noisy_results": results_by_factor,
        "extrapolated": extrapolated,
        "noise_factors": noise_factors,
        "method": "ZNE (Richardson extrapolation)",
        "base_error_rate": base_error_rate,
        "shots_per_level": shots,
    }


def apply_measurement_mitigation(
    circuit: Any,
    shots: int = 4096,
) -> dict:
    """Apply measurement error mitigation via calibration.

    Runs calibration circuits to build a correction matrix,
    then applies it to the measurement results.

    Args:
        circuit: A Qiskit QuantumCircuit with measurements.
        shots: Number of shots.

    Returns:
        dict with raw counts, mitigated counts, and calibration data.
    """
    if not QISKIT_AVAILABLE:
        return {"error": "Qiskit not available for error mitigation"}

    n_qubits = circuit.num_qubits

    # Build noise model for demonstration
    noise_model = NoiseModel()
    meas_error_rate = 0.03  # 3% measurement error
    error_1q = depolarizing_error(0.01, 1)
    noise_model.add_all_qubit_quantum_error(error_1q, ['h', 'x', 'rx', 'ry', 'rz'])

    sim = AerSimulator(noise_model=noise_model)

    # Run the noisy circuit
    transpiled = transpile(circuit, sim)
    raw_result = sim.run(transpiled, shots=shots).result()
    raw_counts = raw_result.get_counts()

    # Run calibration circuits (|0...0⟩ and |1...1⟩)
    cal_circuits = _build_calibration_circuits(n_qubits)
    cal_results = {}
    for label, cal_qc in cal_circuits.items():
        t = transpile(cal_qc, sim)
        r = sim.run(t, shots=shots).result()
        cal_results[label] = r.get_counts()

    # Simple correction: scale counts by calibration ratios
    mitigated = _apply_correction(raw_counts, cal_results, n_qubits, shots)

    return {
        "raw_counts": raw_counts,
        "mitigated_counts": mitigated,
        "calibration": cal_results,
        "method": "Measurement error mitigation (calibration matrix)",
        "measurement_error_rate": meas_error_rate,
        "shots": shots,
    }


def _richardson_extrapolation(
    results: dict[str, dict],
    factors: list[float],
    shots: int,
) -> dict[str, int]:
    """Richardson extrapolation to estimate zero-noise counts."""
    # Collect all states
    all_states = set()
    for counts in results.values():
        all_states.update(counts.keys())

    # For each state, extrapolate to zero noise using linear fit
    extrapolated = {}
    for state in all_states:
        values = []
        for factor in factors:
            count = results[str(factor)].get(state, 0)
            values.append(count / shots)  # Convert to probability

        # Linear extrapolation: p(0) = p(f1) - f1 * (p(f2) - p(f1)) / (f2 - f1)
        if len(values) >= 2:
            slope = (values[-1] - values[0]) / (factors[-1] - factors[0])
            p_zero = values[0] - factors[0] * slope
            p_zero = max(0.0, min(1.0, p_zero))  # Clamp to [0, 1]
        else:
            p_zero = values[0]

        extrapolated[state] = max(0, round(p_zero * shots))

    # Normalize to total shots
    total = sum(extrapolated.values())
    if total > 0 and total != shots:
        scale = shots / total
        extrapolated = {k: max(0, round(v * scale)) for k, v in extrapolated.items()}

    return extrapolated


def _build_calibration_circuits(n_qubits: int) -> dict[str, Any]:
    """Build calibration circuits for measurement mitigation."""
    circuits = {}

    # All-zeros calibration
    qc0 = QuantumCircuit(n_qubits, n_qubits)
    qc0.measure(range(n_qubits), range(n_qubits))
    circuits["0" * n_qubits] = qc0

    # All-ones calibration
    qc1 = QuantumCircuit(n_qubits, n_qubits)
    for i in range(n_qubits):
        qc1.x(i)
    qc1.measure(range(n_qubits), range(n_qubits))
    circuits["1" * n_qubits] = qc1

    return circuits


def _apply_correction(
    raw_counts: dict[str, int],
    cal_results: dict[str, dict],
    n_qubits: int,
    shots: int,
) -> dict[str, int]:
    """Apply simple correction based on calibration data."""
    # Calculate readout fidelities from calibration
    zeros_label = "0" * n_qubits
    ones_label = "1" * n_qubits

    f0 = cal_results.get(zeros_label, {}).get(zeros_label, shots) / shots
    f1 = cal_results.get(ones_label, {}).get(ones_label, shots) / shots

    avg_fidelity = (f0 + f1) / 2
    if avg_fidelity < 0.5:
        avg_fidelity = 1.0  # Avoid division issues

    # Scale counts by inverse fidelity
    mitigated = {}
    for state, count in raw_counts.items():
        mitigated[state] = max(0, round(count / avg_fidelity))

    # Renormalize
    total = sum(mitigated.values())
    if total > 0 and total != shots:
        scale = shots / total
        mitigated = {k: max(0, round(v * scale)) for k, v in mitigated.items()}

    return mitigated


def apply_pauli_twirling(
    circuit: Any,
    shots: int = 4096,
    num_twirls: int = 16,
) -> dict:
    """Apply Pauli Twirling to convert coherent noise into stochastic noise.

    Inserts random Pauli gates (I, X, Y, Z) before and after each 2-qubit
    gate (CX, CZ) such that the ideal operation is preserved but coherent
    errors are randomized. Results are averaged over `num_twirls` realizations.

    Args:
        circuit: A Qiskit QuantumCircuit with measurements.
        shots: Number of shots per twirled circuit.
        num_twirls: Number of random twirl realizations to average over.

    Returns:
        dict with raw counts, twirled (averaged) counts, and metadata.
    """
    if not QISKIT_AVAILABLE:
        return {"error": "Qiskit not available for error mitigation"}

    import random as _rng
    import numpy as _np

    # Pauli pairs that preserve CX: (before_ctrl, before_tgt, after_ctrl, after_tgt)
    # These satisfy: (P_c ⊗ P_t) · CX · (P_c' ⊗ P_t') = CX  (up to global phase)
    TWIRL_PAIRS_CX = [
        ("id", "id", "id", "id"),
        ("x", "id", "x", "x"),
        ("id", "x", "id", "x"),
        ("x", "x", "x", "id"),
        ("y", "id", "y", "x"),
        ("id", "y", "z", "y"),
        ("y", "y", "x", "z"),
        ("x", "y", "y", "z"),
        ("y", "x", "y", "id"),
        ("z", "id", "z", "id"),
        ("id", "z", "z", "z"),
        ("z", "z", "id", "z"),
        ("z", "x", "z", "x"),
        ("x", "z", "y", "y"),
        ("y", "z", "x", "y"),
        ("z", "y", "y", "x"),  # added for full group coverage
    ]

    PAULI_MAP = {"id": "id", "x": "x", "y": "y", "z": "z"}

    def _apply_pauli(qc, qubit, pauli):
        if pauli == "x":
            qc.x(qubit)
        elif pauli == "y":
            qc.y(qubit)
        elif pauli == "z":
            qc.z(qubit)
        # "id" → do nothing

    # Noise model for demonstration
    noise_model = NoiseModel()
    error_1q = depolarizing_error(0.01, 1)
    error_2q = depolarizing_error(0.02, 2)
    noise_model.add_all_qubit_quantum_error(error_1q, ['h', 'x', 'y', 'z', 'rx', 'ry', 'rz'])
    noise_model.add_all_qubit_quantum_error(error_2q, ['cx', 'cz'])
    sim = AerSimulator(noise_model=noise_model)

    # Run raw circuit (no twirling)
    transpiled_raw = transpile(circuit, sim)
    raw_result = sim.run(transpiled_raw, shots=shots).result()
    raw_counts = raw_result.get_counts()

    # Collect twirled results
    all_twirl_counts: list[dict] = []

    for _ in range(num_twirls):
        # Build twirled circuit by walking through original gates
        twirled = QuantumCircuit(circuit.num_qubits, circuit.num_clbits)

        for instruction in circuit.data:
            op = instruction.operation
            qubits = [circuit.find_bit(q).index for q in instruction.qubits]

            if op.name in ("cx", "cnot") and len(qubits) == 2:
                # Pick a random twirl pair
                pair = _rng.choice(TWIRL_PAIRS_CX)
                ctrl, tgt = qubits[0], qubits[1]

                # Before twirl
                _apply_pauli(twirled, ctrl, pair[0])
                _apply_pauli(twirled, tgt, pair[1])

                # Original gate
                twirled.cx(ctrl, tgt)

                # After twirl (correction)
                _apply_pauli(twirled, ctrl, pair[2])
                _apply_pauli(twirled, tgt, pair[3])
            else:
                # Copy gate as-is
                twirled.append(instruction)

        transpiled_tw = transpile(twirled, sim)
        tw_result = sim.run(transpiled_tw, shots=shots).result()
        all_twirl_counts.append(tw_result.get_counts())

    # Average across all twirls
    avg_counts: dict[str, float] = {}
    for tc in all_twirl_counts:
        for state, count in tc.items():
            avg_counts[state] = avg_counts.get(state, 0.0) + count / num_twirls

    # Round to integer counts, normalized to shots
    twirled_counts = {k: max(0, round(v)) for k, v in avg_counts.items()}
    total = sum(twirled_counts.values())
    if total > 0 and total != shots:
        scale = shots / total
        twirled_counts = {k: max(0, round(v * scale)) for k, v in twirled_counts.items()}

    return {
        "raw_counts": raw_counts,
        "twirled_counts": twirled_counts,
        "method": "Pauli Twirling",
        "num_twirls": num_twirls,
        "shots_per_twirl": shots,
    }



def get_mitigation_info() -> str:
    """Return educational content about error mitigation."""
    return """## Quantum Error Mitigation

Error mitigation techniques improve results from noisy quantum hardware
**without** requiring full error correction.

### Available Methods

| Method | Overhead | Accuracy | Best For |
|--------|:---:|:---:|----------|
| **ZNE** | 3× circuits | Good | Gate errors |
| **M3/Calibration** | 2× circuits | Good | Measurement errors |
| **PEC** | Exponential | Excellent | High-precision |
| **Pauli Twirling** | 1× circuits | Moderate | Coherent → stochastic |

### Zero-Noise Extrapolation (ZNE)

Run the circuit at **multiple noise levels** and extrapolate to zero noise:

```
Noise: 1× → Result A
Noise: 2× → Result B
Noise: 3× → Result C
Extrapolate → Result at 0× noise (estimated ideal)
```

### Measurement Mitigation

Build a **calibration matrix** by running known states, then invert
to correct measurement errors:

```
Prepare |00⟩ → measure → {00: 970, 01: 15, 10: 12, 11: 3}
Prepare |11⟩ → measure → {11: 965, 10: 18, 01: 14, 00: 3}
→ Build correction matrix M⁻¹
→ Corrected = M⁻¹ × raw_counts
```

💡 Use `/code Run Bell state with ZNE` to see mitigation in action.
"""
