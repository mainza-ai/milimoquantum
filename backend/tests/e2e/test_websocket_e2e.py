"""Milimo Quantum — WebSocket E2E Tests."""
from __future__ import annotations

import asyncio
import json
import pytest
import websockets


WEBSOCKET_URL = "ws://localhost:8000/sync/ws"


@pytest.mark.e2e
@pytest.mark.websocket
class TestWebSocketConnection:
    """Test WebSocket connectivity with real authentication."""

    async def test_websocket_connection(self, keycloak_token):
        """Test basic WebSocket connection with real token."""
        uri = f"{WEBSOCKET_URL}/test_client?token={keycloak_token}"
        try:
            async with websockets.connect(uri, close_timeout=5) as ws:
                assert ws.open
        except Exception as e:
            pytest.fail(f"WebSocket connection failed: {e}")

    async def test_websocket_ping_pong(self, keycloak_token):
        """Test WebSocket ping/pong."""
        uri = f"{WEBSOCKET_URL}/test_client_ping?token={keycloak_token}"
        try:
            async with websockets.connect(uri, close_timeout=10) as ws:
                await ws.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(response)
                assert data.get("type") == "pong"
        except Exception as e:
            pytest.fail(f"WebSocket ping/pong failed: {e}")

    async def test_websocket_broadcast(self, keycloak_token):
        """Test WebSocket broadcast message."""
        uri = f"{WEBSOCKET_URL}/test_client_broadcast?token={keycloak_token}"
        try:
            async with websockets.connect(uri, close_timeout=10) as ws:
                await ws.send(json.dumps({
                    "type": "broadcast",
                    "data": {"message": "test"}
                }))
        except Exception as e:
            pytest.fail(f"WebSocket broadcast failed: {e}")


@pytest.mark.e2e
@pytest.mark.websocket
class TestWebSocketJobSync:
    """Test WebSocket job synchronization."""

    async def test_job_subscription(self, keycloak_token):
        """Test subscribing to job updates."""
        uri = f"{WEBSOCKET_URL}/job_client_1?token={keycloak_token}"
        try:
            async with websockets.connect(uri, close_timeout=10) as ws:
                await ws.send(json.dumps({
                    "type": "subscribe_job",
                    "job_id": "test_job_123"
                }))
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(response)
                assert data.get("type") == "subscribed"
        except Exception as e:
            pytest.fail(f"Job subscription failed: {e}")

    async def test_multiple_subscriptions(self, keycloak_token):
        """Test multiple job subscriptions."""
        uri = f"{WEBSOCKET_URL}/job_client_multi?token={keycloak_token}"
        try:
            async with websockets.connect(uri, close_timeout=10) as ws:
                job_ids = ["job_1", "job_2", "job_3"]
                for job_id in job_ids:
                    await ws.send(json.dumps({
                        "type": "subscribe_job",
                        "job_id": job_id
                    }))
                    response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(response)
                    assert data.get("type") == "subscribed"
        except Exception as e:
            pytest.fail(f"Multiple subscriptions failed: {e}")


@pytest.mark.e2e
@pytest.mark.websocket
class TestWebSocketReconnection:
    """Test WebSocket reconnection behavior."""

    async def test_connection_close_and_reconnect(self, keycloak_token):
        """Test connection close and reconnect."""
        uri = f"{WEBSOCKET_URL}/reconnect_client?token={keycloak_token}"
        try:
            async with websockets.connect(uri, close_timeout=5) as ws:
                await ws.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(response)
                assert data.get("type") == "pong"

            await asyncio.sleep(0.5)

            async with websockets.connect(uri, close_timeout=5) as ws:
                await ws.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(response)
                assert data.get("type") == "pong"
        except Exception as e:
            pytest.fail(f"Reconnection test failed: {e}")


@pytest.mark.e2e
@pytest.mark.websocket
class TestWebSocketErrors:
    """Test WebSocket error handling."""

    async def test_invalid_message_format(self, keycloak_token):
        """Test handling invalid message format."""
        uri = f"{WEBSOCKET_URL}/error_client?token={keycloak_token}"
        try:
            async with websockets.connect(uri, close_timeout=5) as ws:
                await ws.send("not json")
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            pytest.fail(f"Invalid message test failed: {e}")

    async def test_unknown_message_type(self, keycloak_token):
        """Test handling unknown message type."""
        uri = f"{WEBSOCKET_URL}/unknown_client?token={keycloak_token}"
        try:
            async with websockets.connect(uri, close_timeout=5) as ws:
                await ws.send(json.dumps({"type": "unknown_type"}))
        except Exception as e:
            pytest.fail(f"Unknown type test failed: {e}")
