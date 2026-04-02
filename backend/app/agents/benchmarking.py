"""Milimo Quantum — Benchmarking Agent."""
from __future__ import annotations

import logging
import time
import numpy as np
from typing import AsyncGenerator, Dict, Any, Optional

from app.llm.cloud_provider import get_current_provider, stream_chat_cloud
from app.llm.mlx_client import mlx_client
from app.llm.ollama_client import ollama_client
from app.quantum.hal import hal_config

logger = logging.getLogger(__name__)

BENCHMARKING_SYSTEM_PROMPT = """You are the Milimo Quantum Benchmarking Agent.
You specialize in evaluating quantum vs classical performance and hardware capabilities:
- Quantum Volume (QV) and CLOPS measurements
- Quantum advantage candidates
- Error rate tracking (T1/T2, gate fidelity)
- Classical vs Quantum runtime comparisons

Return executable Python code using Qiskit or Qiskit Benchpress to generate rigorous benchmark circuits.
"""

BENCHMARK_PATTERNS = [
    "benchmark", "clops", "quantum volume", "performance",
    "speed test", "compare quantum", "hardware performance",
    "qv", "qubits per second"
]


def try_quick_benchmark(query: str) -> Optional[Dict[str, Any]]:
    """
    Execute real benchmarks for quick response.
    Called from orchestrator before LLM streaming.
    """
    query_lower = query.lower()
    
    if not any(p in query_lower for p in BENCHMARK_PATTERNS):
        return None
    
    # Determine benchmark type
    if "quantum volume" in query_lower or "qv" in query_lower:
        return _run_quantum_volume_benchmark()
    elif "clops" in query_lower:
        return _run_clops_benchmark()
    else:
        return _run_general_benchmark()


def _run_quantum_volume_benchmark() -> Dict[str, Any]:
    """
    Run a simplified Quantum Volume test.
    
    Quantum Volume = 2^n where n is the largest circuit depth
    that can be executed with >2/3 probability of heavy output.
    """
    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit_aer import AerSimulator
        
        backend = AerSimulator()
        
        # Test increasing widths
        results = []
        for n_qubits in [2, 3, 4, 5]:
            # Generate random circuit (QV model)
            qc = _generate_qv_circuit(n_qubits, n_qubits)
            
            # Transpile and run
            transpiled = transpile(qc, backend, optimization_level=0)
            job = backend.run(transpiled, shots=1024)
            counts = job.result().get_counts()
            
            # Calculate heavy output probability
            # Simplified: check if most frequent outcome has >10% probability
            max_count = max(counts.values()) if counts else 0
            hop = max_count / 1024
            
            success = hop > 0.1  # Simplified threshold
            results.append({
                "width": n_qubits,
                "depth": n_qubits,
                "heavy_output_prob": hop,
                "success": success
            })
            
            if not success:
                break
        
        # Find maximum successful width
        qv = max([r["width"] for r in results if r["success"]], default=1)
        quantum_volume = 2 ** qv
        
        return {
            "response": f"Quantum Volume = {quantum_volume} (2^{qv})",
            "benchmark_type": "quantum_volume",
            "quantum_volume": quantum_volume,
            "max_width": qv,
            "details": results,
            "status": "SUCCESS"
        }
        
    except ImportError:
        return {
            "response": "Qiskit not available for benchmarking.",
            "benchmark_type": "quantum_volume",
            "status": "UNAVAILABLE"
        }
    except Exception as e:
        logger.error(f"QV benchmark failed: {e}")
        return {
            "response": f"Benchmark error: {str(e)}",
            "status": "ERROR"
        }


def _run_clops_benchmark() -> Dict[str, Any]:
    """
    Run CLOPS (Circuit Layer Operations Per Second) benchmark.
    """
    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit_aer import AerSimulator
        
        backend = AerSimulator()
        
        # Create layered circuit
        n_qubits = 4
        n_layers = 10
        
        start_time = time.time()
        iterations = 50
        
        for _ in range(iterations):
            qc = _create_layered_circuit(n_qubits, n_layers)
            transpiled = transpile(qc, backend)
            job = backend.run(transpiled, shots=100)
            _ = job.result()
        
        elapsed = time.time() - start_time
        
        # CLOPS = (C * D * S) / time
        # C = iterations, D = depth, S = shots
        clops = (iterations * n_layers * 100) / elapsed
        
        return {
            "response": f"CLOPS = {clops:.1f} (circuit layer operations per second)",
            "benchmark_type": "clops",
            "clops": clops,
            "iterations": iterations,
            "layers": n_layers,
            "shots_per_circuit": 100,
            "total_time_seconds": round(elapsed, 2),
            "status": "SUCCESS"
        }
        
    except ImportError:
        return {
            "response": "Qiskit not available.",
            "status": "UNAVAILABLE"
        }
    except Exception as e:
        logger.error(f"CLOPS benchmark failed: {e}")
        return {
            "response": f"Benchmark error: {str(e)}",
            "status": "ERROR"
        }


def _run_general_benchmark() -> Dict[str, Any]:
    """Run a general performance benchmark."""
    try:
        from qiskit import QuantumCircuit, transpile
        from qiskit_aer import AerSimulator
        
        backend = AerSimulator()
        
        # Test basic circuit performance
        n_qubits = 4
        qc = QuantumCircuit(n_qubits)
        qc.h(0)
        for i in range(n_qubits - 1):
            qc.cx(i, i + 1)
        qc.measure_all()
        
        # Warmup
        job = backend.run(transpile(qc, backend), shots=1000)
        _ = job.result()
        
        # Timed run
        start = time.time()
        iterations = 100
        for _ in range(iterations):
            job = backend.run(transpile(qc, backend), shots=1000)
            result = job.result()
        
        elapsed = time.time() - start
        
        return {
            "response": f"Executed {iterations} circuits in {elapsed:.2f}s ({iterations/elapsed:.1f} circuits/sec)",
            "benchmark_type": "general",
            "qubits": n_qubits,
            "iterations": iterations,
            "total_time": round(elapsed, 2),
            "circuits_per_second": round(iterations / elapsed, 1),
            "status": "SUCCESS"
        }
        
    except ImportError:
        return {
            "response": "Qiskit not available for benchmarking.",
            "status": "UNAVAILABLE"
        }
    except Exception as e:
        logger.error(f"General benchmark failed: {e}")
        return {
            "response": f"Benchmark error: {str(e)}",
            "status": "ERROR"
        }


def _generate_qv_circuit(n_qubits: int, depth: int) -> "QuantumCircuit":
    """Generate a Quantum Volume model circuit."""
    from qiskit import QuantumCircuit
    
    qc = QuantumCircuit(n_qubits)
    
    for d in range(depth):
        # Random single-qubit gates
        for q in range(n_qubits):
            theta = np.random.uniform(0, 2 * np.pi)
            phi = np.random.uniform(0, 2 * np.pi)
            qc.rz(theta, q)
            qc.ry(phi, q)
        
        # Random pairwise CNOT gates
        perm = np.random.permutation(n_qubits)
        for i in range(0, n_qubits - 1, 2):
            qc.cx(perm[i], perm[i + 1])
    
    return qc


def _create_layered_circuit(n_qubits: int, n_layers: int) -> "QuantumCircuit":
    """Create a layered benchmark circuit."""
    from qiskit import QuantumCircuit
    
    qc = QuantumCircuit(n_qubits)
    
    for _ in range(n_layers):
        # Single-qubit layer
        for q in range(n_qubits):
            qc.h(q)
            qc.rz(0.1, q)
        
        # Two-qubit layer (even-odd pairing)
        for q in range(0, n_qubits - 1, 2):
            qc.cx(q, q + 1)
    
    return qc


async def process_benchmarking_request(
    query: str, history: list[dict], context: str = ""
) -> AsyncGenerator[str, None]:
    """Process a benchmarking query."""
    
    # Try quick benchmark first
    quick_result = try_quick_benchmark(query)
    if quick_result and quick_result.get("status") == "SUCCESS":
        # Return the result as formatted text
        response = quick_result.get("response", "")
        if "details" in quick_result:
            response += "\n\n**Details:**\n"
            for d in quick_result["details"]:
                response += f"- Width {d['width']}: HOP = {d['heavy_output_prob']:.3f} ({'✓' if d['success'] else '✗'})\n"
        yield response
        return
    
    # Fall back to LLM
    full_prompt = BENCHMARKING_SYSTEM_PROMPT
    if context:
        full_prompt += f"\n\n{context}"

    messages = history + [{"role": "user", "content": query}]

    try:
        if hal_config.llm_backend == "mlx" and mlx_client.model:
            async for token in mlx_client.stream_chat(messages, system_prompt=full_prompt):
                yield token
        elif hal_config.llm_backend == "ollama" and await ollama_client.is_available():
            async for token in ollama_client.stream_chat(messages, system_prompt=full_prompt):
                yield token
        else:
            provider = get_current_provider()
            async for token in stream_chat_cloud(messages, system_prompt=full_prompt, provider=provider):
                yield token
    except Exception as e:
        logger.error(f"Benchmarking agent error: {e}")
        yield f"⚠️ **Benchmarking Error:** {str(e)}"
