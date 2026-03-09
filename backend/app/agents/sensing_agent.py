"""Milimo Quantum — Sensing & Metrology Agent.

Handles queries on atom interferometry, magnetometry, quantum sensing,
and quantum-enhanced measurement with executable Qiskit circuits.
"""
from __future__ import annotations

from app.models.schemas import Artifact, ArtifactType

QUICK_TOPICS: dict[str, str] = {
    "sensing": """## Quantum Sensing & Metrology

Quantum sensing exploits quantum states (superposition, entanglement) for ultra-high precision measurements of physical quantities (magnetic fields, acceleration, time).

### Key Technologies
- **NV-Centers in Diamond**: Nitrogen-Vacancy centers act as atomic-scale magnetometers capable of measuring magnetic fields of single cells or neurons.
- **Atom Interferometry**: Uses the wave nature of cold atoms to measure gravity or acceleration with extreme precision (Quantum Gravimeters).
- **Quantum Radar/LiDAR**: Uses entangled photon pairs (quantum illumination) to detect stealth targets with high noise resilience.

### Quantum Advantage in Sensing
- **Standard Quantum Limit (SQL)**: $\\Delta \\phi \\propto 1/\\sqrt{N}$ — achievable with independent probes
- **Heisenberg Limit**: $\\Delta \\phi \\propto 1/N$ — achievable with entangled probes (GHZ states)
- **Fisher Information**: $F_Q$ quantifies the maximum information extractable about a parameter. Higher $F_Q$ = better sensitivity.
""",
    "ramsey": """## Ramsey Interferometry

Ramsey interferometry is the gold standard for quantum sensing. It measures the phase accumulated by a qubit during free evolution in an external field.

### Protocol
1. **Prepare**: Apply Hadamard → superposition $|+\\rangle$
2. **Evolve**: Free evolution under field Hamiltonian → phase $\\phi = \\gamma B t$
3. **Measure**: Apply second Hadamard → interference → measurement

The probability of measuring |1⟩ oscillates as $P(|1\\rangle) = \\sin^2(\\phi/2)$, giving field-dependent fringes.
""",
    "magnetometry": """## Quantum Magnetometry (GHZ-Enhanced)

Using GHZ states (maximally entangled N-qubit states) for magnetometry achieves Heisenberg-limited sensitivity:

$$\\Delta B = \\frac{1}{\\gamma \\sqrt{F_Q}} \\propto \\frac{1}{N}$$

compared to the Standard Quantum Limit $\\propto 1/\\sqrt{N}$ for independent probes.

### Applications
- **Brain imaging** (MEG): detecting femtotesla fields from neural currents
- **Geological survey**: mapping magnetic anomalies for mineral exploration
- **Navigation**: drift-free inertial sensing for GPS-denied environments
""",
    "fisher": """## Quantum Fisher Information (QFI)

The Quantum Fisher Information $F_Q$ is the fundamental limit on parameter estimation precision. For a quantum state $|\\psi(\\theta)\\rangle$:

$$F_Q = 4(\\langle \\partial_\\theta \\psi | \\partial_\\theta \\psi \\rangle - |\\langle \\psi | \\partial_\\theta \\psi \\rangle|^2)$$

The Cramér-Rao bound states: $\\Delta \\theta \\geq 1/\\sqrt{\\nu F_Q}$ where $\\nu$ is the number of measurements.

| State | QFI | Scaling |
|-------|-----|---------|
| Product state | N | SQL: $1/\\sqrt{N}$ |
| GHZ state | N² | Heisenberg: $1/N$ |
| Squeezed state | Between | Sub-SQL |
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "sensing": ["sensing", "metrology", "nv-center", "nv center", "gravimeter", "quantum sensor"],
    "ramsey": ["ramsey", "interferometry", "free evolution", "fringe"],
    "magnetometry": ["magnetometry", "magnetometer", "magnetic field", "brain imaging", "meg"],
    "fisher": ["fisher", "qfi", "cramer-rao", "cramér-rao", "estimation precision"],
}


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick sensing topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None


# ── Circuit Templates ──────────────────────────────────


def _ramsey_code(n_qubits: int = 1) -> str:
    """Generate Ramsey interferometry circuit."""
    return f'''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np

# Ramsey Interferometry — Phase Sensing
# Measures the phase accumulated during free evolution in an external field

n_qubits = {n_qubits}
phases = np.linspace(0, 2*np.pi, 20)  # Sweep the field parameter
probabilities = []

simulator = AerSimulator()
shots = 1024

for phi in phases:
    qc = QuantumCircuit(n_qubits, n_qubits)

    # Step 1: First π/2 pulse (Hadamard)
    for q in range(n_qubits):
        qc.h(q)

    # Step 2: Free evolution (phase from external field)
    for q in range(n_qubits):
        qc.rz(phi, q)

    # Step 3: Second π/2 pulse (Hadamard)
    for q in range(n_qubits):
        qc.h(q)

    # Measure
    qc.measure(range(n_qubits), range(n_qubits))

    transpiled = transpile(qc, simulator)
    result = simulator.run(transpiled, shots=shots).result()
    counts = result.get_counts()
    prob_0 = counts.get('0' * n_qubits, 0) / shots
    probabilities.append(prob_0)

# Print the Ramsey fringe pattern
print("Ramsey Interferometry — Phase Sweep")
print("=" * 45)
for i, (phi, prob) in enumerate(zip(phases, probabilities)):
    bar = "█" * int(prob * 30)
    print(f"  φ={{phi:.2f}} rad | P(|0⟩)={{prob:.3f}} |{{bar}}")

# Show the circuit for a single phase
demo_qc = QuantumCircuit({n_qubits}, {n_qubits})
for q in range({n_qubits}):
    demo_qc.h(q)
    demo_qc.rz(np.pi/4, q)  # Example phase
    demo_qc.h(q)
demo_qc.measure(range({n_qubits}), range({n_qubits}))
print("\\n" + str(demo_qc.draw(output="text")))

# Execute the demo circuit
transpiled = transpile(demo_qc, simulator)
result = simulator.run(transpiled, shots=1024).result()
counts = result.get_counts()
print(f"\\nDemo measurement (φ=π/4): {{counts}}")
'''


def _ghz_magnetometry_code(n_qubits: int = 4) -> str:
    """Generate GHZ-based quantum magnetometry circuit."""
    return f'''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np

# GHZ-Based Quantum Magnetometry
# Achieves Heisenberg-limited sensitivity: Δφ ∝ 1/N (vs SQL: 1/√N)

n_qubits = {n_qubits}
simulator = AerSimulator()
shots = 2048

# Phase to detect (simulated magnetic field)
B_field_phase = np.pi / 6  # Phase from magnetic field interaction

# === Standard Quantum Limit (independent probes) ===
qc_sql = QuantumCircuit(n_qubits, n_qubits)
for q in range(n_qubits):
    qc_sql.h(q)
    qc_sql.rz(B_field_phase, q)  # Each qubit senses independently
    qc_sql.h(q)
qc_sql.measure(range(n_qubits), range(n_qubits))

# === Heisenberg Limit (GHZ entangled probes) ===
qc_hl = QuantumCircuit(n_qubits, n_qubits)
# Create GHZ state: |000...0⟩ + |111...1⟩
qc_hl.h(0)
for q in range(1, n_qubits):
    qc_hl.cx(q-1, q)
# Phase accumulation (N times faster with GHZ!)
for q in range(n_qubits):
    qc_hl.rz(B_field_phase, q)
# Reverse GHZ
for q in range(n_qubits-1, 0, -1):
    qc_hl.cx(q-1, q)
qc_hl.h(0)
qc_hl.measure(range(n_qubits), range(n_qubits))

# Execute both
result_sql = simulator.run(transpile(qc_sql, simulator), shots=shots).result()
result_hl = simulator.run(transpile(qc_hl, simulator), shots=shots).result()

counts_sql = result_sql.get_counts()
counts_hl = result_hl.get_counts()

print("Quantum Magnetometry — GHZ Enhancement")
print("=" * 50)
print(f"Field phase: {{B_field_phase:.4f}} rad")
print(f"Number of sensor qubits: {{n_qubits}}")
print(f"\\n📊 Standard Quantum Limit (independent):")
print(f"   Counts: {{counts_sql}}")
print(f"   Sensitivity: ΔB ∝ 1/√N = 1/√{n_qubits} = {{1/np.sqrt(n_qubits):.4f}}")
print(f"\\n📊 Heisenberg Limit (GHZ entangled):")
print(f"   Counts: {{counts_hl}}")
print(f"   Sensitivity: ΔB ∝ 1/N = 1/{n_qubits} = {{1/n_qubits:.4f}}")
print(f"\\n✨ Quantum advantage: {{np.sqrt(n_qubits):.2f}}× improvement")
print("\\nCircuit (GHZ Magnetometry):")
print(qc_hl.draw(output="text"))
'''


# ── Circuit Dispatch ──────────────────────────────────

CIRCUIT_KEYWORDS: dict[str, list[str]] = {
    "ramsey": ["ramsey", "interferometry", "phase sensing", "fringe", "free evolution"],
    "magnetometry": ["magnetometry", "magnetometer", "magnetic", "ghz sensing", "heisenberg"],
    "qpe_sensing": ["phase estimation", "qpe", "precision measurement"],
}


def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    """Try to match a sensing circuit and generate executable code."""
    lower = message.lower()

    for circuit_type, keywords in CIRCUIT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            if circuit_type == "ramsey":
                code = _ramsey_code()
                summary = "## Ramsey Interferometry\n\nSweeping the phase parameter to observe Ramsey fringes — the foundation of quantum sensing."
            elif circuit_type == "magnetometry":
                code = _ghz_magnetometry_code()
                summary = "## GHZ-Based Quantum Magnetometry\n\nComparing standard quantum limit vs. Heisenberg limit using entangled GHZ probes."
            else:
                return [], None

            import json
            from app.quantum.advanced_sims import run_qutip_sensing_simulation
            
            qutip_data = run_qutip_sensing_simulation(n_qubits=4, phase=0.523)

            artifacts = [
                Artifact(
                    type=ArtifactType.CODE,
                    title=f"Sensing — {circuit_type.replace('_', ' ').title()}",
                    content=code,
                    language="python",
                ),
                Artifact(
                    type=ArtifactType.JSON,
                    title=f"QuTiP Physics Simulation — {circuit_type.title()}",
                    content=json.dumps(qutip_data, indent=2),
                )
            ]
            return artifacts, summary

    return [], None
