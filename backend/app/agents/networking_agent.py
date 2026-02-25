"""Milimo Quantum — Networking Agent.

Handles Quantum Networking, internet simulation, and teleportation queries.
"""
from __future__ import annotations

from app.models.schemas import Artifact, ArtifactType

QUICK_TOPICS: dict[str, str] = {
    "networking": """## Quantum Networking & Internet

Quantum networks transmit qubits between physically separated nodes, enabling secure communication and distributed quantum computing.

### Key Protocols
- **Entanglement Distribution**: Sharing Bell pairs between distant nodes.
- **Quantum Teleportation**: Sending an unknown quantum state using classical bits and pre-shared entanglement.
- **Entanglement Swapping**: Establishing entanglement between nodes that have never directly interacted (the basis of quantum repeaters).

### Simulation Tools
- **NetSquid**: Simulates quantum network performance with timing and physical noise parameters.
- **SquidASM**: Compiles quantum protocols to NetSquid for execution.
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "networking": ["network", "teleportation", "entanglement distribution", "repeater", "squidasm", "netsquid"],
}


def try_quick_topic(message: str) -> str | None:
    """Try to match a quick networking topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None

def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    return [], None
