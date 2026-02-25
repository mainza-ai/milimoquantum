"""Milimo Quantum — Research Agent.

Handles quantum computing educational queries with rich formatting.
"""
from __future__ import annotations


# Quick-reference knowledge base for common quantum topics
QUICK_TOPICS: dict[str, str] = {
    "superposition": """## Quantum Superposition

A quantum bit (qubit) can exist in a **superposition** of states — simultaneously in both |0⟩ and |1⟩:

$$|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$$

where |α|² + |β|² = 1

**Key Points:**
- Unlike a classical bit (0 or 1), a qubit can be "both" until measured
- The **Hadamard gate** (H) creates equal superposition: H|0⟩ = (|0⟩ + |1⟩)/√2
- Upon measurement, the superposition collapses to |0⟩ or |1⟩ with probabilities |α|² and |β|²

**In Qiskit:**
```python
from qiskit import QuantumCircuit
qc = QuantumCircuit(1)
qc.h(0)  # Creates superposition
```

💡 *Try it*: `/code Create a circuit that puts a qubit in superposition and measures it`
""",

    "entanglement": """## Quantum Entanglement

Two qubits are **entangled** when their quantum states are correlated — measuring one instantly determines the other, regardless of distance.

The **Bell State** is the simplest entangled state:

$$|\\Phi^+\\rangle = \\frac{1}{\\sqrt{2}}(|00\\rangle + |11\\rangle)$$

**Key Points:**
- Created with a Hadamard + CNOT gate
- Einstein called it "spooky action at a distance"
- Foundation of quantum teleportation, quantum key distribution, and quantum error correction
- Not faster-than-light communication — no usable info without classical channel

**In Qiskit:**
```python
qc = QuantumCircuit(2)
qc.h(0)       # Superposition
qc.cx(0, 1)   # Entangle
```

💡 *Try it*: `/circuit Create a Bell state`
""",

    "qubit": """## What is a Qubit?

A **qubit** (quantum bit) is the fundamental unit of quantum information.

| Classical Bit | Qubit |
|---|---|
| 0 or 1 | α|0⟩ + β|1⟩ |
| Deterministic | Probabilistic until measured |
| Copied freely | No-cloning theorem |

**Physical Realizations:**
- **Superconducting** (IBM, Google): Josephson junctions cooled to 15 mK
- **Trapped Ion** (Quantinuum, IonQ): Individual atoms held by electromagnetic fields
- **Neutral Atom** (QuEra): Arrays of atoms manipulated by lasers
- **Photonic** (PsiQuantum, Xanadu): Photon polarization states

**Bloch Sphere:** A qubit's state can be visualized on a sphere where:
- North pole = |0⟩
- South pole = |1⟩
- Equator = superposition states
""",
}

# Keywords mapping to topics
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "superposition": ["superposition", "superpose"],
    "entanglement": ["entangle", "entanglement", "bell state", "epr", "spooky"],
    "qubit": ["qubit", "what is a qubit", "quantum bit"],
}


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick topic from the knowledge base."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None
