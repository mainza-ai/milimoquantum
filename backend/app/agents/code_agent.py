"""Milimo Quantum — Code Agent.

Generates Qiskit code and executes quantum circuits.
"""
from __future__ import annotations

import re

from app.quantum.executor import (
    CIRCUIT_LIBRARY,
    QISKIT_AVAILABLE,
    execute_circuit,
)
from app.models.schemas import Artifact, ArtifactType


# Quick circuit patterns the code agent can handle directly
QUICK_CIRCUITS = {
    "bell": "bell",
    "bell state": "bell",
    "ghz": "ghz",
    "ghz state": "ghz",
    "ghz 5": "ghz5",
    "qft": "qft",
    "fourier": "qft",
    "quantum fourier": "qft",
}


def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    """Try to match a quick circuit request and execute it."""
    if not QISKIT_AVAILABLE:
        return [], None

    lower = message.lower().strip()

    # Check for known circuit patterns
    for pattern, circuit_key in QUICK_CIRCUITS.items():
        if pattern in lower:
            name, factory = CIRCUIT_LIBRARY[circuit_key]
            circuit = factory()
            if circuit is None:
                continue

            result = execute_circuit(circuit, shots=1024)
            if "error" in result and result["error"]:
                continue

            # Generate code artifact
            code = _generate_code_for_circuit(circuit_key)
            artifacts = []

            if code:
                artifacts.append(Artifact(
                    type=ArtifactType.CODE,
                    title=f"{name} — Qiskit Code",
                    content=code,
                    language="python",
                ))

            if result.get("circuit_svg"):
                artifacts.append(Artifact(
                    type=ArtifactType.CIRCUIT,
                    title=f"{name} — Circuit Diagram",
                    content=result["circuit_svg"],
                ))

            if result.get("counts"):
                import json
                artifacts.append(Artifact(
                    type=ArtifactType.RESULTS,
                    title=f"{name} — Measurement Results",
                    content=json.dumps(result["counts"]),
                    metadata={
                        "shots": result["shots"],
                        "execution_time_ms": result["execution_time_ms"],
                        "backend": result["backend"],
                        "num_qubits": result["num_qubits"],
                        "depth": result["depth"],
                    },
                ))

            # Build summary message
            top_counts = sorted(result["counts"].items(), key=lambda x: -x[1])[:5]
            counts_str = ", ".join(f"`{k}`: {v}" for k, v in top_counts)
            summary = (
                f"## {name}\n\n"
                f"I've created and executed the circuit using Qiskit Aer.\n\n"
                f"**Circuit:** {result['num_qubits']} qubits, depth {result['depth']}\n"
                f"**Shots:** {result['shots']}\n"
                f"**Backend:** `{result['backend']}`\n"
                f"**Time:** {result['execution_time_ms']}ms\n\n"
                f"**Top Results:** {counts_str}\n\n"
                f"Check the artifact panel for the full code, circuit diagram, and measurement histogram."
            )
            return artifacts, summary

    return [], None


def _generate_code_for_circuit(circuit_key: str) -> str:
    """Generate clean Qiskit code for a named circuit."""
    templates = {
        "bell": '''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create a Bell State circuit — maximally entangled pair
qc = QuantumCircuit(2, 2)
qc.h(0)          # Put qubit 0 in superposition |+⟩
qc.cx(0, 1)      # CNOT: entangle qubit 0 and 1
qc.measure([0, 1], [0, 1])

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
job = simulator.run(transpiled, shots=1024)
result = job.result()
counts = result.get_counts()

print("Bell State Results:", counts)
# Expected: ~50% |00⟩ and ~50% |11⟩
''',
        "ghz": '''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create a GHZ State — 3-qubit entanglement
qc = QuantumCircuit(3, 3)
qc.h(0)          # Superposition on qubit 0
qc.cx(0, 1)      # Entangle qubit 0 → 1
qc.cx(0, 2)      # Entangle qubit 0 → 2
qc.measure([0, 1, 2], [0, 1, 2])

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
job = simulator.run(transpiled, shots=1024)
result = job.result()
counts = result.get_counts()

print("GHZ State Results:", counts)
# Expected: ~50% |000⟩ and ~50% |111⟩
''',
        "ghz5": '''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create a 5-qubit GHZ State
qc = QuantumCircuit(5, 5)
qc.h(0)
for i in range(1, 5):
    qc.cx(0, i)
qc.measure(range(5), range(5))

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
job = simulator.run(transpiled, shots=1024)
result = job.result()
counts = result.get_counts()

print("5-qubit GHZ Results:", counts)
# Expected: ~50% |00000⟩ and ~50% |11111⟩
''',
        "qft": '''from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import QFT
from qiskit_aer import AerSimulator

# Create a Quantum Fourier Transform circuit
n = 3
qc = QuantumCircuit(n, n)
qc.append(QFT(n), range(n))
qc.measure(range(n), range(n))

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
job = simulator.run(transpiled, shots=1024)
result = job.result()
counts = result.get_counts()

print("QFT Results:", counts)
''',
    }
    return templates.get(circuit_key, "")
