"""Milimo Quantum — Backend Health E2E Tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestBackendHealth:
    """Test backend health endpoints."""

    async def test_health_endpoint_returns_200(self, api_client: AsyncClient):
        """Test /api/health returns status 200."""
        response = await api_client.get("/api/health")
        assert response.status_code == 200

    async def test_health_endpoint_returns_healthy_status(self, api_client: AsyncClient):
        """Test /api/health returns healthy status."""
        response = await api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["healthy", "ok", "UP"]

    async def test_health_endpoint_checks_redis(self, api_client: AsyncClient):
        """Test /api/health checks Redis connection."""
        response = await api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        services = data.get("services", data.get("components", {}))
        if "redis" in services:
            assert services["redis"].get("status") in ["healthy", "ok", "UP", "connected"]

    async def test_health_endpoint_checks_qiskit(self, api_client: AsyncClient):
        """Test /api/health checks Qiskit availability."""
        response = await api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        services = data.get("services", data.get("components", {}))
        if "qiskit" in services:
            assert services["qiskit"].get("status") in ["healthy", "ok", "UP", "available"]

    async def test_health_endpoint_checks_graph_db(self, api_client: AsyncClient):
        """Test /api/health checks graph database."""
        response = await api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        services = data.get("services", data.get("components", {}))
        if "graph_db" in services or "neo4j" in services:
            key = "graph_db" if "graph_db" in services else "neo4j"
            assert services[key].get("status") in ["healthy", "ok", "UP", "connected", "skipped"]

    async def test_root_endpoint_returns_app_info(self, api_client: AsyncClient):
        """Test root endpoint returns application info."""
        response = await api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Milimo Quantum"
        assert "version" in data

    async def test_quantum_status_endpoint(self, authenticated_client: AsyncClient):
        """Test quantum status endpoint."""
        response = await authenticated_client.get("/api/quantum/status")
        assert response.status_code == 200
        data = response.json()
        assert "ibm_quantum" in data or "qiskit_available" in data

    async def test_providers_endpoint(self, authenticated_client: AsyncClient):
        """Test hardware providers endpoint."""
        response = await authenticated_client.get("/api/quantum/providers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "providers" in data


@pytest.mark.e2e
class TestRedisConnection:
    """Test Redis connectivity."""

    def test_redis_ping(self, redis_client):
        """Test Redis PING command."""
        assert redis_client.ping() is True

    def test_redis_set_get(self, redis_client, clean_redis_cache):
        """Test Redis SET and GET operations."""
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        assert value == b"test_value"
        redis_client.delete("test_key")

    def test_redis_cache_layer(self, redis_client, clean_redis_cache):
        """Test cache layer key format."""
        from app.cache import cache_set, cache_get, CACHE_TTL_DEFAULT
        
        cache_set("test:sample", {"data": "test"}, ttl=CACHE_TTL_DEFAULT)
        result = cache_get("test:sample")
        assert result == {"data": "test"}


@pytest.mark.e2e
class TestNeo4jConnection:
    """Test Neo4j graph database connectivity."""

    def test_neo4j_ping(self, neo4j_driver):
        """Test Neo4j connection is alive."""
        with neo4j_driver.session() as session:
            result = session.run("RETURN 1 AS test")
            assert result.single()["test"] == 1

    def test_neo4j_version(self, neo4j_driver):
        """Test Neo4j version query."""
        with neo4j_driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
            record = result.single()
            assert "neo4j" in record["name"].lower()

    def test_neo4j_create_query_node(self, neo4j_driver, clean_neo4j_graph):
        """Test creating and querying a node."""
        with neo4j_driver.session() as session:
            session.run("""
                CREATE (n:TestNode {name: 'test_concept', type: 'quantum'})
                RETURN n
            """)
            result = session.run("""
                MATCH (n:TestNode {name: 'test_concept'})
                RETURN n.type AS type
            """)
            assert result.single()["type"] == "quantum"

    def test_neo4j_relationship(self, neo4j_driver, clean_neo4j_graph):
        """Test creating and querying relationships."""
        with neo4j_driver.session() as session:
            session.run("""
                CREATE (a:TestNode {name: 'concept_a'})
                CREATE (b:TestNode {name: 'concept_b'})
                CREATE (a)-[:RELATES_TO]->(b)
            """)
            result = session.run("""
                MATCH (a:TestNode {name: 'concept_a'})-[r:RELATES_TO]->(b:TestNode)
                RETURN type(r) AS rel_type, b.name AS target
            """)
            record = result.single()
            assert record["rel_type"] == "RELATES_TO"
            assert record["target"] == "concept_b"
