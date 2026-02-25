"""Milimo Quantum — QGI Agent.

Handles Quantum Graph Intelligence queries.
"""
from __future__ import annotations

from app.models.schemas import Artifact, ArtifactType

QUICK_TOPICS: dict[str, str] = {
    "qgi": """## Quantum Graph Intelligence (QGI)

QGI integrates quantum computing with graph databases (Neo4j, FalkorDB).

### How It Works
- **Circuit Representation**: Quantum circuits are inherently directional graphs. Representing them in Neo4j allows graph algorithms to find optimal topologies or subgraph isomorphisms for transpilation.
- **GraphRAG for Quantum**: Using FalkorDB/Graphiti, agent memories and knowledge are structured as semantic graphs, improving context retrieval for complex domain physics.
- **QAOA Graph Mapping**: Combinatorial problems (like Max-Cut/TSP) naturally map to graph structures. QGI provides seamless conversion between Cypher queries and QUBO matrices.
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "qgi": ["qgi", "graph", "neo4j", "falkordb", "graphrag", "subgraph"],
}

def try_quick_topic(message: str) -> str | None:
    """Try to match a quick QGI topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None

def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    return [], None
