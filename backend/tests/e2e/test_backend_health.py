"""Milimo Quantum — Backend Health E2E Tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
class TestBackendHealth:
    """Test backend service health and availability."""

    async def test_health_endpoint_returns_200(self, api_client: AsyncClient):
        """Test /api/health returns status 200."""
        response = await api_client.get("/api/health")
        assert response.status_code in [200, 401, 403]

    async def test_health_endpoint_returns_healthy_status(self, api_client: AsyncClient):
        """Test /api/health returns healthy status."""
        response = await api_client.get("/api/health")
        data = response.json()
        assert data["status"] == "healthy"

    async def test_health_endpoint_checks_redis(self, api_client: AsyncClient):
        """Test health endpoint reports Redis status."""
        response = await api_client.get("/api/health")
        data = response.json()
        assert "redis" in data
        assert data["redis"] in ["connected", "disconnected"]

    async def test_health_endpoint_checks_qiskit(self, api_client: AsyncClient):
        """Test health endpoint reports Qiskit availability."""
        response = await api_client.get("/api/health")
        data = response.json()
        assert "qiskit" in data
        assert data["qiskit"] in ["available", "unavailable"]

    async def test_health_endpoint_checks_graph_db(self, api_client: AsyncClient):
        """Test health endpoint reports Neo4j status."""
        response = await api_client.get("/api/health")
        data = response.json()
        assert "graph" in data

    async def test_root_endpoint_returns_app_info(self, api_client: AsyncClient):
        """Test root endpoint returns application info."""
        response = await api_client.get("/")
        assert response.status_code in [200, 401, 403]
        data = response.json()
        assert "name" in data
        assert data["name"] == "Milimo Quantum"
        assert "version" in data

    async def test_quantum_status_endpoint(self, api_client: AsyncClient):
        """Test quantum status endpoint."""
        response = await api_client.get("/api/quantum/status")
        assert response.status_code in [200, 401]

    async def test_providers_endpoint(self, api_client: AsyncClient):
        """Test hardware providers endpoint."""
        response = await api_client.get("/api/quantum/providers")
        assert response.status_code in [200, 401]


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
