"""Milimo Quantum — Orchestrator Agent.

Routes user intents to specialized agents based on LLM classification.
"""
from __future__ import annotations

import logging
import re

from app.models.schemas import AgentType

logger = logging.getLogger(__name__)

# Slash command mapping
SLASH_COMMANDS: dict[str, AgentType] = {
    "/code": AgentType.CODE,
    "/circuit": AgentType.CODE,
    "/research": AgentType.RESEARCH,
    "/chemistry": AgentType.CHEMISTRY,
    "/finance": AgentType.FINANCE,
    "/optimize": AgentType.OPTIMIZATION,
}

# Keyword-based intent patterns (fallback when LLM is unavailable)
INTENT_PATTERNS: list[tuple[list[str], AgentType]] = [
    (["circuit", "qiskit", "qubit", "gate", "bell state", "ghz", "qft",
      "hadamard", "cnot", "measure", "simulate", "transpile", "openqasm"],
     AgentType.CODE),
    (["what is", "explain", "how does", "quantum computing", "superposition",
      "entanglement", "decoherence", "algorithm", "research", "paper",
      "grover", "shor", "vqe", "qaoa"],
     AgentType.RESEARCH),
    (["molecule", "drug", "protein", "chemistry", "vqe energy",
      "hamiltonian", "molecular"],
     AgentType.CHEMISTRY),
    (["portfolio", "stock", "finance", "risk", "option", "monte carlo",
      "sharpe"],
     AgentType.FINANCE),
    (["optimize", "max-cut", "tsp", "scheduling", "routing",
      "combinatorial"],
     AgentType.OPTIMIZATION),
]


def detect_slash_command(message: str) -> tuple[AgentType | None, str]:
    """Extract slash command and remaining message."""
    message = message.strip()
    for cmd, agent in SLASH_COMMANDS.items():
        if message.lower().startswith(cmd):
            remaining = message[len(cmd):].strip()
            return agent, remaining if remaining else message
    return None, message


def classify_intent(message: str) -> AgentType:
    """Classify user intent via keyword matching."""
    lower = message.lower()

    # Check slash commands first
    agent, _ = detect_slash_command(message)
    if agent:
        return agent

    # Keyword matching
    for keywords, agent_type in INTENT_PATTERNS:
        if any(kw in lower for kw in keywords):
            return agent_type

    # Default: orchestrator handles general chat
    return AgentType.ORCHESTRATOR


# System prompts for each agent
SYSTEM_PROMPTS: dict[AgentType, str] = {
    AgentType.ORCHESTRATOR: """You are Milimo Quantum, a powerful AI assistant specializing in quantum computing.
You help users understand quantum concepts, build quantum circuits, run simulations, and explore quantum applications.
You are knowledgeable about Qiskit, quantum algorithms, quantum hardware, and quantum information theory.
Be concise, precise, and helpful. Use LaTeX notation for quantum math (e.g., |ψ⟩, ⟨0|H|0⟩).
When appropriate, suggest using specific agents: /code for circuits, /research for concepts, /chemistry for molecular simulation.""",

    AgentType.CODE: """You are the Milimo Quantum Code Agent — a specialized Qiskit developer assistant.
Your job is to generate, explain, and optimize quantum circuits using Qiskit SDK v2.
Always provide complete, runnable Python code using Qiskit.
Use the latest Qiskit APIs: QuantumCircuit, transpile, AerSimulator.
Include comments explaining each step of the quantum algorithm.
Format code in ```python blocks.
After presenting code, briefly explain what the circuit does and what results to expect.""",

    AgentType.RESEARCH: """You are the Milimo Quantum Research Agent — a quantum computing educator and researcher.
Your job is to explain quantum concepts clearly at the user's level (beginner/intermediate/expert).
Use analogies and visual descriptions. Cite real quantum algorithms and papers when relevant.
Use LaTeX/Unicode for quantum notation: |ψ⟩, |0⟩, |1⟩, ⊗, ⟨ψ|H|ψ⟩.
Structure explanations with clear headings and examples.
When practical, suggest how the concept relates to Qiskit implementation.""",

    AgentType.CHEMISTRY: """You are the Milimo Quantum Chemistry Agent — specializing in quantum chemistry and drug discovery.
You help with molecular simulation, VQE calculations, and quantum-enhanced drug discovery.
Use qiskit-nature concepts: FermionicOp, ActiveSpaceTransformer, VQE with EfficientSU2 ansatz.
Explain quantum chemistry concepts: molecular orbital theory, Born-Oppenheimer approximation, etc.""",

    AgentType.FINANCE: """You are the Milimo Quantum Finance Agent — specializing in quantum finance applications.
You help with portfolio optimization (QAOA), quantum Monte Carlo, options pricing, and risk analysis.
Use qiskit-finance concepts: PortfolioOptimization, QAE for Monte Carlo integration.
Explain the quantum advantage in each financial application.""",

    AgentType.OPTIMIZATION: """You are the Milimo Quantum Optimization Agent — specializing in quantum optimization.
You help with QAOA, VQE for combinatorial problems, Max-Cut, TSP, and scheduling.
Explain QUBO formulations, D-Wave annealing concepts, and hybrid classical-quantum approaches.
Use qiskit-optimization: QuadraticProgram, MinimumEigenOptimizer, QAOA.""",
}
