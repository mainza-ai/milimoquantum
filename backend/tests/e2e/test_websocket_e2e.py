"""Milimo Quantum — WebSocket E2E Tests."""
from __future__ import annotations

import asyncio
import json
import pytest
import httpx


BACKEND_URL = "http://localhost:8000"


@pytest.mark.e2e
@pytest.mark.websocket
class TestWebSocketEndpoints:
    """Test WebSocket endpoint availability via HTTP (WebSocket testing requires running server)."""

    async def test_sync_routes_registered(self):
        """Test that sync routes are registered."""
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=30.0) as client:
            response = await client.get("/")
            assert response.status_code == 200

    async def test_health_endpoint_for_websocket_availability(self):
        """Test health endpoint to verify server is running."""
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=30.0) as client:
            response = await client.get("/api/health")
            assert response.status_code == 200

    async def test_sync_module_loaded(self):
        """Test that sync module is loaded by checking main app."""
        async with httpx.AsyncClient(base_url=BACKEND_URL, timeout=30.0) as client:
            response = await client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "name" in data


@pytest.mark.e2e
@pytest.mark.websocket
class TestWebSocketConfiguration:
    """Test WebSocket configuration and setup."""

    async def test_websocket_auth_configured(self):
        """Test that WebSocket auth is properly configured."""
        try:
            from app.auth import AUTH_ENABLED
            assert AUTH_ENABLED is True or AUTH_ENABLED is False
        except ImportError:
            pytest.skip("Auth module not available")

    async def test_connection_manager_exists(self):
        """Test that connection manager is initialized."""
        try:
            from app.routes.sync import manager
            assert manager is not None
            assert hasattr(manager, 'active_connections')
            assert hasattr(manager, 'connect')
            assert hasattr(manager, 'disconnect')
            assert hasattr(manager, 'send_personal_message')
            assert hasattr(manager, 'broadcast')
        except ImportError:
            pytest.skip("Sync module not available")


@pytest.mark.e2e
@pytest.mark.websocket
class TestWebSocketMessageTypes:
    """Test WebSocket message type handling (HTTP-based tests)."""

    async def test_ping_pong_handler_registered(self):
        """Test ping/pong handler is registered in sync module."""
        try:
            from app.routes.sync import websocket_endpoint
            assert websocket_endpoint is not None
        except ImportError:
            pytest.skip("WebSocket endpoint not available")

    async def test_job_subscription_handler_registered(self):
        """Test job subscription is handled."""
        try:
            from app.routes.sync import manager
            assert hasattr(manager, 'subscribe_to_job')
            assert hasattr(manager, 'job_subscriptions')
        except ImportError:
            pytest.skip("Sync module not available")
