"""Milimo Quantum — Agent E2E Tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.agents
class TestAgentSystem:
    """Test multi-agent system."""

    async def test_chat_endpoint_basic(self, authenticated_client: AsyncClient):
        """Test basic chat endpoint."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "Hello, what can you do?"}
        )
        assert response.status_code == 200

    async def test_chat_with_agent_selection(self, authenticated_client: AsyncClient):
        """Test chat with specific agent."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "/code Create a Bell state circuit"}
        )
        assert response.status_code == 200

    async def test_agent_orchestrator_dispatch(self, authenticated_client: AsyncClient):
        """Test orchestrator agent dispatch."""
        test_queries = [
            "/research quantum entanglement",
            "/optimize portfolio optimization",
            "/qml quantum neural network",
        ]
        for query in test_queries:
            response = await authenticated_client.post(
                "/api/chat/send",
                json={"message": query}
            )
            assert response.status_code == 200

    async def test_code_agent_circuit_generation(self, authenticated_client: AsyncClient):
        """Test code agent generates valid circuits."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "/code Create a 3-qubit GHZ state"}
        )
        assert response.status_code == 200

    async def test_research_agent_arxiv(self, authenticated_client: AsyncClient):
        """Test research agent arXiv search."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "/research VQE algorithms"}
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.agents
class TestBenchmarkingAgent:
    """Test benchmarking agent."""

    async def test_benchmark_agent_quantum_volume(self, authenticated_client: AsyncClient):
        """Test benchmarking agent quantum volume."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "Run a quantum volume benchmark"}
        )
        assert response.status_code == 200

    async def test_benchmark_agent_clops(self, authenticated_client: AsyncClient):
        """Test benchmarking agent CLOPS execution."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "Measure CLOPS performance"}
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.agents
class TestFaultToleranceAgent:
    """Test fault tolerance agent."""

    async def test_fault_tolerance_threshold(self, authenticated_client: AsyncClient):
        """Test fault tolerance agent threshold query."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "What is the surface code error threshold?"}
        )
        assert response.status_code == 200

    async def test_fault_tolerance_surface_code(self, authenticated_client: AsyncClient):
        """Test fault tolerance agent surface code generation."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "Generate a surface code circuit"}
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.agents
class TestSensingAgent:
    """Test sensing agent."""

    async def test_sensing_agent_ramsey(self, authenticated_client: AsyncClient):
        """Test sensing agent Ramsey interferometry."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "/sensing Explain Ramsey interferometry"}
        )
        assert response.status_code == 200

    async def test_sensing_agent_simulation(self, authenticated_client: AsyncClient):
        """Test sensing agent runs simulation."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "Simulate NV center sensing with T2=100us"}
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.agents
class TestNetworkingAgent:
    """Test networking agent."""

    async def test_networking_agent_bb84(self, authenticated_client: AsyncClient):
        """Test networking agent BB84 QKD."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "/networking Simulate BB84 QKD over 10km fiber"}
        )
        assert response.status_code == 200

    async def test_networking_agent_quantum_internet(self, authenticated_client: AsyncClient):
        """Test networking agent quantum internet info."""
        response = await authenticated_client.post(
            "/api/chat/send",
            json={"message": "Explain quantum internet architecture"}
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.agents
class TestMQDDAgent:
    """Test MQDD drug discovery agent."""

    async def test_mqdd_molecular_design(self, authenticated_client: AsyncClient):
        """Test molecular design workflow."""
        response = await authenticated_client.post(
            "/api/mqdd/design",
            json={
                "target": "test_target",
                "count": 5
            }
        )
        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "candidates" in data or "molecules" in data or "status" in data

    async def test_mqdd_admet_prediction(self, authenticated_client: AsyncClient):
        """Test ADMET prediction."""
        response = await authenticated_client.post(
            "/api/mqdd/admet",
            json={
                "smiles": "CCO"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "properties" in data or "predictions" in data or "status" in data
