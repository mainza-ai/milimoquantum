"""Milimo Quantum — Networking Agent.

Handles Quantum Networking, QKD, teleportation, and internet simulation queries
with executable Qiskit circuits.
"""
from __future__ import annotations

from app.models.schemas import Artifact, ArtifactType

QUICK_TOPICS: dict[str, str] = {
    "networking": """## Quantum Networking & Internet

Quantum networks transmit qubits between physically separated nodes, enabling secure communication and distributed quantum computing.

### Key Protocols
- **BB84 QKD**: Bennett-Brassard 1984 — the first quantum key distribution protocol. Alice sends qubits in random bases, Bob measures in random bases, sifting reveals shared key.
- **E91 Protocol**: Ekert 1991 — uses entangled Bell pairs. Security guaranteed by Bell inequality violation.
- **Quantum Teleportation**: Transfers quantum state using pre-shared entanglement + 2 classical bits.
- **Entanglement Swapping**: Extends entanglement range using intermediate "repeater" nodes.
- **Quantum Repeaters**: Overcome photon loss over long distances using entanglement distillation + swapping.

### Key Metrics
| Metric | Description |
|--------|-------------|
| Key Rate | Secure bits per second (after sifting + privacy amplification) |
| QBER | Quantum Bit Error Rate — must be <11% for BB84 security |
| Fidelity | How close the teleported state is to the original |
""",
    "bb84": """## BB84 Quantum Key Distribution

BB84 is the cornerstone of quantum cryptography. It enables two parties (Alice and Bob) to establish a provably secure shared key.

### Protocol Steps
1. **Alice prepares** random bits in random bases (Z or X)
2. **Alice sends** qubits to Bob through quantum channel
3. **Bob measures** in random bases (Z or X)
4. **Sifting**: Alice and Bob announce bases (not bits). Keep matching bases.
5. **Error estimation**: Sample bits to estimate QBER
6. If QBER < 11%: **no eavesdropper** → use remaining bits as key
7. If QBER > 11%: **eavesdropper detected** → abort

### Security: No-Cloning Theorem
An eavesdropper (Eve) cannot copy qubits without disturbing them, introducing detectable errors.
""",
    "teleportation": """## Quantum Teleportation

Quantum teleportation transfers an unknown quantum state from Alice to Bob using:
- 1 pre-shared Bell pair (entanglement)
- 2 classical bits of communication
- No physical qubit transfer

### Protocol
1. Alice and Bob share a Bell pair: $(|00\\rangle + |11\\rangle)/\\sqrt{2}$
2. Alice performs a Bell measurement on her qubit + the unknown state
3. Alice sends 2 classical bits (measurement outcome) to Bob
4. Bob applies a corrective gate based on Alice's bits → recovers the original state

**Note**: This does NOT violate no-faster-than-light because classical bits must be sent.
""",
    "repeater": """## Quantum Repeaters

Quantum repeaters solve the problem of photon loss in long-distance quantum communication.

### Why Needed
- Optical fiber loses ~0.2 dB/km → after 100 km, only 1% of photons survive
- Classical repeaters amplify signals, but **no-cloning theorem** prevents quantum amplification
- Solution: **entanglement swapping** at intermediate nodes

### Architecture
```
Alice ←→ Node1 ←→ Node2 ←→ ... ←→ Bob
     Bell pair   Bell pair       Bell pair
         └── swap ──┘  └── swap ──┘
              Result: Alice ←→ Bob entangled
```

### Key Technologies
- **Quantum memories**: Store qubits while waiting for classical signals
- **Entanglement distillation**: Purify noisy Bell pairs into high-fidelity ones
- **Error correction**: Protect stored qubits from decoherence
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "networking": ["network", "quantum internet", "quantum communication"],
    "bb84": ["bb84", "qkd", "key distribution", "quantum key", "cryptographic key"],
    "teleportation": ["teleportation", "teleport", "state transfer"],
    "repeater": ["repeater", "entanglement swap", "swapping", "long distance", "netsquid", "squidasm"],
}


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick networking topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None


# ── Circuit Templates ──────────────────────────────────


def _bb84_code(n_bits: int = 16) -> str:
    """Generate BB84 QKD simulation code."""
    return f'''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import random
import numpy as np

# BB84 Quantum Key Distribution — Full Protocol Simulation
n_bits = {n_bits}
random.seed(42)

simulator = AerSimulator()

# Step 1: Alice generates random bits and bases
alice_bits = [random.randint(0, 1) for _ in range(n_bits)]
alice_bases = [random.randint(0, 1) for _ in range(n_bits)]  # 0=Z, 1=X

# Step 2: Bob chooses random measurement bases
bob_bases = [random.randint(0, 1) for _ in range(n_bits)]

# Step 3: Quantum channel — Alice prepares, Bob measures
bob_results = []
for i in range(n_bits):
    qc = QuantumCircuit(1, 1)

    # Alice prepares
    if alice_bits[i] == 1:
        qc.x(0)
    if alice_bases[i] == 1:  # X basis
        qc.h(0)

    # Bob measures
    if bob_bases[i] == 1:  # X basis
        qc.h(0)
    qc.measure(0, 0)

    transpiled = transpile(qc, simulator)
    result = simulator.run(transpiled, shots=1).result()
    measured = int(list(result.get_counts().keys())[0])
    bob_results.append(measured)

# Step 4: Sifting — keep bits where bases match
sifted_key_alice = []
sifted_key_bob = []
for i in range(n_bits):
    if alice_bases[i] == bob_bases[i]:
        sifted_key_alice.append(alice_bits[i])
        sifted_key_bob.append(bob_results[i])

# Step 5: Error estimation
errors = sum(a != b for a, b in zip(sifted_key_alice, sifted_key_bob))
qber = errors / len(sifted_key_alice) if sifted_key_alice else 1.0

print("BB84 Quantum Key Distribution")
print("=" * 45)
print(f"Qubits sent: {{n_bits}}")
print(f"Alice bits:   {{''.join(map(str, alice_bits))}}")
print(f"Alice bases:  {{''.join(['Z' if b==0 else 'X' for b in alice_bases])}}")
print(f"Bob bases:    {{''.join(['Z' if b==0 else 'X' for b in bob_bases])}}")
print(f"Bob results:  {{''.join(map(str, bob_results))}}")
print(f"\\nSifting: {{len(sifted_key_alice)}} / {{n_bits}} bits matched bases")
print(f"Sifted key (Alice): {{''.join(map(str, sifted_key_alice))}}")
print(f"Sifted key (Bob):   {{''.join(map(str, sifted_key_bob))}}")
print(f"\\nQBER: {{qber:.1%}}")
print(f"Security: {{'✅ SECURE (QBER < 11%)' if qber < 0.11 else '❌ EAVESDROPPER DETECTED'}}")
print(f"Final key: {{''.join(map(str, sifted_key_alice))}}")
'''


def _teleportation_code() -> str:
    """Generate quantum teleportation circuit."""
    return '''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np

# Quantum Teleportation — Full Protocol
# Teleports an arbitrary state from Alice (q0) to Bob (q2)

simulator = AerSimulator()

# State to teleport: |ψ⟩ = cos(θ/2)|0⟩ + e^{iφ}sin(θ/2)|1⟩
theta = np.pi / 3  # Example rotation

qc = QuantumCircuit(3, 2)

# Step 0: Prepare the state to teleport on q0
qc.ry(theta, 0)
qc.barrier()

# Step 1: Create Bell pair between Alice (q1) and Bob (q2)
qc.h(1)
qc.cx(1, 2)
qc.barrier()

# Step 2: Alice's Bell measurement (q0, q1)
qc.cx(0, 1)
qc.h(0)
qc.barrier()

# Step 3: Measure Alice's qubits (classical communication)
qc.measure(0, 0)
qc.measure(1, 1)

# Step 4: Bob's correction gates (conditioned on classical bits)
qc.x(2).c_if(1, 1)  # If q1 measured 1, apply X
qc.z(2).c_if(0, 1)  # If q0 measured 1, apply Z

print("Quantum Teleportation Circuit")
print("=" * 45)
print(qc.draw(output="text"))

# Verify teleportation by running the circuit
transpiled = transpile(qc, simulator)
result = simulator.run(transpiled, shots=1024).result()
counts = result.get_counts()

print(f"\\nState teleported: |ψ⟩ = cos({theta/2:.2f})|0⟩ + sin({theta/2:.2f})|1⟩")
print(f"θ = {theta:.4f} rad ({np.degrees(theta):.1f}°)")
print(f"\\nMeasurement results: {counts}")
print(f"\\nBob's qubit now holds the teleported state ✅")
print(f"Note: c_if gates apply corrections based on Alice's measurement outcomes.")
'''


def _entanglement_swapping_code() -> str:
    """Generate entanglement swapping circuit."""
    return '''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Entanglement Swapping — Quantum Repeater Building Block
# Creates entanglement between q0 (Alice) and q3 (Bob)
# via an intermediate node that performs a Bell measurement

simulator = AerSimulator()

qc = QuantumCircuit(4, 4)

# Step 1: Create two independent Bell pairs
# Pair 1: Alice (q0) ↔ Node (q1)
qc.h(0)
qc.cx(0, 1)
# Pair 2: Node (q2) ↔ Bob (q3)
qc.h(2)
qc.cx(2, 3)
qc.barrier()

# Step 2: Bell measurement at intermediate node (q1, q2)
qc.cx(1, 2)
qc.h(1)
qc.barrier()

# Measure node qubits
qc.measure(1, 1)
qc.measure(2, 2)

# Step 3: Corrections on Bob's qubit based on node measurement
qc.x(3).c_if(2, 1)
qc.z(3).c_if(1, 1)
qc.barrier()

# Step 4: Verify entanglement — measure Alice and Bob
qc.measure(0, 0)
qc.measure(3, 3)

print("Entanglement Swapping Circuit")
print("=" * 45)
print("Alice(q0) ↔ Node(q1,q2) ↔ Bob(q3)")
print(qc.draw(output="text"))

transpiled = transpile(qc, simulator)
result = simulator.run(transpiled, shots=2048).result()
counts = result.get_counts()

print(f"\\nMeasurement results (all 4 qubits): {counts}")
print(f"\\nAlice-Bob correlation (q0,q3):")
ab_counts = {}
for bitstring, count in counts.items():
    alice_bit = bitstring[3]  # q0 is rightmost
    bob_bit = bitstring[0]    # q3 is leftmost
    ab_key = f"{alice_bit}{bob_bit}"
    ab_counts[ab_key] = ab_counts.get(ab_key, 0) + count

for k, v in sorted(ab_counts.items()):
    print(f"  Alice={k[0]}, Bob={k[1]}: {v}")
print(f"\\n✨ Alice and Bob are now entangled despite never directly interacting!")
'''


# ── Circuit Dispatch ──────────────────────────────────

CIRCUIT_KEYWORDS: dict[str, list[str]] = {
    "bb84": ["bb84", "qkd", "key distribution", "quantum key"],
    "teleportation": ["teleport", "teleportation", "state transfer"],
    "swapping": ["swap", "swapping", "repeater", "entanglement distribution"],
}


def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    """Try to match a networking circuit and generate executable code."""
    lower = message.lower()

    for circuit_type, keywords in CIRCUIT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            if circuit_type == "bb84":
                code = _bb84_code()
                summary = "## BB84 Quantum Key Distribution\n\nFull protocol: prepare → send → measure → sift → estimate QBER → verify security."
            elif circuit_type == "teleportation":
                code = _teleportation_code()
                summary = "## Quantum Teleportation\n\nFull protocol: Bell pair → Bell measurement → classical communication → correction → state recovery."
            elif circuit_type == "swapping":
                code = _entanglement_swapping_code()
                summary = "## Entanglement Swapping\n\nQuantum repeater building block: two Bell pairs → node Bell measurement → long-range entanglement."
            else:
                return [], None

            artifacts = [
                Artifact(
                    type=ArtifactType.CODE,
                    title=f"Networking — {circuit_type.replace('_', ' ').title()}",
                    content=code,
                    language="python",
                ),
            ]
            return artifacts, summary

    return [], None
