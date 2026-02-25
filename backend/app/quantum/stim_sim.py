"""Milimo Quantum — Stim Stabilizer Simulator.

Wrapper for Google Stim, a fast Clifford circuit + Pauli noise simulator.
Optimized for quantum error correction (QEC) simulations --
10-100x faster than general-purpose simulators for stabilizer circuits.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def is_stim_available() -> bool:
    """Check if Stim is installed."""
    try:
        import stim  # noqa: F401
        return True
    except ImportError:
        return False


def create_stabilizer_circuit(
    code_distance: int = 3,
    rounds: int = 1,
    noise_rate: float = 0.001,
) -> dict:
    """Create a surface code memory experiment circuit.

    Args:
        code_distance: Distance of the surface code (3, 5, 7, ...)
        rounds: Number of error correction rounds
        noise_rate: Depolarizing noise rate

    Returns:
        Circuit info dict with stats and Stim circuit string
    """
    try:
        import stim

        # Generate a repetition code circuit as a starting point
        circuit = stim.Circuit.generated(
            "repetition_code:memory",
            rounds=rounds,
            distance=code_distance,
            after_clifford_depolarization=noise_rate,
            after_reset_flip_probability=noise_rate,
            before_measure_flip_probability=noise_rate,
            before_round_data_depolarization=noise_rate,
        )

        return {
            "circuit_str": str(circuit),
            "num_qubits": circuit.num_qubits,
            "num_detectors": circuit.num_detectors,
            "num_observables": circuit.num_observables,
            "code_distance": code_distance,
            "rounds": rounds,
            "noise_rate": noise_rate,
        }
    except ImportError:
        return {"error": "Stim not installed. Install with: pip install stim"}
    except Exception as e:
        return {"error": str(e)}


def sample_stabilizer(
    circuit_str: str | None = None,
    code_distance: int = 3,
    rounds: int = 1,
    noise_rate: float = 0.001,
    shots: int = 10000,
) -> dict:
    """Sample detection events from a stabilizer circuit.

    Returns detection event statistics and logical error rate.
    """
    try:
        import stim
        import numpy as np

        if circuit_str:
            circuit = stim.Circuit(circuit_str)
        else:
            circuit = stim.Circuit.generated(
                "repetition_code:memory",
                rounds=rounds,
                distance=code_distance,
                after_clifford_depolarization=noise_rate,
            )

        # Sample detection events
        sampler = circuit.compile_detector_sampler()
        detection_events, observable_flips = sampler.sample(
            shots, separate_observables=True
        )

        # Calculate logical error rate
        logical_error_rate = float(np.mean(observable_flips))
        detection_rate = float(np.mean(detection_events))

        return {
            "shots": shots,
            "logical_error_rate": logical_error_rate,
            "detection_rate": detection_rate,
            "num_detectors": circuit.num_detectors,
            "num_observables": circuit.num_observables,
            "num_qubits": circuit.num_qubits,
            "distance": code_distance,
            "noise_rate": noise_rate,
            "error_suppression": noise_rate / max(logical_error_rate, 1e-10),
        }
    except ImportError:
        return {"error": "Stim not installed. Install with: pip install stim"}
    except Exception as e:
        return {"error": str(e)}


def decode_errors(
    code_distance: int = 3,
    rounds: int = 3,
    noise_rate: float = 0.01,
    shots: int = 10000,
) -> dict:
    """Run a full decode cycle: generate errors, detect, decode with MWPM.

    Uses PyMatching (if available) for minimum-weight perfect matching.
    """
    try:
        import stim
        import numpy as np

        circuit = stim.Circuit.generated(
            "repetition_code:memory",
            rounds=rounds,
            distance=code_distance,
            after_clifford_depolarization=noise_rate,
        )

        # Try PyMatching for MWPM decoding
        try:
            import pymatching

            detector_error_model = circuit.detector_error_model()
            matcher = pymatching.Matching.from_detector_error_model(detector_error_model)

            sampler = circuit.compile_detector_sampler()
            detection_events, observable_flips = sampler.sample(
                shots, separate_observables=True
            )

            predictions = matcher.decode_batch(detection_events)
            num_errors = int(np.sum(predictions != observable_flips))
            decoded_error_rate = num_errors / shots

            return {
                "decoder": "pymatching_mwpm",
                "shots": shots,
                "raw_logical_error_rate": float(np.mean(observable_flips)),
                "decoded_error_rate": decoded_error_rate,
                "correction_improvement": float(np.mean(observable_flips)) / max(decoded_error_rate, 1e-10),
                "distance": code_distance,
                "rounds": rounds,
                "noise_rate": noise_rate,
            }

        except ImportError:
            # Fall back to no decoder — just report raw error rates
            result = sample_stabilizer(
                code_distance=code_distance,
                rounds=rounds,
                noise_rate=noise_rate,
                shots=shots,
            )
            result["decoder"] = "none (install pymatching for MWPM decoding)"
            return result

    except ImportError:
        return {"error": "Stim not installed. Install with: pip install stim"}
    except Exception as e:
        return {"error": str(e)}


def threshold_scan(
    distances: list[int] | None = None,
    noise_rates: list[float] | None = None,
    shots: int = 5000,
) -> dict:
    """Scan error rates across distances and noise levels to find threshold.

    Returns a grid of logical error rates for plotting.
    """
    if distances is None:
        distances = [3, 5, 7]
    if noise_rates is None:
        noise_rates = [0.001, 0.005, 0.01, 0.02, 0.05]

    try:
        results = []
        for d in distances:
            for p in noise_rates:
                r = sample_stabilizer(
                    code_distance=d,
                    rounds=d,
                    noise_rate=p,
                    shots=shots,
                )
                results.append({
                    "distance": d,
                    "noise_rate": p,
                    "logical_error_rate": r.get("logical_error_rate", None),
                    "error": r.get("error", None),
                })

        return {"results": results, "distances": distances, "noise_rates": noise_rates}
    except Exception as e:
        return {"error": str(e)}
