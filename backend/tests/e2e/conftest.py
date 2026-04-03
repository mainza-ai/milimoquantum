"""Milimo Quantum — E2E Test Configuration & Fixtures."""
from __future__ import annotations

import asyncio
import os
import pytest
import httpx
import redis
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.e2e


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "milimopassword")


@pytest.fixture(scope="session")
def backend_url():
    """Backend URL from environment."""
    return BACKEND_URL


@pytest.fixture(scope="session")
def frontend_url():
    """Frontend URL from environment."""
    return FRONTEND_URL


@pytest.fixture
async def api_client(backend_url):
    """Async HTTP client for API testing."""
    async with httpx.AsyncClient(base_url=backend_url, timeout=60.0) as client:
        yield client


@pytest.fixture
def redis_client():
    """Redis client for cache testing."""
    try:
        client = redis.from_url(REDIS_URL)
        client.ping()
        yield client
        client.close()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest.fixture
def neo4j_driver():
    """Neo4j driver for graph database testing."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        yield driver
        driver.close()
    except ImportError:
        pytest.skip("neo4j driver not installed")
    except Exception as e:
        pytest.skip(f"Neo4j not available: {e}")


@pytest.fixture
async def auth_token(api_client):
    """Get authentication token for protected endpoints."""
    import time
    import jwt
    
    payload = {
        "sub": "test_user",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "aud": "account",
        "iss": "http://localhost:8081/realms/milimo-realm"
    }
    secret = "your-256-bit-secret"
    token = jwt.encode(payload, secret, algorithm="HS256")
    return f"Bearer {token}"


@pytest.fixture
async def authenticated_client(api_client, auth_token):
    """HTTP client with authentication headers."""
    api_client.headers["Authorization"] = auth_token
    return api_client


@pytest.fixture
def mock_nvidia_nim():
    """Mock NVIDIA NIM responses for testing."""
    mock_responses = {
        "chat": {
            "choices": [{"message": {"content": "Test quantum response"}}]
        },
        "complete": {
            "text": "This is a test completion from NVIDIA NIM."
        }
    }
    
    with patch("app.llm.cloud_provider.NVIDIA_NIM_CLIENT") as mock_client:
        mock_client.chat = AsyncMock(return_value=mock_responses["chat"])
        mock_client.complete = AsyncMock(return_value=mock_responses["complete"])
        yield mock_client


@pytest.fixture
def mock_qiskit_execution():
    """Mock Qiskit circuit execution for fast testing."""
    mock_result = {
        "counts": {"00": 512, "11": 512},
        "shots": 1024,
        "backend": "aer_simulator",
        "status": "SUCCESS"
    }
    
    with patch("app.quantum.executor.run_circuit") as mock_run:
        mock_run.return_value = mock_result
        yield mock_run


@pytest.fixture
def clean_redis_cache(redis_client):
    """Clean Redis cache before/after tests."""
    keys = redis_client.keys("milimo:*")
    if keys:
        redis_client.delete(*keys)
    yield
    keys = redis_client.keys("milimo:*")
    if keys:
        redis_client.delete(*keys)


@pytest.fixture
def clean_neo4j_graph(neo4j_driver):
    """Clean Neo4j test data before/after tests."""
    def cleanup():
        with neo4j_driver.session() as session:
            session.run("MATCH (n:TestNode) DETACH DELETE n")
    
    cleanup()
    yield
    cleanup()


def pytest_collection_modifyitems(config, items):
    """Add E2E marker to all tests in this directory."""
    e2e_marker = pytest.mark.e2e
    
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(e2e_marker)
