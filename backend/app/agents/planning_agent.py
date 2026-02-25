"""Milimo Quantum — Planning Agent.

Decomposes complex multi-step tasks into sub-task plans and orchestrates
sequential execution across domain agents.
"""
from __future__ import annotations

import logging
from app.models.schemas import AgentType

logger = logging.getLogger(__name__)


# Patterns that suggest a multi-step / planning task
PLANNING_TRIGGERS: list[str] = [
    "compare",
    "step by step",
    "step-by-step",
    "build a pipeline",
    "workflow",
    "plan for",
    "sequence of",
    "first then",
    "end to end",
    "end-to-end",
    "walk me through",
    "design a full",
]


def needs_planning(message: str) -> bool:
    """Determine if a message warrants multi-step planning."""
    lower = message.lower()
    return any(trigger in lower for trigger in PLANNING_TRIGGERS)


def decompose_task(message: str) -> list[dict]:
    """Break a complex request into ordered sub-tasks.

    Returns a list of step dicts: {agent, instruction, depends_on}
    """
    lower = message.lower()

    # ── Compare pattern ─────────────────────────────────
    if "compare" in lower:
        return [
            {
                "step": 1,
                "agent": AgentType.RESEARCH,
                "instruction": f"Explain the concepts being compared: {message}",
                "depends_on": None,
            },
            {
                "step": 2,
                "agent": AgentType.CODE,
                "instruction": "Generate Qiskit circuits to demonstrate each approach",
                "depends_on": 1,
            },
            {
                "step": 3,
                "agent": AgentType.ORCHESTRATOR,
                "instruction": "Synthesize the comparison with a clear recommendation",
                "depends_on": 2,
            },
        ]

    # ── Pipeline / workflow pattern ─────────────────────
    if any(kw in lower for kw in ["pipeline", "workflow", "end to end", "end-to-end"]):
        steps = []
        if any(kw in lower for kw in ["molecule", "drug", "chemistry", "vqe"]):
            steps = [
                {"step": 1, "agent": AgentType.RESEARCH, "instruction": "Explain the molecular simulation approach", "depends_on": None},
                {"step": 2, "agent": AgentType.CHEMISTRY, "instruction": "Set up the molecular Hamiltonian and ansatz", "depends_on": 1},
                {"step": 3, "agent": AgentType.CODE, "instruction": "Generate the complete Qiskit code", "depends_on": 2},
            ]
        elif any(kw in lower for kw in ["portfolio", "finance", "optimize"]):
            steps = [
                {"step": 1, "agent": AgentType.RESEARCH, "instruction": "Explain the optimization approach", "depends_on": None},
                {"step": 2, "agent": AgentType.FINANCE, "instruction": "Formulate the financial model", "depends_on": 1},
                {"step": 3, "agent": AgentType.OPTIMIZATION, "instruction": "Build the QAOA circuit", "depends_on": 2},
                {"step": 4, "agent": AgentType.CODE, "instruction": "Generate the complete implementation", "depends_on": 3},
            ]
        else:
            steps = [
                {"step": 1, "agent": AgentType.RESEARCH, "instruction": f"Research: {message}", "depends_on": None},
                {"step": 2, "agent": AgentType.CODE, "instruction": "Implement the solution in Qiskit", "depends_on": 1},
            ]
        return steps

    # ── Default: research → code ────────────────────────
    return [
        {"step": 1, "agent": AgentType.RESEARCH, "instruction": f"Analyze: {message}", "depends_on": None},
        {"step": 2, "agent": AgentType.CODE, "instruction": "Implement in Qiskit", "depends_on": 1},
    ]


def format_plan(steps: list[dict]) -> str:
    """Format a plan into a readable markdown response."""
    agent_names = {
        AgentType.ORCHESTRATOR: "Milimo",
        AgentType.CODE: "Code Agent",
        AgentType.RESEARCH: "Research Agent",
        AgentType.CHEMISTRY: "Chemistry Agent",
        AgentType.FINANCE: "Finance Agent",
        AgentType.OPTIMIZATION: "Optimization Agent",
    }

    lines = ["## Execution Plan\n"]
    lines.append("I've broken this task into the following steps:\n")
    for step in steps:
        agent_name = agent_names.get(step["agent"], "Agent")
        dep = f" *(depends on step {step['depends_on']})*" if step.get("depends_on") else ""
        lines.append(f"**Step {step['step']}** — {agent_name}{dep}")
        lines.append(f"> {step['instruction']}\n")

    lines.append("---\n")
    lines.append("*Executing each step below...*\n")
    return "\n".join(lines)
