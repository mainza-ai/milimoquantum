"""Milimo Quantum — Code Agent.

Generates Qiskit code and executes quantum circuits.
Handles both quick-match patterns AND dynamic circuit generation.
"""
from __future__ import annotations

import json
import re

from app.quantum.executor import (
    CIRCUIT_LIBRARY,
    QISKIT_AVAILABLE,
    execute_circuit,
    create_ghz_state,
    create_qft_circuit,
    create_bell_state,
)
from app.models.schemas import Artifact, ArtifactType


# ── Quick pattern → exact circuit ─────────────────────────
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


def _extract_qubit_count(message: str) -> int | None:
    """Extract number of qubits from a message like '5 qubit circuit'."""
    patterns = [
        r"(\d+)\s*[-\s]?qubit",       # "5 qubit", "5-qubit"
        r"(\d+)\s*[-\s]?qubit",       # same
        r"n\s*=\s*(\d+)",             # "n=5"
        r"with\s+(\d+)\s+qubit",      # "with 5 qubits"
        r"(\d+)\s+q\b",               # "5 q"
    ]
    for pat in patterns:
        m = re.search(pat, message, re.IGNORECASE)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 20:
                return n
    return None


def _detect_circuit_type(message: str) -> str:
    """Detect what kind of circuit the user wants."""
    lower = message.lower()

    # Specific circuit types
    if any(kw in lower for kw in ["ghz", "greenberger"]):
        return "ghz"
    if any(kw in lower for kw in ["qft", "fourier"]):
        return "qft"
    if any(kw in lower for kw in ["bell", "epr"]):
        return "bell"
    if any(kw in lower for kw in ["entangle", "entanglement"]):
        return "entanglement"
    if any(kw in lower for kw in ["superposition", "hadamard"]):
        return "superposition"
    if any(kw in lower for kw in ["random", "general"]):
        return "random"
    if any(kw in lower for kw in ["grover", "search"]):
        return "grover"

    # Generic "circuit" request
    return "generic"


def _build_dynamic_circuit(circuit_type: str, n_qubits: int):
    """Build a circuit dynamically based on type and qubit count."""
    if not QISKIT_AVAILABLE:
        return None, "", ""

    from qiskit import QuantumCircuit

    if circuit_type == "ghz":
        circuit = create_ghz_state(n_qubits)
        name = f"GHZ State ({n_qubits} qubits)"
        code = _ghz_code(n_qubits)
        return circuit, name, code

    elif circuit_type == "qft":
        circuit = create_qft_circuit(n_qubits)
        name = f"Quantum Fourier Transform ({n_qubits} qubits)"
        code = _qft_code(n_qubits)
        return circuit, name, code

    elif circuit_type == "bell":
        circuit = create_bell_state()
        name = "Bell State (2 qubits)"
        code = _bell_code()
        return circuit, name, code

    elif circuit_type == "entanglement":
        # Linear entanglement chain
        qc = QuantumCircuit(n_qubits, n_qubits)
        qc.h(0)
        for i in range(n_qubits - 1):
            qc.cx(i, i + 1)
        qc.measure(range(n_qubits), range(n_qubits))
        name = f"Entanglement Chain ({n_qubits} qubits)"
        code = _entanglement_code(n_qubits)
        return qc, name, code

    elif circuit_type == "superposition":
        qc = QuantumCircuit(n_qubits, n_qubits)
        for i in range(n_qubits):
            qc.h(i)
        qc.measure(range(n_qubits), range(n_qubits))
        name = f"Uniform Superposition ({n_qubits} qubits)"
        code = _superposition_code(n_qubits)
        return qc, name, code

    elif circuit_type == "random":
        import random
        qc = QuantumCircuit(n_qubits, n_qubits)
        gates = ['h', 'x', 'y', 'z', 's', 't']
        # Layer 1: random single-qubit gates
        for i in range(n_qubits):
            gate = random.choice(gates)
            getattr(qc, gate)(i)
        # Layer 2: entangling gates
        for i in range(0, n_qubits - 1, 2):
            qc.cx(i, i + 1)
        # Layer 3: more random gates
        for i in range(n_qubits):
            gate = random.choice(gates)
            getattr(qc, gate)(i)
        qc.measure(range(n_qubits), range(n_qubits))
        name = f"Random Circuit ({n_qubits} qubits)"
        code = _random_code(n_qubits)
        return qc, name, code

    else:
        # Generic: GHZ is a good default for N-qubit circuits
        circuit = create_ghz_state(n_qubits)
        name = f"Quantum Circuit ({n_qubits} qubits)"
        code = _ghz_code(n_qubits)
        return circuit, name, code


def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    """Try to match a circuit request and execute it.

    Handles:
    1. Exact named patterns (bell, ghz, qft)
    2. Dynamic N-qubit circuits ("create a 5 qubit circuit")
    3. Circuit-type detection ("entanglement circuit with 4 qubits")
    """
    if not QISKIT_AVAILABLE:
        return [], None

    lower = message.lower().strip()

    # ── Step 1: Check exact named patterns ──────────────
    for pattern, circuit_key in QUICK_CIRCUITS.items():
        if pattern in lower:
            name, factory = CIRCUIT_LIBRARY[circuit_key]
            circuit = factory()
            if circuit is None:
                continue

            result = execute_circuit(circuit, shots=1024)
            if result.get("error"):
                continue

            code = _generate_code_for_circuit(circuit_key)
            return _build_artifacts(name, code, result)

    # ── Step 2: Dynamic circuit generation ──────────────
    # Check if the message is asking for a circuit
    circuit_keywords = [
        "circuit", "qubit", "quantum", "entangle", "superposition",
        "hadamard", "create", "generate", "build", "make", "run",
        "execute", "simulate", "grover", "random",
    ]
    is_circuit_request = any(kw in lower for kw in circuit_keywords)

    if is_circuit_request:
        n_qubits = _extract_qubit_count(message) or 3  # default to 3
        circuit_type = _detect_circuit_type(message)

        circuit, name, code = _build_dynamic_circuit(circuit_type, n_qubits)
        if circuit is None:
            return [], None

        result = execute_circuit(circuit, shots=1024)
        if result.get("error"):
            return [], None

        return _build_artifacts(name, code, result)

    return [], None


def _build_artifacts(name: str, code: str, result: dict) -> tuple[list[Artifact], str]:
    """Build artifact list and summary from execution result."""
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
            content=code,
            metadata={
                "ascii_diagram": result["circuit_svg"],
                "num_qubits": result.get("num_qubits"),
                "depth": result.get("depth"),
            }
        ))

    if result.get("counts"):
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

    # Build summary
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


def _generate_code_for_circuit(circuit_key: str) -> str:
    """Generate clean Qiskit code for a named circuit."""
    templates = {
        "bell": _bell_code(),
        "ghz": _ghz_code(3),
        "ghz5": _ghz_code(5),
        "qft": _qft_code(3),
    }
    return templates.get(circuit_key, "")


# ── Code Templates ──────────────────────────────────────

def _bell_code() -> str:
    return '''from qiskit import QuantumCircuit, transpile
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
'''


def _ghz_code(n: int) -> str:
    return f'''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create a {n}-qubit GHZ State — multi-qubit entanglement
n = {n}
qc = QuantumCircuit(n, n)
qc.h(0)          # Superposition on qubit 0
for i in range(1, n):
    qc.cx(0, i)  # Entangle qubit 0 → i
qc.measure(range(n), range(n))

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
job = simulator.run(transpiled, shots=1024)
result = job.result()
counts = result.get_counts()

print(f"{n}-qubit GHZ State Results:", counts)
# Expected: ~50% |{"0" * n}⟩ and ~50% |{"1" * n}⟩
'''


def _qft_code(n: int) -> str:
    return f'''from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import QFT
from qiskit_aer import AerSimulator

# Create a {n}-qubit Quantum Fourier Transform circuit
n = {n}
qc = QuantumCircuit(n, n)
qc.append(QFT(n), range(n))
qc.measure(range(n), range(n))

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
job = simulator.run(transpiled, shots=1024)
result = job.result()
counts = result.get_counts()

print(f"{n}-qubit QFT Results:", counts)
'''


def _entanglement_code(n: int) -> str:
    return f'''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create a {n}-qubit linear entanglement chain
n = {n}
qc = QuantumCircuit(n, n)
qc.h(0)          # Superposition on first qubit
for i in range(n - 1):
    qc.cx(i, i + 1)  # CNOT chain: entangle neighbors
qc.measure(range(n), range(n))

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
job = simulator.run(transpiled, shots=1024)
result = job.result()
counts = result.get_counts()

print(f"{n}-qubit Entanglement Chain Results:", counts)
'''


def _superposition_code(n: int) -> str:
    return f'''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create a {n}-qubit uniform superposition (all Hadamards)
n = {n}
qc = QuantumCircuit(n, n)
for i in range(n):
    qc.h(i)      # Hadamard on each qubit
qc.measure(range(n), range(n))

# Simulate — should produce all 2^n states with equal probability
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
job = simulator.run(transpiled, shots=1024)
result = job.result()
counts = result.get_counts()

print(f"{n}-qubit Superposition Results:", counts)
print(f"Expected: ~{{1024 // (2**n)}} counts per state")
'''


def _random_code(n: int) -> str:
    return f'''import random
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create a {n}-qubit random quantum circuit
n = {n}
qc = QuantumCircuit(n, n)

# Layer 1: Random single-qubit gates
gates = ['h', 'x', 'y', 'z', 's', 't']
for i in range(n):
    gate = random.choice(gates)
    getattr(qc, gate)(i)

# Layer 2: Entangling CNOT gates
for i in range(0, n - 1, 2):
    qc.cx(i, i + 1)

# Layer 3: More random gates
for i in range(n):
    gate = random.choice(gates)
    getattr(qc, gate)(i)

qc.measure(range(n), range(n))

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
job = simulator.run(transpiled, shots=1024)
result = job.result()
counts = result.get_counts()

print(f"{n}-qubit Random Circuit Results:", counts)
'''
