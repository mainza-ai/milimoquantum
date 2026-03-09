"""Milimo Quantum — Agent Tests.

Tests that each agent's quick-topic and quick-circuit handlers work correctly.
"""
from __future__ import annotations



class TestAgentImports:
    """Test that all agents can be imported without errors."""

    def test_import_orchestrator(self):
        from app.agents.orchestrator import classify_intent, detect_slash_command
        assert classify_intent is not None
        assert detect_slash_command is not None

    def test_import_code_agent(self):
        from app.agents.code_agent import try_quick_circuit
        assert try_quick_circuit is not None

    def test_import_dwave_agent(self):
        from app.agents.dwave_agent import try_quick_circuit
        assert try_quick_circuit is not None

    def test_import_sensing_agent(self):
        from app.agents.sensing_agent import try_quick_circuit
        assert try_quick_circuit is not None

    def test_import_networking_agent(self):
        from app.agents.networking_agent import try_quick_circuit
        assert try_quick_circuit is not None

    def test_import_qgi_agent(self):
        from app.agents.qgi_agent import try_quick_circuit
        assert try_quick_circuit is not None


class TestOrchestrator:
    """Test the orchestrator's intent classifier and slash commands."""

    def test_slash_code(self):
        from app.agents.orchestrator import detect_slash_command
        from app.models.schemas import AgentType
        agent, msg = detect_slash_command("/code Create a Bell state")
        assert agent == AgentType.CODE
        assert "Create a Bell state" in msg

    def test_slash_dwave(self):
        from app.agents.orchestrator import detect_slash_command
        from app.models.schemas import AgentType
        agent, msg = detect_slash_command("/dwave solve max-cut")
        assert agent == AgentType.DWAVE

    def test_slash_sensing(self):
        from app.agents.orchestrator import detect_slash_command
        from app.models.schemas import AgentType
        agent, msg = detect_slash_command("/sensing magnetometry")
        assert agent == AgentType.SENSING

    def test_slash_networking(self):
        from app.agents.orchestrator import detect_slash_command
        from app.models.schemas import AgentType
        agent, msg = detect_slash_command("/networking bb84")
        assert agent == AgentType.NETWORKING

    def test_keyword_classification(self):
        from app.agents.orchestrator import classify_intent
        from app.models.schemas import AgentType
        assert classify_intent("create a bell state circuit") == AgentType.CODE
        assert classify_intent("what is quantum computing?") == AgentType.RESEARCH


class TestDWaveAgent:
    """Test D-Wave agent quick topics and circuits."""

    def test_quick_topic_dwave(self):
        from app.agents.dwave_agent import try_quick_topic
        result = try_quick_topic("Tell me about dwave annealing")
        assert result is not None
        assert "QUBO" in result

    def test_quick_topic_qubo(self):
        from app.agents.dwave_agent import try_quick_topic
        result = try_quick_topic("What is QUBO?")
        assert result is not None

    def test_quick_circuit_maxcut(self):
        from app.agents.dwave_agent import try_quick_circuit
        artifacts, summary = try_quick_circuit("solve max-cut for a graph")
        assert len(artifacts) >= 1
        assert "dimod" in artifacts[0].content

    def test_quick_circuit_no_match(self):
        from app.agents.dwave_agent import try_quick_circuit
        artifacts, summary = try_quick_circuit("what is the weather?")
        assert len(artifacts) == 0


class TestSensingAgent:
    """Test Sensing agent quick topics and circuits."""

    def test_quick_topic_sensing(self):
        from app.agents.sensing_agent import try_quick_topic
        result = try_quick_topic("Tell me about quantum sensing")
        assert result is not None

    def test_quick_topic_ramsey(self):
        from app.agents.sensing_agent import try_quick_topic
        result = try_quick_topic("Explain Ramsey interferometry")
        assert result is not None

    def test_quick_circuit_ramsey(self):
        from app.agents.sensing_agent import try_quick_circuit
        artifacts, summary = try_quick_circuit("simulate ramsey interferometry")
        assert len(artifacts) >= 1
        assert "Hadamard" in artifacts[0].content or "qc.h" in artifacts[0].content

    def test_quick_circuit_magnetometry(self):
        from app.agents.sensing_agent import try_quick_circuit
        artifacts, summary = try_quick_circuit("quantum magnetometry with GHZ")
        assert len(artifacts) >= 1


class TestNetworkingAgent:
    """Test Networking agent quick topics and circuits."""

    def test_quick_topic_bb84(self):
        from app.agents.networking_agent import try_quick_topic
        result = try_quick_topic("How does BB84 QKD work?")
        assert result is not None
        assert "sifting" in result.lower() or "BB84" in result

    def test_quick_circuit_bb84(self):
        from app.agents.networking_agent import try_quick_circuit
        artifacts, summary = try_quick_circuit("simulate BB84 key distribution")
        assert len(artifacts) >= 1

    def test_quick_circuit_teleportation(self):
        from app.agents.networking_agent import try_quick_circuit
        artifacts, summary = try_quick_circuit("quantum teleportation")
        assert len(artifacts) >= 1

    def test_quick_circuit_swapping(self):
        from app.agents.networking_agent import try_quick_circuit
        artifacts, summary = try_quick_circuit("entanglement swapping repeater")
        assert len(artifacts) >= 1


class TestQGIAgent:
    """Test QGI agent quick topics and circuits."""

    def test_quick_topic_qgi(self):
        from app.agents.qgi_agent import try_quick_topic
        result = try_quick_topic("Tell me about quantum graph intelligence")
        assert result is not None

    def test_quick_circuit_quantum_walk(self):
        from app.agents.qgi_agent import try_quick_circuit
        artifacts, summary = try_quick_circuit("quantum walk on a graph")
        assert len(artifacts) >= 1

    def test_quick_circuit_qaoa(self):
        from app.agents.qgi_agent import try_quick_circuit
        artifacts, summary = try_quick_circuit("QAOA for max-cut")
        assert len(artifacts) >= 1
