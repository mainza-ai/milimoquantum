"""Milimo Quantum — Noise Model Profiles.

Provides realistic noise models based on real device calibration data.
Supports IBM-style backends with T1/T2 times, gate errors, and readout errors.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ── Calibration Profiles ──────────────────────────────────
# Based on publicly available IBM calibration data (indicative values).
DEVICE_PROFILES: dict[str, dict[str, Any]] = {
    "ibm_brisbane": {
        "num_qubits": 127,
        "t1_us": 250.0,
        "t2_us": 150.0,
        "gate_error_1q": 2.5e-4,
        "gate_error_2q": 7.5e-3,
        "readout_error": 1.2e-2,
        "gate_time_1q_ns": 60,
        "gate_time_2q_ns": 660,
        "processor": "Eagle r3",
    },
    "ibm_osaka": {
        "num_qubits": 127,
        "t1_us": 280.0,
        "t2_us": 180.0,
        "gate_error_1q": 2.2e-4,
        "gate_error_2q": 6.8e-3,
        "readout_error": 1.0e-2,
        "gate_time_1q_ns": 56,
        "gate_time_2q_ns": 640,
        "processor": "Eagle r3",
    },
    "ibm_torino": {
        "num_qubits": 133,
        "t1_us": 300.0,
        "t2_us": 200.0,
        "gate_error_1q": 1.8e-4,
        "gate_error_2q": 5.5e-3,
        "readout_error": 8.0e-3,
        "gate_time_1q_ns": 50,
        "gate_time_2q_ns": 580,
        "processor": "Heron r2",
    },
    "ideal": {
        "num_qubits": 127,
        "t1_us": float("inf"),
        "t2_us": float("inf"),
        "gate_error_1q": 0.0,
        "gate_error_2q": 0.0,
        "readout_error": 0.0,
        "gate_time_1q_ns": 0,
        "gate_time_2q_ns": 0,
        "processor": "Ideal (noiseless)",
    },
}


def list_profiles() -> list[dict]:
    """List all available noise profiles."""
    return [
        {
            "name": name,
            "num_qubits": p["num_qubits"],
            "processor": p["processor"],
            "gate_error_2q": p["gate_error_2q"],
            "readout_error": p["readout_error"],
        }
        for name, p in DEVICE_PROFILES.items()
    ]


def get_profile(name: str) -> dict | None:
    """Get detailed calibration data for a device."""
    return DEVICE_PROFILES.get(name)


def build_noise_model(profile_name: str, num_qubits: int | None = None) -> Any | None:
    """Build a Qiskit NoiseModel from a calibration profile.

    Returns a NoiseModel object or None if Qiskit Aer is not available.
    """
    profile = DEVICE_PROFILES.get(profile_name)
    if not profile:
        logger.error(f"Unknown profile: {profile_name}")
        return None

    if profile_name == "ideal":
        return None  # No noise for ideal

    try:
        from qiskit_aer.noise import NoiseModel
        from qiskit_aer.noise.errors import (
            depolarizing_error,
            thermal_relaxation_error,
            ReadoutError,
        )

        n_qubits = num_qubits or min(profile["num_qubits"], 20)  # cap for sim
        noise_model = NoiseModel()

        # Single-qubit gate error (depolarizing + thermal relaxation)
        for qubit in range(n_qubits):
            # Thermal relaxation
            t1 = profile["t1_us"] * 1e3  # convert to ns
            t2 = min(profile["t2_us"] * 1e3, 2 * t1)  # T2 <= 2*T1
            gate_time = profile["gate_time_1q_ns"]

            if t1 > 0 and t2 > 0 and gate_time > 0:
                thermal_err = thermal_relaxation_error(t1, t2, gate_time)
                noise_model.add_quantum_error(
                    thermal_err, ["u1", "u2", "u3", "x", "h", "s", "t", "rz", "sx"], [qubit]
                )

            # Readout error
            p0_given_1 = profile["readout_error"]
            p1_given_0 = profile["readout_error"] * 0.8  # asymmetric
            readout_err = ReadoutError(
                [[1 - p1_given_0, p1_given_0], [p0_given_1, 1 - p0_given_1]]
            )
            noise_model.add_readout_error(readout_err, [qubit])

        # Two-qubit gate error (depolarizing)
        cx_err = depolarizing_error(profile["gate_error_2q"], 2)
        noise_model.add_all_qubit_quantum_error(cx_err, ["cx", "cz", "ecr"])

        logger.info(f"Built noise model for {profile_name} ({n_qubits} qubits)")
        return noise_model

    except ImportError:
        logger.warning("qiskit_aer not available for noise model construction")
        return None
    except Exception as e:
        logger.error(f"Failed to build noise model: {e}")
        return None


def execute_with_noise(
    circuit: Any, profile_name: str, shots: int = 4096
) -> dict:
    """Execute a circuit with a specific noise profile.

    Returns counts + noise metadata.
    """
    try:
        from qiskit_aer import AerSimulator

        noise_model = build_noise_model(profile_name, circuit.num_qubits)
        backend = AerSimulator(noise_model=noise_model) if noise_model else AerSimulator()

        from qiskit import transpile

        transpiled = transpile(circuit, backend)
        job = backend.run(transpiled, shots=shots)
        result = job.result()
        counts = result.get_counts()

        profile = DEVICE_PROFILES.get(profile_name, {})
        return {
            "counts": counts,
            "shots": shots,
            "noise_profile": profile_name,
            "processor": profile.get("processor", "unknown"),
            "gate_error_2q": profile.get("gate_error_2q", 0),
            "readout_error": profile.get("readout_error", 0),
            "noisy": noise_model is not None,
        }
    except Exception as e:
        return {"error": str(e)}
