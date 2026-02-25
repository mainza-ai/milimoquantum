"""Milimo Quantum — Sensing & Metrology Agent.

Handles queries on atom interferometry, magnetometry, and quantum sensing.
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

### Simulation Approach
These are typically simulated using specific Hamiltonians describing the interaction of the qubit state with the external classical field parameters over time.
""",
}

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "sensing": ["sensing", "metrology", "nv-center", "gravimeter", "interferometry", "magnetometry"],
}

def try_quick_topic(message: str) -> str | None:
    """Try to match a quick sensing topic."""
    lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return QUICK_TOPICS[topic]
    return None

def try_quick_circuit(message: str) -> tuple[list[Artifact], str | None]:
    return [], None
