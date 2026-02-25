"""Milimo Quantum — Benchmarking Engine.

Run benchmarks to compare quantum vs classical performance and track QPU metrics.
"""
from __future__ import annotations

import time
import random
import logging
import datetime
from typing import Dict, Any, List

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.random import random_circuit
from qiskit.quantum_info import Statevector

from app.quantum.executor import execute_circuit, QISKIT_AVAILABLE

logger = logging.getLogger(__name__)

BENCHMARK_HISTORY = []


class BenchmarkEngine:
    """Engine for running quantum-classical performance comparisons."""

    @staticmethod
    def run_benchmark(
        name: str,
        size: int,
        shots: int = 1024,
        backend_name: str = "aer_simulator"
    ) -> Dict[str, Any]:
        """Run a benchmark comparison.

        Args:
            name: Benchmark type ('random_circuit', 'grover_search', 'qft').
            size: Problem size (qubits).
            shots: Number of shots.
            backend_name: Backend to usage.
        """
        if not QISKIT_AVAILABLE:
            return {"error": "Qiskit not installed"}

        logger.info(f"Running benchmark: {name} (n={size})")
        start_time = time.time()

        # 1. Prepare Circuit
        qc = None
        if name == "random_circuit":
            depth = size * size
            qc = random_circuit(size, depth, measure=True)
        elif name == "qft":
            from qiskit.circuit.library import QFT
            qc = QFT(size, do_swaps=True).decompose()
            qc.measure_all()
        elif name == "grover":
             # Simplified Grover dummy for benchmarking
             qc = QuantumCircuit(size)
             qc.h(range(size))
             qc.measure_all()
        else:
             return {"error": f"Unknown benchmark type: {name}"}

        prep_time = time.time() - start_time

        # 2. Metrics (Classical Pre-calculation)
        metrics = {
            "width": qc.num_qubits,
            "depth": qc.depth(),
            "count_ops": dict(qc.count_ops()),
            "estimated_clops": 0, # Placeholder
        }

        # 3. Execution (Quantum)
        q_start = time.time()
        result = execute_circuit(qc, shots=shots)
        q_time = time.time() - q_start

        # 4. Classical Simulation (Baseline Comparison)
        # For small circuits (<20 qubits), we can simulate exact statevector
        c_time = -1.0
        if size <= 20:
            c_start = time.time()
            try:
                # Naive statevector simulation as "classical baseline"
                # Remove measurements for statevector
                qc_no_meas = qc.remove_final_measurements(inplace=False)
                Statevector(qc_no_meas)
            except Exception:
                pass
            c_time = time.time() - c_start
        
        # 5. Advantage Classification
        classification = "classical_superior"
        if q_time < c_time and c_time > 0:
            classification = "quantum_advantage" 
        elif c_time < 0:
             classification = "quantum_only" # Too big for classical

        report = {
            "id": f"bench_{int(start_time)}",
            "timestamp": datetime.datetime.now().isoformat(),
            "benchmark": name,
            "problem_size": size,
            "backend": backend_name,
            "metrics": metrics,
            "timings": {
                "preparation": round(prep_time, 4),
                "quantum_exec": round(q_time, 4),
                "classical_sim": round(c_time, 4) if c_time > 0 else None,
            },
            "classification": classification,
            "result_summary": "Success" if "counts" in result else "Failed"
        }

        BENCHMARK_HISTORY.append(report)
        return report

    @staticmethod
    def get_history(limit: int = 50) -> List[Dict[str, Any]]:
        """Get past benchmark reports."""
        return sorted(BENCHMARK_HISTORY, key=lambda x: x["timestamp"], reverse=True)[:limit]
