"""Milimo Quantum — Cryptography & Post-Quantum Security Agent.

Handles quantum key distribution (QKD), Shor's algorithm, QRNG,
and post-quantum cryptography education.
Phase 3: Template-based with executable circuits.
"""
from __future__ import annotations

from app.models.schemas import Artifact, ArtifactType


# ── Quick-reference knowledge base ──────────────────────
QUICK_TOPICS: dict[str, str] = {
    "bb84": """## BB84 Quantum Key Distribution Protocol

BB84 is the first and most widely implemented QKD protocol, invented by Bennett & Brassard in 1984.

### How It Works

1. **Alice** prepares qubits in random bases (Z or X) with random bit values
2. **Alice sends** qubits to Bob over a quantum channel
3. **Bob measures** each qubit in a randomly chosen basis (Z or X)
4. **Sifting** — Alice and Bob publicly compare bases, keep only matching ones
5. **Error estimation** — sacrifice a subset to check for eavesdropping
6. **Privacy amplification** — hash remaining bits to extract secure key

### Security Guarantee

$$P(\\text{Eve detected}) = 1 - \\left(\\frac{3}{4}\\right)^n$$

Any eavesdropper (Eve) must measure qubits, causing detectable disturbance:
- If Eve intercepts in the **wrong basis**, she introduces ~25% error rate
- Expected error rate without Eve: **< 1%** (channel noise only)
- Alarm threshold: **> 11%** error rate → abort protocol

### Basis Encoding

| Basis | Bit 0 | Bit 1 |
|-------|-------|-------|
| **Z (Computational)** | |0⟩ | |1⟩ |
| **X (Hadamard)** | |+⟩ = (|0⟩+|1⟩)/√2 | |−⟩ = (|0⟩−|1⟩)/√2 |

### Real-World Deployments

- **China Micius satellite** — 1200 km QKD (2017)
- **SwissQuantum** — Geneva metropolitan QKD network
- **Toshiba** — 600 km fiber QKD record (2021)

💡 *Try it*: `/crypto Simulate BB84 for 8 qubits`
""",

    "shor": """## Shor's Algorithm

Shor's algorithm can factor integers in **polynomial time** on a quantum computer,
breaking RSA and other public-key cryptosystems.

### Complexity Comparison

| Algorithm | Time Complexity | Type |
|-----------|----------------|------|
| Trial Division | O(√N) | Classical |
| Number Field Sieve | O(exp(N^(1/3))) | Classical (best known) |
| **Shor's Algorithm** | **O((log N)³)** | **Quantum** |

### How It Works

1. **Choose** random `a < N` and check `gcd(a, N) = 1`
2. **Find period** `r` of `f(x) = a^x mod N` using QPE
3. **Extract factors**: `gcd(a^(r/2) ± 1, N)`

### Current Status

| Factored Number | Qubits Used | Year | Team |
|----------------|-------------|------|------|
| 15 = 3 × 5 | 7 | 2001 | IBM |
| 21 = 3 × 7 | 10 | 2012 | Bristol |
| RSA-2048 | ~4000 logical | Future | Estimated |

### Threat Level

- **RSA-2048**: Requires ~4,000 error-corrected logical qubits (~20M physical)
- **ECC-256**: Requires ~2,300 logical qubits
- **Timeline**: Estimated 2030–2040 for cryptographically relevant quantum computers
- **HNDL threat**: "Harvest Now, Decrypt Later" — encrypted data stolen today could be decrypted when QCs are ready

💡 *Try it*: `/code Demonstrate Shor's algorithm for factoring 15`
""",

    "pqc": """## Post-Quantum Cryptography (PQC)

NIST standardized the first post-quantum algorithms in 2024 to resist quantum attacks.

### NIST PQC Standards

| Algorithm | Type | Use Case | Status |
|-----------|------|----------|--------|
| **ML-KEM (CRYSTALS-Kyber)** | Lattice-based | Key encapsulation | FIPS 203 (2024) |
| **ML-DSA (CRYSTALS-Dilithium)** | Lattice-based | Digital signatures | FIPS 204 (2024) |
| **SLH-DSA (SPHINCS+)** | Hash-based | Backup signatures | FIPS 205 (2024) |
| **FN-DSA (FALCON)** | Lattice-based | Compact signatures | Draft (2025) |

### Migration Strategy

1. **Inventory** — catalog all cryptographic assets (TLS certs, VPN, SSH, etc.)
2. **Prioritize** — start with long-lived secrets (government, healthcare, finance)
3. **Hybrid mode** — deploy PQC alongside classical crypto (double protection)
4. **Test** — validate performance impact (Kyber adds ~1KB to key exchange)
5. **Full migration** — transition to PQC-only when validated

### Key Sizes Comparison

| Algorithm | Public Key | Ciphertext | Security Level |
|-----------|-----------|------------|----------------|
| RSA-2048 | 256 B | 256 B | 112-bit (vulnerable) |
| ML-KEM-768 | 1,184 B | 1,088 B | 192-bit (quantum-safe) |
| ML-KEM-1024 | 1,568 B | 1,568 B | 256-bit (quantum-safe) |

### Quantum-Safe TLS

```
Client → ServerHello: ML-KEM-768 + X25519 (hybrid)
Server → ServerHello: Accept hybrid key exchange
→ Shared secret derived from BOTH classical + PQC
```
""",

    "qrng": """## Quantum Random Number Generation (QRNG)

Quantum mechanics provides **true randomness** — unlike classical PRNGs which are deterministic.

### How It Works

1. **Prepare** qubit in |0⟩ state
2. **Apply** Hadamard gate → |+⟩ = (|0⟩ + |1⟩)/√2
3. **Measure** → 0 or 1 with exactly 50% probability each
4. **Repeat** for N bits of certified random output

### Why QRNG Matters

| Source | Truly Random? | Certifiable? | Speed |
|--------|:---:|:---:|------|
| `/dev/urandom` | ❌ PRNG | ❌ | Fast |
| Hardware RNG (Intel RDRAND) | ⚠️ Debated | ❌ | Fast |
| Atmospheric noise | ~Yes | ❌ | Slow |
| **Quantum (H gate + measure)** | **✅ Provably** | **✅** | Medium |

### Applications

- **Cryptographic key generation** — provably unpredictable keys
- **Monte Carlo simulation** — unbiased sampling (finance, physics)
- **Lottery / gambling** — certified fair randomness
- **Scientific experiments** — eliminate systematic bias

### NIST SP 800-22 Tests

All QRNG output should pass:
- Frequency test, Runs test, Serial test
- Approximate entropy test, Cumulative sums
- Linear complexity test, Universal test

💡 *Try it*: `/crypto Generate 16 quantum random bits`
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "bb84": ["bb84", "qkd", "quantum key distribution", "key distribution", "e91", "quantum key"],
    "shor": ["shor", "factoring", "factorization", "rsa", "break encryption", "factor"],
    "pqc": ["post-quantum", "pqc", "kyber", "dilithium", "lattice", "nist", "quantum-safe", "quantum safe"],
    "qrng": ["qrng", "random number", "random bit", "entropy", "true random"],
}


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick cryptography topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None


# ── Quick circuit templates ─────────────────────────────
def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    """Try to generate a cryptography-related circuit."""
    lower = message.lower()

    # ── BB84 QKD simulation ─────────────────────────────
    if any(kw in lower for kw in ["bb84", "qkd", "key distribution"]):
        return _build_bb84_circuit()

    # ── QRNG circuit ────────────────────────────────────
    if any(kw in lower for kw in ["random", "qrng", "entropy"]):
        return _build_qrng_circuit()

    return [], None


def _build_bb84_circuit() -> tuple[list[Artifact], str | None]:
    """Build and execute a BB84 QKD simulation circuit."""
    code = '''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np

# BB84 QKD Simulation — 8 qubits
n_bits = 8

# Step 1: Alice chooses random bits and bases
alice_bits = np.random.randint(0, 2, n_bits)
alice_bases = np.random.randint(0, 2, n_bits)  # 0=Z, 1=X

# Step 2: Bob chooses random measurement bases
bob_bases = np.random.randint(0, 2, n_bits)  # 0=Z, 1=X

# Step 3: Build quantum circuit
qc = QuantumCircuit(n_bits, n_bits)

for i in range(n_bits):
    # Alice encodes her bit
    if alice_bits[i] == 1:
        qc.x(i)          # Flip to |1⟩
    if alice_bases[i] == 1:
        qc.h(i)          # Switch to X basis

    qc.barrier([i])

    # Bob measures in his chosen basis
    if bob_bases[i] == 1:
        qc.h(i)          # Switch to X basis before measuring

qc.measure(range(n_bits), range(n_bits))

# Execute
sim = AerSimulator()
result = sim.run(transpile(qc, sim), shots=1).result()
bob_results = list(result.get_counts().keys())[0][::-1]
bob_bits = [int(b) for b in bob_results]

# Sifting: keep only bits where bases match
matching = [i for i in range(n_bits) if alice_bases[i] == bob_bases[i]]
sifted_key_alice = [alice_bits[i] for i in matching]
sifted_key_bob = [bob_bits[i] for i in matching]

print(f"Alice bits:  {list(alice_bits)}")
print(f"Alice bases: {['Z' if b==0 else 'X' for b in alice_bases]}")
print(f"Bob bases:   {['Z' if b==0 else 'X' for b in bob_bases]}")
print(f"Bob results: {bob_bits}")
print(f"Matching positions: {matching}")
print(f"Sifted key (Alice): {sifted_key_alice}")
print(f"Sifted key (Bob):   {sifted_key_bob}")
print(f"Keys match: {sifted_key_alice == sifted_key_bob}")
'''

    from app.quantum.executor import QISKIT_AVAILABLE
    if not QISKIT_AVAILABLE:
        return [], None

    artifacts = [
        Artifact(
            type=ArtifactType.CODE,
            title="BB84 QKD Simulation — Qiskit Code",
            content=code,
            language="python",
        ),
    ]

    try:
        from qiskit import QuantumCircuit as QC, transpile
        from qiskit_aer import AerSimulator
        import numpy as np
        import json
        import time

        n_bits = 8
        alice_bits = np.random.randint(0, 2, n_bits)
        alice_bases = np.random.randint(0, 2, n_bits)
        bob_bases = np.random.randint(0, 2, n_bits)

        qc = QC(n_bits, n_bits)
        for i in range(n_bits):
            if alice_bits[i] == 1:
                qc.x(i)
            if alice_bases[i] == 1:
                qc.h(i)
            qc.barrier([i])
            if bob_bases[i] == 1:
                qc.h(i)
        qc.measure(range(n_bits), range(n_bits))

        sim = AerSimulator()
        t0 = time.time()
        result = sim.run(transpile(qc, sim), shots=1).result()
        elapsed = round((time.time() - t0) * 1000, 2)
        bob_results = list(result.get_counts().keys())[0][::-1]
        bob_bits = [int(b) for b in bob_results]

        matching = [i for i in range(n_bits) if alice_bases[i] == bob_bases[i]]
        sifted_alice = [int(alice_bits[i]) for i in matching]
        sifted_bob = [bob_bits[i] for i in matching]

        artifacts.append(Artifact(
            type=ArtifactType.RESULTS,
            title="BB84 QKD — Key Exchange Results",
            content=json.dumps({
                "alice_bits": list(map(int, alice_bits)),
                "alice_bases": ["Z" if b == 0 else "X" for b in alice_bases],
                "bob_bases": ["Z" if b == 0 else "X" for b in bob_bases],
                "bob_results": bob_bits,
                "matching_positions": matching,
                "sifted_key_alice": sifted_alice,
                "sifted_key_bob": sifted_bob,
                "keys_match": sifted_alice == sifted_bob,
            }),
            metadata={
                "execution_time_ms": elapsed,
                "backend": "aer_simulator",
                "num_qubits": n_bits,
            },
        ))

        bases_a = ", ".join("Z" if b == 0 else "X" for b in alice_bases)
        bases_b = ", ".join("Z" if b == 0 else "X" for b in bob_bases)

        summary = (
            f"## BB84 Quantum Key Distribution\n\n"
            f"I've simulated the BB84 protocol with {n_bits} qubits.\n\n"
            f"**Alice's bases:** {bases_a}\n"
            f"**Bob's bases:** {bases_b}\n"
            f"**Matching positions:** {matching} ({len(matching)}/{n_bits} match)\n\n"
            f"**Sifted key (Alice):** `{''.join(map(str, sifted_alice))}`\n"
            f"**Sifted key (Bob):** `{''.join(map(str, sifted_bob))}`\n"
            f"**Keys match:** {'✅ Yes' if sifted_alice == sifted_bob else '❌ No'}\n\n"
            f"**Time:** {elapsed}ms\n\n"
            f"In a real deployment, Alice and Bob would then perform **error estimation** "
            f"and **privacy amplification** to distill a perfectly secure key."
        )
        return artifacts, summary

    except Exception:
        summary = (
            "## BB84 QKD Simulation\n\n"
            "I've generated the BB84 protocol simulation code. "
            "Check the artifact panel for the complete implementation."
        )
        return artifacts, summary


def _build_qrng_circuit() -> tuple[list[Artifact], str | None]:
    """Build and execute a QRNG circuit."""
    code = '''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Quantum Random Number Generator — 16 truly random bits
n_bits = 16
qc = QuantumCircuit(n_bits, n_bits)

# Apply Hadamard to each qubit: |0⟩ → |+⟩ = (|0⟩ + |1⟩)/√2
for i in range(n_bits):
    qc.h(i)

# Measure — each bit is provably random (Born rule)
qc.measure(range(n_bits), range(n_bits))

# Execute
sim = AerSimulator()
result = sim.run(transpile(qc, sim), shots=1).result()
random_bits = list(result.get_counts().keys())[0]

print(f"Quantum random bits: {random_bits}")
print(f"As integer: {int(random_bits, 2)}")
print(f"As hex: 0x{int(random_bits, 2):04x}")
print(f"Note: These bits are provably random via the Born rule")
'''

    from app.quantum.executor import QISKIT_AVAILABLE
    if not QISKIT_AVAILABLE:
        return [], None

    artifacts = [
        Artifact(
            type=ArtifactType.CODE,
            title="QRNG — Qiskit Code",
            content=code,
            language="python",
        ),
    ]

    try:
        from qiskit import QuantumCircuit as QC, transpile
        from qiskit_aer import AerSimulator
        import json
        import time

        n_bits = 16
        qc = QC(n_bits, n_bits)
        for i in range(n_bits):
            qc.h(i)
        qc.measure(range(n_bits), range(n_bits))

        sim = AerSimulator()
        t0 = time.time()
        result = sim.run(transpile(qc, sim), shots=10).result()
        elapsed = round((time.time() - t0) * 1000, 2)
        counts = result.get_counts()

        # Take first result as the random number
        random_bits = list(counts.keys())[0]
        random_int = int(random_bits, 2)

        artifacts.append(Artifact(
            type=ArtifactType.RESULTS,
            title="QRNG — Random Numbers Generated",
            content=json.dumps(counts),
            metadata={
                "execution_time_ms": elapsed,
                "backend": "aer_simulator",
                "num_qubits": n_bits,
            },
        ))

        # Show all 10 samples
        all_samples = [f"`{k}` ({int(k, 2)})" for k in list(counts.keys())[:5]]

        summary = (
            f"## Quantum Random Number Generator\n\n"
            f"Generated {n_bits}-bit quantum random numbers using Hadamard gates.\n\n"
            f"**Primary random value:** `{random_bits}` = **{random_int}** (0x{random_int:04x})\n\n"
            f"**Sample outputs:** {', '.join(all_samples)}\n\n"
            f"**Circuit:** {n_bits} qubits × H gate → measure\n"
            f"**Time:** {elapsed}ms\n\n"
            f"Each bit is provably random via the Born rule: "
            f"H|0⟩ = (|0⟩+|1⟩)/√2 gives exactly 50/50 probability."
        )
        return artifacts, summary

    except Exception:
        summary = (
            "## QRNG\n\n"
            "I've generated the quantum random number generator code. "
            "Check the artifact panel."
        )
        return artifacts, summary
