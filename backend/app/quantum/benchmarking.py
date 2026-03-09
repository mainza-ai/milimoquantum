"""Milimo Quantum — Benchmarking Engine.

Run benchmarks to compare quantum vs classical performance and track QPU metrics.
"""
from __future__ import annotations

import time
import logging
from typing import Dict, Any, List

from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit
from qiskit.quantum_info import Statevector

from app.quantum.executor import execute_circuit, QISKIT_AVAILABLE
from app.db import get_session
from app.db.models import BenchmarkResult

logger = logging.getLogger(__name__)


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
        start_time_val = time.time()

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

        prep_time = time.time() - start_time_val

        # 2. Metrics (Classical Pre-calculation)
        metrics = {
            "width": qc.num_qubits,
            "depth": qc.depth(),
            "count_ops": dict(qc.count_ops()),
            "estimated_clops": 0, # Placeholder
        }

        # 3. Execution (Quantum)
        q_start = time.time()
        result_exec = execute_circuit(qc, shots=shots)
        q_time = time.time() - q_start

        # 4. Classical Simulation (Baseline Comparison)
        c_time = -1.0
        if size <= 20:
            c_start = time.time()
            try:
                # Naive statevector simulation as "classical baseline"
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

        # 6. Save to Persistent Database
        db_result = BenchmarkResult(
            benchmark_name=name,
            problem_size=size,
            backend=backend_name,
            shots=shots,
            preparation_time=prep_time,
            quantum_exec_time=q_time,
            classical_sim_time=c_time if c_time > 0 else None,
            classification=classification,
            metrics=metrics,
            result_summary="Success" if "counts" in result_exec else "Failed"
        )

        with get_session() as session:
            session.add(db_result)
            session.commit()
            session.refresh(db_result)
            
            # Return report as dict
            return {
                "id": db_result.id,
                "timestamp": db_result.timestamp.isoformat(),
                "benchmark": db_result.benchmark_name,
                "problem_size": db_result.problem_size,
                "backend": db_result.backend,
                "metrics": db_result.metrics,
                "timings": {
                    "preparation": round(db_result.preparation_time, 4),
                    "quantum_exec": round(db_result.quantum_exec_time, 4),
                    "classical_sim": round(db_result.classical_sim_time, 4) if db_result.classical_sim_time else None,
                },
                "classification": db_result.classification,
                "result_summary": db_result.result_summary
            }

    @staticmethod
    def get_history(limit: int = 50) -> List[Dict[str, Any]]:
        """Get past benchmark reports from database."""
        with get_session() as session:
            results = session.query(BenchmarkResult).order_by(BenchmarkResult.timestamp.desc()).limit(limit).all()
            return [
                {
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat(),
                    "benchmark": r.benchmark_name,
                    "problem_size": r.problem_size,
                    "backend": r.backend,
                    "metrics": r.metrics,
                    "timings": {
                        "preparation": round(r.preparation_time, 4),
                        "quantum_exec": round(r.quantum_exec_time, 4),
                        "classical_sim": round(r.classical_sim_time, 4) if r.classical_sim_time else None,
                    },
                    "classification": r.classification,
                    "result_summary": r.result_summary
                }
                for r in results
            ]
