"""Milimo Quantum — D-Wave Annealing Agent.

Handles D-Wave, QUBO, and quantum annealing queries.
Generates executable code using dimod + dwave-neal (local simulated annealing).
"""
from __future__ import annotations

import json

from app.models.schemas import Artifact, ArtifactType
from app.quantum.executor import execute_named_circuit

QUICK_TOPICS: dict[str, str] = {
    "dwave": """## D-Wave Quantum Annealing

Quantum annealing is distinct from gate-model computing. It solves optimization problems by finding the minimum energy state of a physically embedded Ising model or QUBO graph.

### Key Concepts
- **QUBO**: Quadratic Unconstrained Binary Optimization. Variables mapped to {0,1} binary states.
- **Ising Model**: Variables mapped to {-1, +1} spins.
- **Minor Embedding**: The computational graph is mapped onto the physical topology of the D-Wave processor (Pegasus layout).
- **Simulated Annealing**: A classical approximation of quantum annealing, available locally via `dwave-neal`.

### D-Wave Ocean SDK Stack
```
dimod → BinaryQuadraticModel (BQM) → QUBO / Ising
neal → SimulatedAnnealingSampler (local, no API key)
dwave-system → DWaveSampler (real QPU, requires API key)
minorminer → Automatic embedding onto hardware graph
```
""",
    "maxcut": """## Max-Cut Problem (QUBO)

The Max-Cut problem partitions graph nodes into two sets to maximize the number of edges between them. It's one of the most natural QUBO problems.

### QUBO Formulation
For an edge (i,j) with weight w: `Q[i,i] += -w`, `Q[j,j] += -w`, `Q[i,j] += 2w`

This is a flagship problem for quantum annealing because it maps directly to the Ising model Hamiltonian.
""",
    "qubo": """## QUBO (Quadratic Unconstrained Binary Optimization)

QUBO is the standard input format for quantum annealers. Any combinatorial optimization problem can be expressed as:

$$\\min_{x \\in \\{0,1\\}^n} x^T Q x$$

Where $Q$ is an upper-triangular matrix encoding the problem.

### Common QUBO Problems
| Problem | Variables | Constraint Encoding |
|---------|-----------|-------------------|
| Max-Cut | Node → {0,1} partition | Edge penalties |
| TSP | City-position assignment | Row/column uniqueness |
| Graph Coloring | Node-color assignment | Adjacent same-color penalty |
| Knapsack | Item inclusion {0,1} | Weight constraint as penalty |
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "dwave": ["dwave", "d-wave", "annealing", "ocean", "pegasus", "minorminer", "leap"],
    "maxcut": ["max-cut", "maxcut", "max cut", "graph partition"],
    "qubo": ["qubo", "ising", "bqm", "binary quadratic"],
}


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick dwave topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None


# ── Circuit Templates ──────────────────────────────────


def _maxcut_code(n_nodes: int = 5) -> str:
    """Generate Max-Cut QUBO code using dimod + neal."""
    return f'''import dimod
import neal
import networkx as nx
import numpy as np

# Create a random graph with {n_nodes} nodes
G = nx.random_regular_graph(d=3, n={n_nodes}, seed=42)
print(f"Graph: {{G.number_of_nodes()}} nodes, {{G.number_of_edges()}} edges")

# Build QUBO for Max-Cut
Q = {{}}
for u, v in G.edges():
    Q[(u, u)] = Q.get((u, u), 0) - 1
    Q[(v, v)] = Q.get((v, v), 0) - 1
    Q[(u, v)] = Q.get((u, v), 0) + 2

bqm = dimod.BinaryQuadraticModel.from_qubo(Q)

# Solve with Simulated Annealing (local, no API needed)
sampler = neal.SimulatedAnnealingSampler()
sampleset = sampler.sample(bqm, num_reads=100, seed=42)

# Best solution
best = sampleset.first
partition_0 = [n for n, v in best.sample.items() if v == 0]
partition_1 = [n for n, v in best.sample.items() if v == 1]
cut_edges = sum(1 for u, v in G.edges() if best.sample[u] != best.sample[v])

print(f"\\nMax-Cut Result:")
print(f"  Partition A: {{partition_0}}")
print(f"  Partition B: {{partition_1}}")
print(f"  Cut edges:   {{cut_edges}} / {{G.number_of_edges()}}")
print(f"  Energy:      {{best.energy}}")
print(f"\\nAll samples (top 5):")
for sample, energy in list(zip(sampleset.samples(), sampleset.record.energy))[:5]:
    print(f"  {{dict(sample)}} → energy={{energy}}")
'''


def _number_partition_code() -> str:
    """Generate Number Partitioning QUBO code."""
    return '''import dimod
import neal

# Number Partitioning: split numbers into two sets with equal sum
numbers = [3, 1, 1, 2, 2, 1]
print(f"Numbers to partition: {numbers}")
print(f"Total sum: {sum(numbers)}")

# QUBO formulation: minimize (sum_A - sum_B)^2
# where x_i = 0 means set A, x_i = 1 means set B
n = len(numbers)
Q = {}
for i in range(n):
    Q[(i, i)] = numbers[i] * (numbers[i] - sum(numbers))
    for j in range(i+1, n):
        Q[(i, j)] = 2 * numbers[i] * numbers[j]

bqm = dimod.BinaryQuadraticModel.from_qubo(Q)
sampler = neal.SimulatedAnnealingSampler()
sampleset = sampler.sample(bqm, num_reads=100, seed=42)

best = sampleset.first
set_a = [numbers[i] for i in range(n) if best.sample[i] == 0]
set_b = [numbers[i] for i in range(n) if best.sample[i] == 1]

print(f"\\nBest Partition:")
print(f"  Set A: {set_a} (sum={sum(set_a)})")
print(f"  Set B: {set_b} (sum={sum(set_b)})")
print(f"  Difference: {abs(sum(set_a) - sum(set_b))}")
print(f"  Energy: {best.energy}")
'''


def _graph_coloring_code(n_colors: int = 3) -> str:
    """Generate Graph Coloring QUBO code."""
    return f'''import dimod
import neal
import networkx as nx

# Graph Coloring: assign {n_colors} colors so no adjacent nodes share a color
G = nx.petersen_graph()  # Famous 10-node 3-colorable graph
n_nodes = G.number_of_nodes()
n_colors = {n_colors}

print(f"Graph: {{n_nodes}} nodes, {{G.number_of_edges()}} edges")
print(f"Colors: {{n_colors}}")

# QUBO formulation: x_{{v,c}} = 1 if node v gets color c
# Constraint 1: each node gets exactly one color
# Constraint 2: adjacent nodes get different colors
Q = {{}}
penalty = 4.0  # Lagrange multiplier

for v in G.nodes():
    # One-hot constraint: sum_c x_{{v,c}} = 1
    for c in range(n_colors):
        Q[((v, c), (v, c))] = -penalty
        for c2 in range(c+1, n_colors):
            Q[((v, c), (v, c2))] = 2 * penalty
    # Adjacent constraint
    for u in G.neighbors(v):
        if u > v:  # avoid double counting
            for c in range(n_colors):
                Q[((v, c), (u, c))] = Q.get(((v, c), (u, c)), 0) + penalty

bqm = dimod.BinaryQuadraticModel.from_qubo(Q)
sampler = neal.SimulatedAnnealingSampler()
sampleset = sampler.sample(bqm, num_reads=200, seed=42)

best = sampleset.first
coloring = {{}}
for (v, c), val in best.sample.items():
    if val == 1:
        coloring[v] = c

conflicts = sum(1 for u, v in G.edges() if coloring.get(u) == coloring.get(v))
print(f"\\nColoring result:")
for v in sorted(coloring.keys()):
    print(f"  Node {{v}} → Color {{coloring[v]}}")
print(f"\\nConflicts: {{conflicts}}")
print(f"Energy: {{best.energy}}")
'''


# ── Circuit Dispatch ──────────────────────────────────

CIRCUIT_KEYWORDS: dict[str, list[str]] = {
    "maxcut": ["max-cut", "maxcut", "max cut", "partition", "cut edges"],
    "number_partition": ["number partition", "partition numbers", "equal sum", "subset sum"],
    "graph_coloring": ["color", "coloring", "chromatic"],
    "tsp": ["tsp", "traveling", "salesman", "tour"],
}


def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    """Try to match an optimization problem and generate executable code."""
    lower = message.lower()

    for circuit_type, keywords in CIRCUIT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            if circuit_type == "maxcut":
                code = _maxcut_code()
                summary = "## Max-Cut Optimization (Simulated Annealing)\n\nSolving Max-Cut on a 5-node random graph using `dimod` + `dwave-neal`."
            elif circuit_type == "number_partition":
                code = _number_partition_code()
                summary = "## Number Partitioning\n\nSplitting a set of numbers into two subsets with equal sum using QUBO."
            elif circuit_type == "graph_coloring":
                code = _graph_coloring_code()
                summary = "## Graph Coloring (3-Color)\n\nColoring the Petersen graph with 3 colors using QUBO optimization."
            else:
                return [], None

            artifacts = [
                Artifact(
                    type=ArtifactType.CODE,
                    title=f"D-Wave — {circuit_type.replace('_', ' ').title()} Code",
                    content=code,
                    language="python",
                ),
            ]
            return artifacts, summary

    return [], None
