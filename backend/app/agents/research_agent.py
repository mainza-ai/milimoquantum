"""Milimo Quantum — Research Agent.

Handles quantum computing educational queries with rich formatting.
Supports configurable explanation levels and comprehensive topic coverage.
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

    "gates": """## Quantum Gates

Quantum gates manipulate qubits through unitary transformations. Unlike classical logic gates, they are **reversible**.

### Single-Qubit Gates

| Gate | Matrix | Effect |
|------|--------|--------|
| **X** (NOT) | $\\begin{pmatrix}0&1\\\\1&0\\end{pmatrix}$ | Flips |0⟩ ↔ |1⟩ |
| **H** (Hadamard) | $\\frac{1}{\\sqrt{2}}\\begin{pmatrix}1&1\\\\1&-1\\end{pmatrix}$ | Creates superposition |
| **Z** (Phase) | $\\begin{pmatrix}1&0\\\\0&-1\\end{pmatrix}$ | Adds phase to |1⟩ |
| **T** (π/8) | $\\begin{pmatrix}1&0\\\\0&e^{i\\pi/4}\\end{pmatrix}$ | π/4 phase, key for fault tolerance |
| **Rz(θ)** | $\\begin{pmatrix}e^{-i\\theta/2}&0\\\\0&e^{i\\theta/2}\\end{pmatrix}$ | Z-axis rotation |

### Multi-Qubit Gates
- **CNOT** (CX): Flips target if control is |1⟩ — foundation of entanglement
- **Toffoli** (CCX): 3-qubit AND gate — universal for classical computation
- **SWAP**: Exchanges two qubit states
- **CZ**: Phase gate applied if both qubits are |1⟩

### Universal Gate Sets
{H, T, CNOT} can approximate any unitary to arbitrary precision. This is the basis of quantum universality.

💡 *Try it*: `/code Create a circuit using H, CNOT, and T gates`
""",

    "error_correction": """## Quantum Error Correction

Quantum computers must fight **decoherence** — the loss of quantum information to the environment. Error correction encodes a logical qubit across multiple physical qubits.

### Key Codes
| Code | Physical Qubits | Distance | Notes |
|------|-----------------|----------|-------|
| **Shor [[9,1,3]]** | 9 | 3 | First QEC code, corrects 1 error |
| **Steane [[7,1,3]]** | 7 | 3 | CSS code, transversal Clifford gates |
| **Surface Code** | O(d²) | d | Leading candidate for real hardware |
| **Color Code** | O(d²) | d | Transversal T-gate (unlike surface) |

### Error Types
- **Bit flip** (X error): |0⟩ → |1⟩ — corrected by repetition code
- **Phase flip** (Z error): |+⟩ → |−⟩ — corrected in Hadamard basis
- **General error**: Any combination of X, Y, Z — corrected by full QEC

### Logical Error Rate Formula
$$p_L \\approx \\left(\\frac{p}{p_{th}}\\right)^{\\lfloor d/2 \\rfloor + 1}$$

where $p$ = physical error rate, $p_{th}$ = threshold (~0.6% for surface code), $d$ = code distance.

💡 *Try it*: `/code Simulate a 3-qubit bit-flip error correction code`
""",

    "algorithms": """## Quantum Algorithms

### Key Algorithms and Speedups

| Algorithm | Problem | Speedup | Qubits Needed |
|-----------|---------|---------|---------------|
| **Shor's** | Integer factoring | Exponential (O(n³) vs exp) | ~2n+3 |
| **Grover's** | Unstructured search | Quadratic (O(√N) vs O(N)) | log₂(N) |
| **VQE** | Ground state energy | Quantum advantage for molecules | ~2 per orbital |
| **QAOA** | Combinatorial optimization | Potential advantage | Problem-dependent |
| **QPE** | Phase estimation | Exponential for eigenvalues | ~n + precision |
| **QML** | Machine learning | Problem-dependent | Variable |

### Grover's Algorithm — How It Works
1. **Initialize**: Apply H to all qubits → equal superposition
2. **Oracle**: Marks the target state with a phase flip
3. **Diffusion**: Amplifies the marked state's amplitude
4. Repeat steps 2-3 approximately $\\frac{\\pi}{4}\\sqrt{N}$ times
5. **Measure**: High probability of finding the target

### NISQ vs Fault-Tolerant
- **NISQ era** (now): 50-1000 noisy qubits. VQE, QAOA, QML feasible.
- **Fault-tolerant era** (future): Millions of physical qubits. Shor's, full QPE feasible.

💡 *Try it*: `/code Implement Grover's algorithm for a 3-qubit search`
""",

    "supremacy": """## Quantum Supremacy / Advantage

**Quantum supremacy** = demonstrating a quantum computer performing a task no classical computer can do in reasonable time.

### Historical Milestones
| Year | Team | Qubits | Claim |
|------|------|--------|-------|
| 2019 | Google (Sycamore) | 53 | Random circuit sampling in 200s vs est. 10,000 years classical |
| 2020 | USTC (Jiuzhang) | 76 photons | Gaussian Boson Sampling |
| 2023 | IBM (Eagle) | 127 | Utility-scale advantage for physics simulation |
| 2024 | Google (Willow) | 105 | Below-threshold error correction |

### Controversy
- IBM challenged Google's 10,000-year estimate (showed classical simulation in 2.5 days)
- Supremacy ≠ useful computation (random circuit sampling has no practical application)
- **Quantum advantage** (useful speedup) may be the more important milestone

### Current Frontiers
- **Quantum utility**: IBM's 2023 demonstration showed quantum hardware producing results that are hard to simulate classically AND useful for physics
- **Error correction threshold**: Google's Willow chip crossed below the surface code threshold
""",
}

# Keywords mapping to topics
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "superposition": ["superposition", "superpose", "wave function"],
    "entanglement": ["entangle", "entanglement", "bell state", "epr", "spooky"],
    "qubit": ["qubit", "what is a qubit", "quantum bit", "bloch sphere"],
    "gates": ["gate", "hadamard", "cnot", "toffoli", "pauli", "rotation", "unitary"],
    "error_correction": ["error correction", "qec", "surface code", "fault tolerant",
                         "decoherence", "stabilizer", "logical qubit", "shor code", "steane"],
    "algorithms": ["algorithm", "shor", "grover", "vqe", "qaoa", "qpe",
                   "search algorithm", "factoring", "quantum advantage"],
    "supremacy": ["supremacy", "advantage", "sycamore", "beyond classical",
                  "utility", "quantum utility"],
}

# ── Explain Levels ──────────────────────────────────────

EXPLAIN_LEVELS = {
    "beginner": "Explain simply, use analogies, avoid math notation. Target audience: high school student.",
    "intermediate": "Use proper quantum notation (ket, bra, Dirac). Include equations. Target: physics undergraduate.",
    "expert": "Full mathematical treatment with density matrices, Kraus operators, and complexity analysis. Target: graduate researcher.",
}


def detect_explain_level(message: str) -> str:
    """Detect the desired explanation level from the message."""
    lower = message.lower()
    if any(kw in lower for kw in ["simple", "beginner", "easy", "eli5", "basic"]):
        return "beginner"
    if any(kw in lower for kw in ["expert", "advanced", "detailed", "rigorous", "formal"]):
        return "expert"
    return "intermediate"


def get_system_prompt_suffix(level: str) -> str:
    """Get system prompt suffix for the explain level."""
    return EXPLAIN_LEVELS.get(level, EXPLAIN_LEVELS["intermediate"])


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick topic from the knowledge base."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None
