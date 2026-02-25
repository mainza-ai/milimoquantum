"""Milimo Quantum — Chemistry Agent.

Handles quantum chemistry, molecular simulation, and drug discovery queries.
Phase 2: Template-based with educational knowledge base.
"""
from __future__ import annotations

from app.models.schemas import Artifact, ArtifactType


# ── Quick-reference knowledge base ──────────────────────
QUICK_TOPICS: dict[str, str] = {
    "vqe": """## Variational Quantum Eigensolver (VQE)

VQE finds the **ground-state energy** of a molecule — the lowest energy configuration
of its electrons. This is crucial for drug discovery and materials science.

### How It Works

1. **Encode the molecule** as a qubit Hamiltonian via Jordan-Wigner or Bravyi-Kitaev mapping
2. **Prepare a trial state** using a parameterized ansatz (e.g., EfficientSU2, UCCSD)
3. **Measure energy** ⟨ψ(θ)|H|ψ(θ)⟩ on a quantum computer
4. **Classically optimize** parameters θ to minimize energy
5. **Repeat** until convergence

$$E_0 \\leq \\langle \\psi(\\theta)|H|\\psi(\\theta) \\rangle$$

### Molecules Simulated with VQE

| Molecule | Qubits | Use Case |
|----------|--------|----------|
| H₂ | 2–4 | Benchmark |
| LiH | 4–12 | Battery materials |
| HeH⁺ | 2–4 | Astrophysics |
| H₂O | 8–14 | Chemical bonding |
| BeH₂ | 6–14 | Industrial chemistry |

### Qiskit Implementation Pattern

```python
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import COBYLA
from qiskit.circuit.library import EfficientSU2

ansatz = EfficientSU2(num_qubits=4, reps=2)
optimizer = COBYLA(maxiter=500)
vqe = VQE(ansatz=ansatz, optimizer=optimizer)
```

💡 *Try it*: `/code Create a VQE circuit for H2`
""",

    "hamiltonian": """## Molecular Hamiltonian Construction

The electronic Hamiltonian describes a molecule's energy in terms of electron interactions:

$$H = \\sum_{pq} h_{pq} a^\\dagger_p a_q + \\frac{1}{2} \\sum_{pqrs} h_{pqrs} a^\\dagger_p a^\\dagger_q a_s a_r$$

### Mapping to Qubits

| Method | Qubit Cost | Gate Cost | Best For |
|--------|-----------|-----------|----------|
| **Jordan-Wigner** | N qubits | O(N) gates | Small molecules |
| **Bravyi-Kitaev** | N qubits | O(log N) gates | Medium molecules |
| **Parity** | N-1 qubits | Moderate | Symmetry reduction |

### Workflow

```
Molecule geometry → PySCF/Psi4 driver → Integrals h_pq, h_pqrs
  → Active space reduction → Fermion-to-qubit mapping
  → Qubit Hamiltonian → VQE/QPE optimization → Ground state energy
```

### Active Space Selection

For large molecules, use **active space reduction** to limit qubits:
- Freeze core electrons (1s orbitals)
- Select only frontier orbitals (HOMO-2 to LUMO+2)
- Reduce from hundreds of orbitals to 4–20 active orbitals
""",

    "drug_discovery": """## Quantum Drug Discovery

Quantum computing can accelerate drug discovery by accurately simulating molecular interactions.

### Pipeline

1. **Target identification** — identify protein target (e.g., SARS-CoV-2 protease)
2. **Lead generation** — screen molecular candidates against binding site
3. **Binding affinity** — VQE for accurate energy calculations of protein-ligand complexes
4. **ADMET prediction** — absorption, distribution, metabolism, excretion, toxicity
5. **Lead optimization** — iterate on molecular structure

### Quantum Advantage

| Classical (DFT/HF) | Quantum (VQE/QPE) |
|---|---|
| Approximate electron correlation | Exact correlation energy |
| Polynomial scaling | Exponential state space |
| Fails for strongly correlated systems | Handles transition metals, radicals |

### Key Metrics
- **Chemical accuracy**: 1.6 mHa (1 kcal/mol) — minimum for useful drug predictions
- **Current VQE accuracy**: ~5 mHa on 10-qubit systems
- **Target for drug discovery**: 100+ qubit error-corrected machines (est. 2028–2031)

### IBM Partnership Examples
- **IBM + Cleveland Clinic**: Quantum simulations for Alzheimer's drug candidates
- **IBM + Pfizer**: SQD (sample-based quantum diagonalization) for molecular energies
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "vqe": ["vqe", "variational quantum eigensolver", "ground state energy", "eigensolver"],
    "hamiltonian": ["hamiltonian", "jordan-wigner", "bravyi-kitaev", "fermion", "molecular orbital"],
    "drug_discovery": ["drug", "discovery", "protein", "binding", "admet", "pharmaceutical", "medicine"],
}


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick chemistry topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None


# ── Quick circuit templates ─────────────────────────────
VQE_CIRCUITS: dict[str, tuple[str, str]] = {
    "h2": ("H₂ VQE Simulation", '''from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import EfficientSU2
from qiskit_aer import AerSimulator
import numpy as np

# H₂ molecule VQE ansatz — 2 qubits
ansatz = EfficientSU2(num_qubits=2, reps=1, entanglement="linear")

# Bind random parameters for demonstration
num_params = ansatz.num_parameters
params = np.random.uniform(-np.pi, np.pi, num_params)
bound_circuit = ansatz.assign_parameters(params)

# Add measurements
qc = QuantumCircuit(2, 2)
qc.compose(bound_circuit, inplace=True)
qc.measure([0, 1], [0, 1])

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
result = simulator.run(transpiled, shots=4096).result()
counts = result.get_counts()

print("H₂ VQE Ansatz Measurement:", counts)
print("Note: In a real VQE, a classical optimizer iterates these parameters")
print("to minimize ⟨ψ(θ)|H|ψ(θ)⟩ toward the ground state energy -1.137 Ha")
'''),
    "lih": ("LiH VQE Simulation", '''from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import EfficientSU2
from qiskit_aer import AerSimulator
import numpy as np

# LiH molecule VQE ansatz — 4 qubits (reduced active space)
ansatz = EfficientSU2(num_qubits=4, reps=2, entanglement="circular")

# Bind random parameters
num_params = ansatz.num_parameters
params = np.random.uniform(-np.pi, np.pi, num_params)
bound_circuit = ansatz.assign_parameters(params)

qc = QuantumCircuit(4, 4)
qc.compose(bound_circuit, inplace=True)
qc.measure(range(4), range(4))

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
result = simulator.run(transpiled, shots=4096).result()
counts = result.get_counts()

print("LiH VQE Ansatz (4 qubits, active space):", counts)
print("Ground state energy target: -7.882 Ha")
'''),
}


def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    """Try to generate a chemistry-related circuit."""
    lower = message.lower()

    for key, (name, code) in VQE_CIRCUITS.items():
        if key in lower or (key == "h2" and "hydrogen" in lower):
            from app.quantum.executor import QISKIT_AVAILABLE
            if not QISKIT_AVAILABLE:
                return [], None

            artifacts = [
                Artifact(
                    type=ArtifactType.CODE,
                    title=f"{name} — Qiskit Code",
                    content=code,
                    language="python",
                ),
            ]

            # Execute the ansatz to show measurement distribution
            try:
                from qiskit import QuantumCircuit as QC, transpile
                from qiskit.circuit.library import EfficientSU2
                from qiskit_aer import AerSimulator
                import numpy as np
                import json
                import time

                n_qubits = 2 if key == "h2" else 4
                reps = 1 if key == "h2" else 2
                ansatz = EfficientSU2(num_qubits=n_qubits, reps=reps, entanglement="linear" if key == "h2" else "circular")
                params = np.random.uniform(-np.pi, np.pi, ansatz.num_parameters)
                bound = ansatz.assign_parameters(params)

                qc = QC(n_qubits, n_qubits)
                qc.compose(bound, inplace=True)
                qc.measure(range(n_qubits), range(n_qubits))

                sim = AerSimulator()
                t0 = time.time()
                result = sim.run(transpile(qc, sim), shots=4096).result()
                elapsed = round((time.time() - t0) * 1000, 2)
                counts = result.get_counts()

                artifacts.append(Artifact(
                    type=ArtifactType.RESULTS,
                    title=f"{name} — VQE Ansatz Distribution",
                    content=json.dumps(counts),
                    metadata={
                        "shots": 4096,
                        "execution_time_ms": elapsed,
                        "backend": "aer_statevector",
                        "num_qubits": n_qubits,
                        "depth": qc.depth(),
                    },
                ))

                top = sorted(counts.items(), key=lambda x: -x[1])[:4]
                counts_str = ", ".join(f"`{k}`: {v}" for k, v in top)
                summary = (
                    f"## {name}\n\n"
                    f"I've generated and executed a VQE ansatz circuit.\n\n"
                    f"**Circuit:** {n_qubits} qubits, depth {qc.depth()}\n"
                    f"**Ansatz:** EfficientSU2 (reps={reps})\n"
                    f"**Shots:** 4096\n"
                    f"**Time:** {elapsed}ms\n\n"
                    f"**Top states:** {counts_str}\n\n"
                    f"In a real VQE workflow, a classical optimizer would iterate the ansatz "
                    f"parameters to minimize ⟨ψ(θ)|H|ψ(θ)⟩ and find the ground-state energy."
                )
                return artifacts, summary

            except Exception:
                summary = (
                    f"## {name}\n\n"
                    f"I've generated the VQE ansatz code for {name}. "
                    f"Check the artifact panel for the complete Qiskit implementation."
                )
                return artifacts, summary

    return [], None
