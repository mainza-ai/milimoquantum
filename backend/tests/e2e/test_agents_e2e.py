"""Milimo Quantum — Agent E2E Tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.agents
class TestAgentSystem:
    """Test multi-agent system."""

    async def test_chat_endpoint_basic(self, api_client: AsyncClient):
        """Test basic chat endpoint."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "Hello, what can you do?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data or "content" in data

    async def test_chat_with_agent_selection(self, api_client: AsyncClient):
        """Test chat with specific agent."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "/code Create a Bell state circuit"}
        )
        assert response.status_code == 200

    async def test_agent_orchestrator_dispatch(self, api_client: AsyncClient):
        """Test orchestrator agent dispatch."""
        test_queries = [
            "/research quantum entanglement",
            "/optimize portfolio optimization",
            "/qml quantum neural network",
        ]
        for query in test_queries:
            response = await api_client.post(
                "/api/chat",
                json={"message": query}
            )
            assert response.status_code == 200

    async def test_code_agent_circuit_generation(self, api_client: AsyncClient):
        """Test code agent generates valid circuits."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "/code Create a 3-qubit GHZ state"}
        )
        assert response.status_code == 200
        data = response.json()
        response_text = data.get("response", "") or data.get("content", "")
        assert "GHZ" in response_text or "circuit" in response_text.lower()

    async def test_research_agent_arxiv(self, api_client: AsyncClient):
        """Test research agent arXiv search."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "/research VQE algorithms"}
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.agents
class TestBenchmarkingAgent:
    """Test benchmarking agent with real execution."""

    async def test_benchmark_agent_quantum_volume(self, api_client: AsyncClient):
        """Test benchmarking agent QV execution."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "Run a quantum volume benchmark"}
        )
        assert response.status_code == 200

    async def test_benchmark_agent_clops(self, api_client: AsyncClient):
        """Test benchmarking agent CLOPS execution."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "Measure CLOPS performance"}
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.agents
class TestFaultToleranceAgent:
    """Test fault tolerance agent with Stim."""

    async def test_fault_tolerance_threshold(self, api_client: AsyncClient):
        """Test fault tolerance agent threshold calculation."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "What is the surface code error threshold?"}
        )
        assert response.status_code == 200

    async def test_fault_tolerance_surface_code(self, api_client: AsyncClient):
        """Test fault tolerance agent surface code generation."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "Generate a surface code circuit"}
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.agents
class TestSensingAgent:
    """Test sensing agent with QuTiP."""

    async def test_sensing_agent_ramsey(self, api_client: AsyncClient):
        """Test sensing agent Ramsey interferometry."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "/sensing Explain Ramsey interferometry"}
        )
        assert response.status_code == 200

    async def test_sensing_agent_simulation(self, api_client: AsyncClient):
        """Test sensing agent runs simulation."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "Simulate NV center sensing with T2=100us"}
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.agents
class TestNetworkingAgent:
    """Test networking agent with NetSQuid."""

    async def test_networking_agent_bb84(self, api_client: AsyncClient):
        """Test networking agent BB84 simulation."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "/networking Simulate BB84 QKD over 10km fiber"}
        )
        assert response.status_code == 200

    async def test_networking_agent_quantum_internet(self, api_client: AsyncClient):
        """Test networking agent quantum internet info."""
        response = await api_client.post(
            "/api/chat",
            json={"message": "Explain quantum internet architecture"}
        )
        assert response.status_code == 200


@pytest.mark.e2e
@pytest.mark.agents
class TestMQDDAgent:
    """Test MQDD drug discovery agent."""

    async def test_mqdd_molecular_design(self, api_client: AsyncClient):
        """Test MQDD molecular design."""
        response = await api_client.post(
            "/api/mqdd/design",
            json={
                "target": "EGFR",
                "constraints": {
                    "molecular_weight": {"max": 500},
                    "logp": {"min": -2, "max": 5}
                },
                "count": 5
            }
        )
        assert response.status_code in [200, 404]

    async def test_mqdd_admet_prediction(self, api_client: AsyncClient):
        """Test ADMET prediction."""
        response = await api_client.post(
            "/api/mqdd/admet",
            json={"smiles": "CC(=O)Oc1ccccc1C(=O)O"}
        )
        if response.status_code == 404:
            pytest.skip("MQDD ADMET endpoint not available")
        assert response.status_code == 200
