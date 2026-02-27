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

    Returns a list of step dicts: {agent, instruction, depends_on, expected_output}
    """
    lower = message.lower()

    # ── Compare pattern ─────────────────────────────────
    if "compare" in lower:
        return [
            {
                "step": 1,
                "agent": AgentType.RESEARCH,
                "instruction": f"Explain the concepts being compared: {message}. Extract the distinct theoretical models.",
                "depends_on": None,
                "expected_output": ["theoretical_models", "comparison_metrics"]
            },
            {
                "step": 2,
                "agent": AgentType.CODE,
                "instruction": "Generate Qiskit circuits to demonstrate each approach identified.",
                "depends_on": 1,
                "expected_output": ["circuit_codes"]
            },
            {
                "step": 3,
                "agent": AgentType.ORCHESTRATOR,
                "instruction": "Synthesize the comparison with a clear recommendation.",
                "depends_on": 2,
                "expected_output": ["final_synthesis"]
            },
        ]

    # ── Pipeline / workflow pattern ─────────────────────
    if any(kw in lower for kw in ["pipeline", "workflow", "end to end", "end-to-end", "drug"]):
        steps = []
        if any(kw in lower for kw in ["molecule", "drug", "chemistry", "vqe", "affinity", "protein"]):
            steps = [
                {
                    "step": 1, 
                    "agent": AgentType.RESEARCH, 
                    "instruction": f"Research the molecular target for: {message}. Return the molecular structure details.",
                    "depends_on": None,
                    "expected_output": ["molecule_name", "smiles", "formula", "protein_target"]
                },
                {
                    "step": 2, 
                    "agent": AgentType.CHEMISTRY, 
                    "instruction": "Set up the molecular Hamiltonian and VQE ansatz for the identified molecule.", 
                    "depends_on": 1,
                    "expected_output": ["qubit_count", "hamiltonian_mapping", "ansatz_type"]
                },
                {
                    "step": 3, 
                    "agent": AgentType.CODE, 
                    "instruction": "Generate the complete Qiskit code to execute the VQE simulation.", 
                    "depends_on": 2,
                    "expected_output": ["circuit_code"]
                },
            ]
        elif any(kw in lower for kw in ["portfolio", "finance", "optimize"]):
            steps = [
                {"step": 1, "agent": AgentType.RESEARCH, "instruction": f"Explain the optimization approach for: {message}", "depends_on": None, "expected_output": ["optimization_strategy"]},
                {"step": 2, "agent": AgentType.FINANCE, "instruction": "Formulate the financial model based on the strategy.", "depends_on": 1, "expected_output": ["financial_model", "assets"]},
                {"step": 3, "agent": AgentType.OPTIMIZATION, "instruction": "Build the QAOA circuit definition.", "depends_on": 2, "expected_output": ["qaoa_parameters"]},
                {"step": 4, "agent": AgentType.CODE, "instruction": "Generate the complete implementation.", "depends_on": 3, "expected_output": ["circuit_code"]},
            ]
        else:
            steps = [
                {"step": 1, "agent": AgentType.RESEARCH, "instruction": f"Research: {message}", "depends_on": None, "expected_output": ["research_summary"]},
                {"step": 2, "agent": AgentType.CODE, "instruction": "Implement the solution in Qiskit", "depends_on": 1, "expected_output": ["circuit_code"]},
            ]
        return steps

    # ── Default: research → code ────────────────────────
    return [
        {"step": 1, "agent": AgentType.RESEARCH, "instruction": f"Analyze: {message}", "depends_on": None, "expected_output": ["analysis"]},
        {"step": 2, "agent": AgentType.CODE, "instruction": "Implement in Qiskit", "depends_on": 1, "expected_output": ["code"]},
    ]

def get_workflow_artifact(steps: list[dict], title: str = "Execution Pipeline") -> dict:
    """Generate a WORKFLOW artifact definition mapping the DAG."""
    nodes = []
    edges = []
    for step in steps:
        nodes.append({
            "id": str(step["step"]),
            "label": str(step.get("agent", "Agent").value).title() if hasattr(step.get("agent"), "value") else str(step.get("agent")),
            "description": step["instruction"],
            "expected_output": step.get("expected_output", [])
        })
        if step.get("depends_on"):
            edges.append({
                "source": str(step["depends_on"]),
                "target": str(step["step"])
            })
    
    import json
    return {
        "type": "workflow",
        "title": title,
        "content": json.dumps({"nodes": nodes, "edges": edges}),
        "language": "json"
    }


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
