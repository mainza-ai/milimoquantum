"""Milimo Quantum — D-Wave Annealing Agent.

Handles D-Wave, QUBO, and quantum annealing queries.
"""
from __future__ import annotations

from app.models.schemas import Artifact, ArtifactType

QUICK_TOPICS: dict[str, str] = {
    "dwave": """## D-Wave Quantum Annealing

Quantum annealing is distinct from gate-model computing. It solves optimization problems by finding the minimum energy state of a physically embedded Ising model or QUBO graph.

### Key Concepts
- **QUBO**: Quadratic Unconstrained Binary Optimization. Optimization variables mapped to {0,1} binary states.
- **Ising Model**: Variables mapped to {-1, +1} spins.
- **Minor Embedding**: The computational graph of the QUBO is mapped onto the physical topology of the D-Wave processor (e.g., Pegasus layout).

### D-Wave Ocean SDK Flow
```python
from dwave.system import DWaveSampler, EmbeddingComposite
import dimod

# Define QUBO dictionary: Q
Q = {(0, 0): -1, (1, 1): -1, (0, 1): 2}

# Run on D-Wave hardware (or SimulatedAnnealingSampler locally)
sampler = EmbeddingComposite(DWaveSampler())
sampleset = sampler.sample_qubo(Q, num_reads=10)
print(sampleset)
```
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "dwave": ["dwave", "annealing", "qubo", "ising", "ocean", "dimod", "pegasus", "minorminer"],
}

def try_quick_topic(message: str) -> str | None:
    """Try to match a quick dwave topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None

def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    return [], None
