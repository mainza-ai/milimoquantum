"""Milimo Quantum — Learning Academy Routes.

Provides structured quantum computing lessons with executable code examples.
Lesson content is stored inline for simplicity — no external files needed.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/academy", tags=["academy"])

PROGRESS_FILE = Path.home() / ".milimoquantum" / "academy_progress.json"


# ── Lesson Library ─────────────────────────────────────

LESSONS = [
    {
        "id": "qubits-and-gates",
        "title": "Qubits & Gates",
        "order": 1,
        "icon": "⚛️",
        "description": "Learn how quantum bits and gates work — the building blocks of quantum computing.",
        "difficulty": "beginner",
        "estimated_minutes": 10,
        "sections": [
            {
                "type": "text",
                "content": """## What is a Qubit?

A **qubit** is the quantum equivalent of a classical bit. While a classical bit is always 0 or 1, a qubit can be in a **superposition** of both states:

$$|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$$

where |α|² + |β|² = 1.

Think of it like a coin: a classical bit is either heads or tails, while a qubit is like a coin spinning in the air — it's both until you look at it."""
            },
            {
                "type": "text",
                "content": """## Quantum Gates

Quantum gates manipulate qubits, just like classical logic gates manipulate bits. The key difference: quantum gates are **reversible**.

| Gate | Effect | Symbol |
|------|--------|--------|
| **X** (NOT) | Flips |0⟩ ↔ |1⟩ | ≈ Classical NOT |
| **H** (Hadamard) | Creates superposition | No classical equivalent |
| **Z** (Phase) | Flips sign of |1⟩ | No classical equivalent |
| **CNOT** | Flips target if control = |1⟩ | ≈ Classical XOR |

The **Hadamard gate** is the most important single-qubit gate — it creates equal superposition:
$$H|0\\rangle = \\frac{|0\\rangle + |1\\rangle}{\\sqrt{2}}$$"""
            },
            {
                "type": "code",
                "title": "Try it: Superposition Circuit",
                "description": "This circuit puts a qubit in superposition and measures it. Run it to see ~50/50 results!",
                "code": """from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create a 1-qubit circuit
qc = QuantumCircuit(1, 1)
qc.h(0)          # Hadamard gate → superposition
qc.measure(0, 0) # Measure

# Simulate
sim = AerSimulator()
transpiled = transpile(qc, sim)
counts = sim.run(transpiled, shots=1024).result().get_counts()
print("Superposition results:", counts)
# Expected: ~50% '0' and ~50% '1'
"""
            },
            {
                "type": "quiz",
                "question": "After applying a Hadamard gate to |0⟩, what is the probability of measuring |1⟩?",
                "options": ["0%", "25%", "50%", "100%"],
                "correct": 2,
                "explanation": "The Hadamard gate creates equal superposition: H|0⟩ = (|0⟩ + |1⟩)/√2, so P(|1⟩) = |1/√2|² = 50%."
            }
        ],
    },
    {
        "id": "entanglement",
        "title": "Entanglement",
        "order": 2,
        "icon": "🔗",
        "description": "Discover quantum entanglement — Einstein's 'spooky action at a distance'.",
        "difficulty": "beginner",
        "estimated_minutes": 12,
        "sections": [
            {
                "type": "text",
                "content": """## Quantum Entanglement

When two qubits are **entangled**, measuring one instantly determines the state of the other, no matter how far apart they are.

The simplest entangled state is the **Bell State**:
$$|\\Phi^+\\rangle = \\frac{|00\\rangle + |11\\rangle}{\\sqrt{2}}$$

This means: both qubits are either **both 0** or **both 1** — but you don't know which until you measure."""
            },
            {
                "type": "code",
                "title": "Try it: Bell State Circuit",
                "description": "This creates a Bell state — the simplest entangled pair. Notice the results are only |00⟩ and |11⟩, never |01⟩ or |10⟩!",
                "code": """from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create a Bell State
qc = QuantumCircuit(2, 2)
qc.h(0)        # Superposition on qubit 0
qc.cx(0, 1)    # CNOT: entangle qubits 0 and 1
qc.measure([0, 1], [0, 1])

# Simulate
sim = AerSimulator()
transpiled = transpile(qc, sim)
counts = sim.run(transpiled, shots=1024).result().get_counts()
print("Bell State results:", counts)
# Expected: ~50% '00' and ~50% '11'
"""
            },
            {
                "type": "text",
                "content": """## All Four Bell States

There are 4 maximally entangled states for 2 qubits:

| Bell State | Formula | Circuit |
|-----------|---------|---------|
| |Φ+⟩ | (|00⟩ + |11⟩)/√2 | H + CNOT |
| |Φ−⟩ | (|00⟩ − |11⟩)/√2 | H + CNOT + Z |
| |Ψ+⟩ | (|01⟩ + |10⟩)/√2 | X + H + CNOT |
| |Ψ−⟩ | (|01⟩ − |10⟩)/√2 | X + H + CNOT + Z |

These are the foundation of quantum teleportation and quantum key distribution!"""
            },
            {
                "type": "quiz",
                "question": "If you measure the Bell state |Φ+⟩ and get |0⟩ on qubit A, what will qubit B be?",
                "options": ["|0⟩", "|1⟩", "Either (50/50)", "You can't predict"],
                "correct": 0,
                "explanation": "|Φ+⟩ = (|00⟩ + |11⟩)/√2 — qubits are correlated. If A = |0⟩, then B must be |0⟩ too."
            }
        ],
    },
    {
        "id": "quantum-algorithms",
        "title": "Quantum Algorithms",
        "order": 3,
        "icon": "🧮",
        "description": "Learn Grover's search algorithm — quadratic speedup for finding needles in haystacks.",
        "difficulty": "intermediate",
        "estimated_minutes": 15,
        "sections": [
            {
                "type": "text",
                "content": """## Why Quantum Algorithms?

Classical computers search unsorted data in **O(N)** time — check every item. Quantum computers can do it in **O(√N)** using **Grover's Algorithm**.

| Problem Size | Classical | Grover's |
|-------------|-----------|----------|
| 100 items | ~100 checks | ~10 checks |
| 1 million | ~1M checks | ~1000 checks |
| 1 billion | ~1B checks | ~31,623 checks |

### How Grover's Works
1. **Initialize**: equal superposition over all states
2. **Oracle**: mark the target with a phase flip
3. **Diffusion**: amplify marked state's probability
4. **Repeat** √N times
5. **Measure**: high probability of finding the target"""
            },
            {
                "type": "code",
                "title": "Try it: Grover's Search (2 Qubits)",
                "description": "This searches for |11⟩ among 4 possible states using Grover's algorithm.",
                "code": """from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# 2-qubit Grover's searching for |11⟩
qc = QuantumCircuit(2, 2)

# Step 1: Initialize superposition
qc.h([0, 1])

# Step 2: Oracle — mark |11⟩ with phase flip
qc.cz(0, 1)  # CZ flips phase when both qubits are |1⟩

# Step 3: Diffusion operator
qc.h([0, 1])
qc.z([0, 1])
qc.cz(0, 1)
qc.h([0, 1])

# Measure
qc.measure([0, 1], [0, 1])

sim = AerSimulator()
transpiled = transpile(qc, sim)
counts = sim.run(transpiled, shots=1024).result().get_counts()
print("Grover's Search results:", counts)
# Expected: |11⟩ with high probability
"""
            },
            {
                "type": "quiz",
                "question": "How many iterations does Grover's algorithm need to search 1 million items?",
                "options": ["~100", "~1,000", "~500,000", "~1,000,000"],
                "correct": 1,
                "explanation": "Grover's needs ~√N iterations. √1,000,000 = 1,000."
            }
        ],
    },
    {
        "id": "error-correction",
        "title": "Error Correction",
        "order": 4,
        "icon": "🛡️",
        "description": "Understand why quantum computers need error correction and how it works.",
        "difficulty": "intermediate",
        "estimated_minutes": 15,
        "sections": [
            {
                "type": "text",
                "content": """## The Noise Problem

Real quantum computers suffer from **decoherence** — qubits lose their quantum properties over time. Error rates are ~0.1-1% per gate, compared to ~10⁻¹⁵ for classical computers.

**Solution:** Encode 1 logical qubit across multiple physical qubits, so errors can be detected and corrected.

### The Simplest Code: 3-Qubit Bit-Flip Code
Encode |0⟩ → |000⟩ and |1⟩ → |111⟩. If one qubit flips, majority vote corrects it:
- |000⟩ → |010⟩ (error on qubit 1) → majority vote → |000⟩ ✓"""
            },
            {
                "type": "code",
                "title": "Try it: 3-Qubit Bit-Flip Code",
                "description": "This demonstrates encoding, introducing an error, and correcting it.",
                "code": """from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# 3-qubit bit-flip error correction
qc = QuantumCircuit(5, 3)  # 3 data qubits + 2 ancilla

# Step 1: Encode |0⟩ → |000⟩ (using CNOT)
qc.cx(0, 1)
qc.cx(0, 2)
qc.barrier()

# Step 2: Introduce a bit-flip error on qubit 1
qc.x(1)  # Simulated error!
qc.barrier()

# Step 3: Syndrome measurement
qc.cx(0, 3)  # Compare q0 and q1
qc.cx(1, 3)
qc.cx(1, 4)  # Compare q1 and q2
qc.cx(2, 4)
qc.barrier()

# Step 4: Correction (based on syndrome)
qc.ccx(3, 4, 1)  # If both ancillas flag → fix q1
qc.barrier()

# Measure data qubits
qc.measure([0, 1, 2], [0, 1, 2])

sim = AerSimulator()
transpiled = transpile(qc, sim)
counts = sim.run(transpiled, shots=1024).result().get_counts()
print("Error Correction results:", counts)
# Expected: '000' (error corrected!)
"""
            },
            {
                "type": "quiz",
                "question": "How many physical qubits does a distance-3 surface code use per logical qubit?",
                "options": ["3", "7", "9", "17"],
                "correct": 2,
                "explanation": "A distance-3 surface code uses d² = 9 data qubits (plus ancillas for syndrome measurement)."
            }
        ],
    },
    {
        "id": "applications",
        "title": "Real Applications",
        "order": 5,
        "icon": "🚀",
        "description": "Explore real-world quantum applications: VQE for chemistry, QAOA for optimization, QKD for security.",
        "difficulty": "intermediate",
        "estimated_minutes": 15,
        "sections": [
            {
                "type": "text",
                "content": """## Quantum Applications Today

Quantum computing isn't just theoretical — it has real applications being developed right now:

| Application | Algorithm | Status |
|------------|-----------|--------|
| **Drug Discovery** | VQE (Variational Quantum Eigensolver) | Active research |
| **Optimization** | QAOA, Quantum Annealing | Commercial products |
| **Cybersecurity** | QKD (BB84, E91) | Deployed in production |
| **Machine Learning** | QNN, QSVM | Early research |
| **Finance** | Portfolio optimization, Monte Carlo | Pilots at banks |"""
            },
            {
                "type": "code",
                "title": "Try it: QAOA for Max-Cut",
                "description": "This uses QAOA to solve a graph optimization problem — finding the best way to split nodes into two groups.",
                "code": """from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np

# QAOA for Max-Cut on a 4-node cycle graph
# Edges: (0,1), (1,2), (2,3), (3,0)
n = 4
edges = [(0,1), (1,2), (2,3), (3,0)]
gamma, beta = 0.7, 0.5  # QAOA parameters

qc = QuantumCircuit(n, n)

# Initial superposition
for i in range(n):
    qc.h(i)

# Cost layer: ZZ interaction for each edge
for (i, j) in edges:
    qc.rzz(2 * gamma, i, j)

# Mixer layer: X rotation
for i in range(n):
    qc.rx(2 * beta, i)

qc.measure(range(n), range(n))

sim = AerSimulator()
transpiled = transpile(qc, sim)
counts = sim.run(transpiled, shots=1024).result().get_counts()

# Find the best cut
print("QAOA Max-Cut results:")
for bitstring, count in sorted(counts.items(), key=lambda x: -x[1])[:5]:
    cut_value = sum(1 for (i,j) in edges if bitstring[i] != bitstring[j])
    print(f"  {bitstring}: {count} shots, cut value = {cut_value}")
"""
            },
            {
                "type": "quiz",
                "question": "What does VQE (Variational Quantum Eigensolver) primarily compute?",
                "options": [
                    "The shortest path in a graph",
                    "The ground state energy of a molecule",
                    "Random numbers",
                    "Encryption keys"
                ],
                "correct": 1,
                "explanation": "VQE finds the minimum eigenvalue (ground state energy) of a molecular Hamiltonian — critical for drug discovery and materials science."
            }
        ],
    },
]


# ── API Endpoints ──────────────────────────────────────

def _load_progress() -> dict:
    """Load user progress from disk."""
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"completed": [], "quiz_scores": {}}


def _save_progress(data: dict):
    """Save user progress to disk."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


@router.get("/lessons")
async def list_lessons():
    """List all available lessons with progress status."""
    progress = _load_progress()
    lessons = []
    for lesson in sorted(LESSONS, key=lambda x: x["order"]):
        lessons.append({
            "id": lesson["id"],
            "title": lesson["title"],
            "icon": lesson["icon"],
            "description": lesson["description"],
            "difficulty": lesson["difficulty"],
            "estimated_minutes": lesson["estimated_minutes"],
            "order": lesson["order"],
            "completed": lesson["id"] in progress.get("completed", []),
            "quiz_score": progress.get("quiz_scores", {}).get(lesson["id"]),
        })
    return {"lessons": lessons}


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str):
    """Get full lesson content by ID."""
    for lesson in LESSONS:
        if lesson["id"] == lesson_id:
            progress = _load_progress()
            return {
                **lesson,
                "completed": lesson_id in progress.get("completed", []),
                "quiz_score": progress.get("quiz_scores", {}).get(lesson_id),
            }
    raise HTTPException(status_code=404, detail=f"Lesson '{lesson_id}' not found")


@router.post("/progress")
async def save_progress(lesson_id: str, completed: bool = True, quiz_score: int | None = None):
    """Save user progress for a lesson."""
    progress = _load_progress()

    if completed and lesson_id not in progress["completed"]:
        progress["completed"].append(lesson_id)

    if quiz_score is not None:
        progress.setdefault("quiz_scores", {})[lesson_id] = quiz_score

    _save_progress(progress)
    return {"status": "saved", "progress": progress}
