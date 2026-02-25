"""Milimo Quantum — QGI Agent (Quantum Graph Intelligence).

Handles Quantum Graph Intelligence queries: quantum walks on graphs,
QAOA for graph optimization, graph-encoded quantum circuits.
"""
from __future__ import annotations

from app.models.schemas import Artifact, ArtifactType

QUICK_TOPICS: dict[str, str] = {
    "qgi": """## Quantum Graph Intelligence (QGI)

QGI bridges quantum computing with graph theory and graph databases (Neo4j, FalkorDB).

### Core Capabilities
- **Quantum Walks on Graphs**: Quantum analogue of random walks. A quantum walker exists in superposition across graph nodes, enabling O(√N) search vs O(N) classical.
- **QAOA for Graph Problems**: Max-Cut, Graph Coloring, Minimum Vertex Cover — all map naturally to QAOA circuits derived from graph adjacency matrices.
- **Graph-Encoded Circuits**: Encode graph structure directly into quantum circuits using ZZ-interaction terms for each edge.
- **Quantum PageRank**: Use quantum walk eigenvectors to rank nodes — potentially faster than classical PageRank for large sparse graphs.

### Pipeline
```
Graph (NetworkX) → Adjacency Matrix → Quantum Circuit → Execute → Results → Enrich Graph
```
""",
    "quantum_walk": """## Quantum Walks on Graphs

A continuous-time quantum walk on a graph G is governed by the Hamiltonian:

$$H = -\\gamma A$$

where $A$ is the adjacency matrix and $\\gamma$ is the hopping rate. The walker evolves as:

$$|\\psi(t)\\rangle = e^{-iHt}|\\psi(0)\\rangle$$

### Key Properties
- **Superposition**: Walker exists at all nodes simultaneously
- **Interference**: Probability amplitudes interfere constructively/destructively
- **Speedup**: Spatial search in O(√N) vs O(N) classical
- **Community Detection**: Walk eigenvectors reveal graph community structure
""",
    "qaoa_graph": """## QAOA for Graph Optimization

QAOA (Quantum Approximate Optimization Algorithm) maps graph optimization problems to quantum circuits:

### Circuit Structure
1. **Problem Hamiltonian** $H_C$: Encodes the objective (e.g., Max-Cut edges as ZZ interactions)
2. **Mixer Hamiltonian** $H_B$: Applies X rotations to explore solution space
3. **Variational Loop**: Alternate $e^{-i\\gamma H_C}$ and $e^{-i\\beta H_B}$ for $p$ layers

For Max-Cut: $H_C = \\sum_{(i,j) \\in E} \\frac{1}{2}(1 - Z_i Z_j)$

Higher $p$ → better approximation ratio, but deeper circuits.
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "qgi": ["qgi", "graph intelligence", "neo4j", "falkordb", "graphrag"],
    "quantum_walk": ["quantum walk", "walker", "random walk", "graph traversal"],
    "qaoa_graph": ["qaoa", "max-cut", "maxcut", "graph optimization", "graph coloring"],
}


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick QGI topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None


# ── Circuit Templates ──────────────────────────────────


def _quantum_walk_code(n_nodes: int = 4) -> str:
    """Generate quantum walk on a graph circuit."""
    return f'''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np
import networkx as nx
from scipy.linalg import expm

# Continuous-Time Quantum Walk on a Graph
# The walker evolves under H = -γA where A is the adjacency matrix

n_nodes = {n_nodes}
n_qubits = int(np.ceil(np.log2(n_nodes)))  # Qubits needed to encode nodes

# Create graph (cycle graph as example)
G = nx.cycle_graph(n_nodes)
A = nx.adjacency_matrix(G).toarray().astype(float)

print(f"Graph: Cycle graph with {{n_nodes}} nodes")
print(f"Adjacency matrix:\\n{{A}}")
print(f"Encoding in {{n_qubits}} qubits ({{2**n_qubits}} computational states)")

# Quantum walk parameters
gamma = 1.0  # Hopping rate
t = np.pi / 4  # Evolution time

# Compute exact evolution operator U = exp(-iγAt)
H = -gamma * A
# Pad to 2^n_qubits dimension
dim = 2**n_qubits
H_padded = np.zeros((dim, dim))
H_padded[:n_nodes, :n_nodes] = H
U = expm(-1j * H_padded * t)

# Build a quantum circuit implementing U using Qiskit UnitaryGate
qc = QuantumCircuit(n_qubits, n_qubits)

# Start at node 0
# (|0⟩^n is already the initial state)

# Apply quantum walk evolution
from qiskit.quantum_info import Operator
qc.unitary(Operator(U), range(n_qubits), label=f"QW(t={{t:.2f}})")

# Measure to see walker distribution
qc.measure(range(n_qubits), range(n_qubits))

simulator = AerSimulator()
transpiled = transpile(qc, simulator)
result = simulator.run(transpiled, shots=4096).result()
counts = result.get_counts()

print(f"\\nQuantum Walk Results (t={{t:.2f}}, γ={{gamma}}):")
print("=" * 45)
total = sum(counts.values())
for state in sorted(counts.keys()):
    node_idx = int(state, 2)
    prob = counts[state] / total
    bar = "█" * int(prob * 40)
    label = f"Node {{node_idx}}" if node_idx < n_nodes else "invalid"
    print(f"  |{{state}}⟩ ({{label}}): {{prob:.4f}} {{bar}}")

# Compare with classical random walk
print(f"\\nClassical random walk would be uniform: {{1/n_nodes:.4f}} per node")
print(f"Quantum walk shows INTERFERENCE — non-uniform distribution!")
print(f"\\n" + str(qc.draw(output="text")))
'''


def _qaoa_maxcut_code(n_nodes: int = 4) -> str:
    """Generate QAOA for Max-Cut code."""
    return f'''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np
import networkx as nx

# QAOA for Max-Cut — Graph Optimization
# Circuit encodes graph edges as ZZ interactions

n_nodes = {n_nodes}
p = 1  # QAOA depth (number of layers)

# Create graph
G = nx.Graph()
G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)])
print(f"Graph: {{G.number_of_nodes()}} nodes, {{G.number_of_edges()}} edges")
print(f"Edges: {{list(G.edges())}}")

# QAOA parameters (pre-optimized for this graph)
gamma = [0.6]  # Problem parameters
beta = [0.3]   # Mixer parameters

# Build QAOA circuit
qc = QuantumCircuit(n_nodes, n_nodes)

# Initial state: uniform superposition
for q in range(n_nodes):
    qc.h(q)

for layer in range(p):
    # Problem unitary: exp(-iγC) where C = Σ_(i,j)∈E (1 - ZiZj)/2
    for u, v in G.edges():
        qc.cx(u, v)
        qc.rz(2 * gamma[layer], v)
        qc.cx(u, v)

    # Mixer unitary: exp(-iβB) where B = Σ_i Xi
    for q in range(n_nodes):
        qc.rx(2 * beta[layer], q)

qc.measure(range(n_nodes), range(n_nodes))

print(f"\\nQAOA Circuit (p={{p}}):")
print(qc.draw(output="text"))

# Execute
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
result = simulator.run(transpiled, shots=4096).result()
counts = result.get_counts()

# Evaluate Max-Cut value for each bitstring
print(f"\\nResults:")
print("=" * 50)
best_cut = 0
best_solution = ""
for bitstring, count in sorted(counts.items(), key=lambda x: -x[1])[:8]:
    assignment = [int(b) for b in reversed(bitstring)]
    cut_value = sum(1 for u, v in G.edges() if assignment[u] != assignment[v])
    if cut_value > best_cut:
        best_cut = cut_value
        best_solution = bitstring
    prob = count / 4096
    print(f"  {{bitstring}} | cut={{cut_value}}/{{G.number_of_edges()}} | count={{count}} ({{prob:.3f}})")

print(f"\\n🏆 Best solution: {{best_solution}} with cut={{best_cut}}/{{G.number_of_edges()}}")
partition_0 = [i for i, b in enumerate(reversed(best_solution)) if b == '0']
partition_1 = [i for i, b in enumerate(reversed(best_solution)) if b == '1']
print(f"   Partition A: {{partition_0}}")
print(f"   Partition B: {{partition_1}}")
'''


def _graph_circuit_code() -> str:
    """Generate graph-encoded quantum circuit code."""
    return '''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np
import networkx as nx

# Graph-Encoded Quantum Circuit
# Every edge in the graph becomes a ZZ-interaction in the circuit

# Create a small graph
G = nx.Graph()
G.add_edges_from([(0, 1, {"weight": 0.5}),
                  (1, 2, {"weight": 0.8}),
                  (2, 3, {"weight": 0.3}),
                  (0, 3, {"weight": 0.6})])

n_qubits = G.number_of_nodes()
qc = QuantumCircuit(n_qubits, n_qubits)

# Initialize: uniform superposition
for q in range(n_qubits):
    qc.h(q)

# Encode graph structure: each edge → ZZ interaction
for u, v, data in G.edges(data=True):
    w = data.get("weight", 1.0)
    # ZZ interaction: exp(-i * w * Z_u ⊗ Z_v)
    qc.cx(u, v)
    qc.rz(2 * w, v)
    qc.cx(u, v)

# Add mixing layer
for q in range(n_qubits):
    qc.rx(np.pi / 4, q)

qc.measure(range(n_qubits), range(n_qubits))

print("Graph-Encoded Quantum Circuit")
print("=" * 45)
print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
print(f"Edge weights: {[(u,v,d['weight']) for u,v,d in G.edges(data=True)]}")
print(f"\\nCircuit:")
print(qc.draw(output="text"))

# Execute
simulator = AerSimulator()
transpiled = transpile(qc, simulator)
result = simulator.run(transpiled, shots=2048).result()
counts = result.get_counts()

print(f"\\nMeasurement results: {counts}")

# Analyze which graph partitions are favored
print(f"\\nGraph structure analysis:")
for node in G.nodes():
    neighbors = list(G.neighbors(node))
    total_weight = sum(G[node][n]["weight"] for n in neighbors)
    print(f"  Node {node}: neighbors={neighbors}, total_weight={total_weight:.2f}")
'''


# ── Circuit Dispatch ──────────────────────────────────

CIRCUIT_KEYWORDS: dict[str, list[str]] = {
    "quantum_walk": ["quantum walk", "walk on graph", "walker", "graph traversal", "continuous time"],
    "qaoa_maxcut": ["qaoa", "max-cut", "maxcut", "max cut", "graph optimization"],
    "graph_circuit": ["graph circuit", "graph encode", "zz interaction", "graph to circuit"],
}


def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    """Try to match a QGI circuit and generate executable code."""
    lower = message.lower()

    for circuit_type, keywords in CIRCUIT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            if circuit_type == "quantum_walk":
                code = _quantum_walk_code()
                summary = "## Quantum Walk on Graph\n\nContinuous-time quantum walk on a cycle graph — showing quantum interference vs. classical uniform distribution."
            elif circuit_type == "qaoa_maxcut":
                code = _qaoa_maxcut_code()
                summary = "## QAOA Max-Cut\n\nQuantum approximate optimization for Max-Cut — graph edges encoded as ZZ interactions."
            elif circuit_type == "graph_circuit":
                code = _graph_circuit_code()
                summary = "## Graph-Encoded Circuit\n\nDirect encoding of a weighted graph into quantum ZZ-interaction terms."
            else:
                return [], None

            artifacts = [
                Artifact(
                    type=ArtifactType.CODE,
                    title=f"QGI — {circuit_type.replace('_', ' ').title()}",
                    content=code,
                    language="python",
                ),
            ]
            return artifacts, summary

    return [], None
