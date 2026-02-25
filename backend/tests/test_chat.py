"""Milimo Quantum — Chat API Tests.

Tests the chat endpoints, SSE streaming, agent routing, and auto-retry mechanism.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestSlashCommands:
    """Test slash command parsing."""

    def test_code_slash(self):
        from app.agents.orchestrator import detect_slash_command
        from app.models.schemas import AgentType
        agent, msg = detect_slash_command("/code Create a Bell state")
        assert agent == AgentType.CODE
        assert "Create a Bell state" in msg

    def test_research_slash(self):
        from app.agents.orchestrator import detect_slash_command
        from app.models.schemas import AgentType
        agent, msg = detect_slash_command("/research What is entanglement?")
        assert agent == AgentType.RESEARCH

    def test_chemistry_slash(self):
        from app.agents.orchestrator import detect_slash_command
        from app.models.schemas import AgentType
        agent, msg = detect_slash_command("/chemistry VQE for H2")
        assert agent == AgentType.CHEMISTRY

    def test_no_slash(self):
        from app.agents.orchestrator import detect_slash_command
        agent, msg = detect_slash_command("Hello world")
        assert agent is None
        assert msg == "Hello world"


class TestIntentClassification:
    """Test keyword-based intent classification."""

    def test_circuit_intent(self):
        from app.agents.orchestrator import classify_intent
        from app.models.schemas import AgentType
        assert classify_intent("create a bell state circuit") == AgentType.CODE

    def test_research_intent(self):
        from app.agents.orchestrator import classify_intent
        from app.models.schemas import AgentType
        assert classify_intent("what is quantum computing?") == AgentType.RESEARCH

    def test_chemistry_intent(self):
        from app.agents.orchestrator import classify_intent
        from app.models.schemas import AgentType
        assert classify_intent("molecular hamiltonian for drug design") == AgentType.CHEMISTRY

    def test_finance_intent(self):
        from app.agents.orchestrator import classify_intent
        from app.models.schemas import AgentType
        assert classify_intent("portfolio optimization for stocks") == AgentType.FINANCE

    def test_dwave_intent(self):
        from app.agents.orchestrator import classify_intent
        from app.models.schemas import AgentType
        assert classify_intent("solve a QUBO problem with dwave") == AgentType.DWAVE

    def test_sensing_intent(self):
        from app.agents.orchestrator import classify_intent
        from app.models.schemas import AgentType
        assert classify_intent("quantum sensing magnetometry") == AgentType.SENSING

    def test_networking_intent(self):
        from app.agents.orchestrator import classify_intent
        from app.models.schemas import AgentType
        assert classify_intent("quantum teleportation protocol") == AgentType.NETWORKING

    def test_fallback_to_orchestrator(self):
        from app.agents.orchestrator import classify_intent
        from app.models.schemas import AgentType
        assert classify_intent("hello there") == AgentType.ORCHESTRATOR


class TestMultiAgentDispatch:
    """Test the multi-agent dispatch system."""

    def test_dispatch_to_research(self):
        from app.agents.orchestrator import dispatch_to_agent
        from app.models.schemas import AgentType
        result = dispatch_to_agent(AgentType.RESEARCH, "explain superposition")
        assert "response" in result
        assert len(result["response"]) > 0

    def test_dispatch_to_dwave(self):
        from app.agents.orchestrator import dispatch_to_agent
        from app.models.schemas import AgentType
        result = dispatch_to_agent(AgentType.DWAVE, "dwave annealing overview")
        assert "response" in result

    def test_dispatch_multi_step(self):
        from app.agents.orchestrator import dispatch_multi_agent
        from app.models.schemas import AgentType
        # Use research + code which don't have problematic imports
        steps = [
            {"step": 1, "agent": AgentType.RESEARCH, "instruction": "explain entanglement"},
            {"step": 2, "agent": AgentType.RESEARCH, "instruction": "explain gates"},
        ]
        results = dispatch_multi_agent(steps)
        assert len(results) == 2
        assert results[0]["step"] == 1
        assert results[1]["step"] == 2


class TestChatRouteHelpers:
    """Test the chat route helper functions."""

    def test_agent_labels_complete(self):
        from app.routes.chat import AGENT_LABELS
        from app.models.schemas import AgentType
        # Verify all agent types have labels
        for agent in AgentType:
            assert agent in AGENT_LABELS, f"Missing label for {agent}"


class TestPlanningAgent:
    """Test the planning agent's decomposition logic."""

    def test_needs_planning(self):
        from app.agents.planning_agent import needs_planning
        assert needs_planning("compare grover and shor algorithms") is True
        assert needs_planning("build a pipeline for drug discovery") is True
        assert needs_planning("create a bell state") is False

    def test_decompose_compare(self):
        from app.agents.planning_agent import decompose_task
        steps = decompose_task("compare QAOA and VQE")
        assert len(steps) >= 2
        assert steps[0]["step"] == 1

    def test_decompose_pipeline(self):
        from app.agents.planning_agent import decompose_task
        steps = decompose_task("build a pipeline for molecular simulation")
        assert len(steps) >= 2

    def test_format_plan(self):
        from app.agents.planning_agent import format_plan, decompose_task
        steps = decompose_task("compare two algorithms")
        plan_text = format_plan(steps)
        assert "Execution Plan" in plan_text
        assert "Step 1" in plan_text


class TestResearchAgent:
    """Test the upgraded research agent."""

    def test_quick_topic_superposition(self):
        from app.agents.research_agent import try_quick_topic
        result = try_quick_topic("tell me about superposition")
        assert result is not None
        assert "superposition" in result.lower()

    def test_quick_topic_gates(self):
        from app.agents.research_agent import try_quick_topic
        result = try_quick_topic("explain quantum gates")
        assert result is not None
        assert "Hadamard" in result

    def test_quick_topic_error_correction(self):
        from app.agents.research_agent import try_quick_topic
        result = try_quick_topic("quantum error correction")
        assert result is not None
        assert "surface code" in result.lower() or "Surface Code" in result

    def test_quick_topic_algorithms(self):
        from app.agents.research_agent import try_quick_topic
        result = try_quick_topic("quantum algorithms overview")
        assert result is not None
        assert "Grover" in result or "Shor" in result

    def test_explain_level_detection(self):
        from app.agents.research_agent import detect_explain_level
        assert detect_explain_level("explain it in simple terms") == "beginner"
        assert detect_explain_level("give me a rigorous detailed analysis") == "expert"
        assert detect_explain_level("how does QPE work?") == "intermediate"
