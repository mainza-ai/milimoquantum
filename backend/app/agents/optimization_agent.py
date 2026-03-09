"""Milimo Quantum — Optimization Agent.

Handles combinatorial optimization: QAOA, Max-Cut, TSP, QUBO formulation.
Phase 2: Template-based with executable circuits.
"""
from __future__ import annotations

from app.models.schemas import Artifact, ArtifactType


# ── Quick-reference knowledge base ──────────────────────
QUICK_TOPICS: dict[str, str] = {
    "qaoa": """## QAOA — Quantum Approximate Optimization Algorithm

QAOA is the leading quantum algorithm for **combinatorial optimization** problems.

### How It Works

1. **Encode** the optimization problem as a cost Hamiltonian H_C
2. **Initialize** |+⟩^n (equal superposition of all solutions)
3. **Apply** alternating layers:
   - **Cost layer**: e^{-iγH_C} — encodes the problem
   - **Mixer layer**: e^{-iβH_M} — explores solution space
4. **Measure** → sample candidate solutions
5. **Classically optimize** γ, β to maximize cost function

### Circuit Structure (p layers)

```
|0⟩ ─ H ─ [Cost(γ₁)] ─ [Mixer(β₁)] ─ [Cost(γ₂)] ─ [Mixer(β₂)] ─ Measure
```

### Performance vs Depth

| p (layers) | Max-Cut approx. ratio | Circuit depth |
|---|---|---|
| 1 | ≥ 0.6924 | O(n²) |
| 2 | ≥ 0.7559 | O(n²) |
| ∞ | 1.0 (exact) | Exponential |

### Comparison to Classical

- **Gurobi/CPLEX**: Exact for small instances, exponential worst-case
- **QAOA (p=3)**: Good approximations, polynomial circuit depth
- **Breakeven**: Expected at ~100 error-corrected qubits

💡 *Try it*: `/optimize Solve Max-Cut for a 4-node graph`
""",

    "maxcut": """## Max-Cut Problem

Given a graph G = (V, E), partition vertices into two sets S and S̄ to **maximize** the number of edges crossing the partition.

### QUBO Formulation

$$C(x) = \\sum_{(i,j) \\in E} w_{ij} \\cdot x_i(1 - x_j) + x_j(1 - x_i)$$

where x_i ∈ {0, 1} indicates which set vertex i belongs to.

### Quantum Encoding

- Each vertex → 1 qubit
- Edge weights → ZZ interactions in cost Hamiltonian
- Cost Hamiltonian: $H_C = \\sum_{(i,j)} \\frac{w_{ij}}{2}(I - Z_i Z_j)$

### Example: 4-Node Graph

```
0 ─── 1
|  ×  |
3 ─── 2
```

Optimal cut: {0,2} vs {1,3} → 4 edges cut (all of them)
""",

    "tsp": """## Traveling Salesman Problem (TSP)

Find the shortest route visiting all N cities exactly once and returning to start.

### Quantum Encoding

- **N² qubits** for N cities (one-hot position encoding)
- Qubit (i,j) = 1 means "visit city i at step j"
- Constraints encoded as penalty terms in QUBO

### QUBO Formulation

$$H = A \\sum_v \\left(1 - \\sum_j x_{v,j}\\right)^2 + A \\sum_j \\left(1 - \\sum_v x_{v,j}\\right)^2 + B \\sum_{(u,v) \\in E} w_{uv} \\sum_j x_{u,j} x_{v,j+1}$$

### Scaling

| Cities | Qubits | Classical (Exact) | D-Wave | QAOA |
|---|---|---|---|---|
| 4 | 16 | 0.001s | 0.02s | Feasible |
| 10 | 100 | 3.6M permutations | Hybrid | Hard |
| 20 | 400 | 10¹⁸ permutations | Hybrid | Future |
| 50+ | 2500 | Intractable | Hybrid solver | Future |

### D-Wave vs Gate-Based

- **D-Wave**: Best for large QUBO problems (5000+ qubits), native annealing
- **QAOA**: More flexible, higher quality solutions, fewer qubits available
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "qaoa": ["qaoa", "quantum approximate", "approximate optimization"],
    "maxcut": ["max-cut", "maxcut", "max cut", "graph partition"],
    "tsp": ["tsp", "traveling salesman", "travelling salesman", "shortest route", "city tour"],
}


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick optimization topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None


# ── Quick circuit templates ─────────────────────────────
def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    """Try to generate an optimization-related circuit."""
    lower = message.lower()

    if any(kw in lower for kw in ["max-cut", "maxcut", "max cut", "graph"]):
        return _build_maxcut_circuit()
    if any(kw in lower for kw in ["tsp", "traveling", "travelling", "cities"]):
        return _build_tsp_demo()
    if any(kw in lower for kw in ["qaoa", "optimize"]):
        return _build_maxcut_circuit()

    return [], None


def _build_maxcut_circuit() -> tuple[list[Artifact], str | None]:
    """Build and execute a 4-node Max-Cut QAOA circuit."""
    from app.quantum.executor import QISKIT_AVAILABLE
    if not QISKIT_AVAILABLE:
        return [], None

    code = '''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np

# Max-Cut QAOA for a 4-node graph
# Graph: 0-1, 1-2, 2-3, 3-0, 0-2 (5 edges)
n_qubits = 4
edges = [(0,1), (1,2), (2,3), (3,0), (0,2)]
p = 2  # QAOA depth

qc = QuantumCircuit(n_qubits, n_qubits)

# Initial state: equal superposition
for i in range(n_qubits):
    qc.h(i)

# QAOA layers
for layer in range(p):
    gamma = np.pi / (3 * (layer + 1))
    beta = np.pi / (4 * (layer + 1))

    # Cost unitary: e^{-i*gamma*C}
    for (i, j) in edges:
        qc.rzz(2 * gamma, i, j)

    # Mixer unitary: e^{-i*beta*B}
    for i in range(n_qubits):
        qc.rx(2 * beta, i)

qc.measure(range(n_qubits), range(n_qubits))

# Simulate
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
result = simulator.run(transpiled, shots=4096).result()
counts = result.get_counts()

# Evaluate cuts
def count_cut(bitstring, edges):
    return sum(1 for i, j in edges if bitstring[i] != bitstring[j])

print("Max-Cut QAOA Results (4 nodes, 5 edges):")
for bs, cnt in sorted(counts.items(), key=lambda x: -x[1])[:5]:
    bits = bs.zfill(n_qubits)
    cut_size = count_cut(bits, edges)
    s0 = [str(i) for i, b in enumerate(reversed(bits)) if b == "0"]
    s1 = [str(i) for i, b in enumerate(reversed(bits)) if b == "1"]
    print(f"  {bs} ({cnt}/4096): cut={cut_size}, S0={{{','.join(s0)}}}, S1={{{','.join(s1)}}}")
'''

    artifacts = [
        Artifact(type=ArtifactType.CODE, title="Max-Cut QAOA — Qiskit Code", content=code, language="python"),
    ]

    try:
        from qiskit import QuantumCircuit as QC, transpile
        from qiskit_aer import AerSimulator
        import numpy as np
        import json
        import time

        n = 4
        edges = [(0,1), (1,2), (2,3), (3,0), (0,2)]
        qc = QC(n, n)
        for i in range(n): 
            qc.h(i)
        for layer in range(2):
            gamma = np.pi / (3 * (layer + 1))
            beta = np.pi / (4 * (layer + 1))
            for (i, j) in edges: 
                qc.rzz(2 * gamma, i, j)
            for i in range(n): 
                qc.rx(2 * beta, i)
        qc.measure(range(n), range(n))

        sim = AerSimulator()
        t0 = time.time()
        result = sim.run(transpile(qc, sim), shots=4096).result()
        elapsed = round((time.time() - t0) * 1000, 2)
        counts = result.get_counts()

        artifacts.append(Artifact(
            type=ArtifactType.RESULTS, title="Max-Cut QAOA — Results",
            content=json.dumps(counts),
            metadata={"shots": 4096, "execution_time_ms": elapsed, "backend": "aer_statevector", "num_qubits": n, "depth": qc.depth()},
        ))

        def count_cut(bs, edges):
            return sum(1 for i, j in edges if bs[i] != bs[j])

        top = sorted(counts.items(), key=lambda x: -x[1])[:3]
        cut_str = ""
        for bs, cnt in top:
            bits = bs.zfill(n)
            cut = count_cut(list(reversed(bits)), [(i,j) for i,j in edges])
            cut_str += f"- `{bs}` ({cnt} hits): **{cut} edges cut**\n"

        summary = (
            f"## Max-Cut QAOA (4 nodes, 5 edges)\n\n"
            f"Built and executed a 2-layer QAOA circuit for the Max-Cut problem.\n\n"
            f"**Graph:** 4 nodes, 5 edges (0-1, 1-2, 2-3, 3-0, 0-2)\n"
            f"**Circuit:** {n} qubits, depth {qc.depth()}, p=2\n"
            f"**Shots:** 4096 | **Time:** {elapsed}ms\n\n"
            f"**Top solutions:**\n{cut_str}\n"
            f"Optimal cut: 4 edges (e.g., {{0,2}} vs {{1,3}})"
        )
        return artifacts, summary

    except Exception:
        return artifacts, "## Max-Cut QAOA\n\nGenerated the QAOA circuit code. Check the artifact panel."


def _build_tsp_demo() -> tuple[list[Artifact], str | None]:
    """Build a TSP educational response with QAOA reference."""
    topic = QUICK_TOPICS["tsp"]
    return [], topic
