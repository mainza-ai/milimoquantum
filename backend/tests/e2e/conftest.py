"""Milimo Quantum — E2E Test Configuration & Fixtures."""
from __future__ import annotations

import asyncio
import os
import pytest
import httpx
import redis

pytestmark = pytest.mark.e2e


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "milimopassword")

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8081")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "milimo-realm")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "milimo-client")
TEST_USER = os.getenv("E2E_TEST_USER", "admin")
TEST_PASSWORD = os.getenv("E2E_TEST_PASSWORD", "admin")


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


@pytest.fixture(scope="session")
async def keycloak_token():
    """Get real token from Keycloak using password grant."""
    token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "password",
                "client_id": KEYCLOAK_CLIENT_ID,
                "username": TEST_USER,
                "password": TEST_PASSWORD,
                "scope": "openid profile email"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code != 200:
            pytest.skip(f"Failed to get Keycloak token: {response.status_code} - {response.text}")

        token_data = response.json()
        return token_data["access_token"]


@pytest.fixture(scope="session")
async def keycloak_refresh_token():
    """Get refresh token from Keycloak."""
    token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            token_url,
            data={
                "grant_type": "password",
                "client_id": KEYCLOAK_CLIENT_ID,
                "username": TEST_USER,
                "password": TEST_PASSWORD,
                "scope": "openid profile email"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code != 200:
            pytest.skip(f"Failed to get Keycloak token: {response.status_code}")

        token_data = response.json()
        return token_data["refresh_token"]


@pytest.fixture
async def authenticated_client(api_client, keycloak_token):
    """HTTP client with real Keycloak authentication."""
    api_client.headers["Authorization"] = f"Bearer {keycloak_token}"
    api_client.headers["X-Requested-With"] = "XMLHttpRequest"
    return api_client


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
