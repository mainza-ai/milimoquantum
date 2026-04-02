"""Milimo Quantum - Device Syncing Engine.

Manages WebSockets for real-time state broadcast and P2P connection logic.
"""
from __future__ import annotations

import logging
from typing import Dict

from app.auth import get_current_user, keycloak_openid, AUTH_ENABLED
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sync", tags=["sync"], dependencies=[Depends(get_current_user)])


class ConnectionManager:
    """Manages active websocket connections."""
    def __init__(self):
        # Maps client_id to their active websocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Maps job_id to client_id for job status updates
        self.job_subscriptions: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept connection and store."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        """Remove connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total: {len(self.active_connections)}")
        # Clean up job subscriptions
        jobs_to_remove = [jid for jid, cid in self.job_subscriptions.items() if cid == client_id]
        for jid in jobs_to_remove:
            del self.job_subscriptions[jid]

    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to an explicit client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict, exclude_client: str | None = None):
        """Send message to all open clients."""
        for client_id, connection in self.active_connections.items():
            if exclude_client is not None and client_id == exclude_client:
                continue
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to {client_id}: {e}")

    async def subscribe_to_job(self, job_id: str, client_id: str):
        """Subscribe a client to job status updates."""
        self.job_subscriptions[job_id] = client_id

    async def broadcast_job_status(self, job_id: str, status: dict):
        """Broadcast job status to subscribed client."""
        client_id = self.job_subscriptions.get(job_id)
        if client_id and client_id in self.active_connections:
            await self.active_connections[client_id].send_json({
                "type": "job_status",
                "job_id": job_id,
                **status
            })


manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: str = Query(None)):
    """WebSocket sync endpoint."""
    
    # 1. Authorize WebSocket via Query Token instead of Header
    if AUTH_ENABLED:
        if not token:
            await websocket.close(code=1008, reason="Missing token parameter")
            return
        try:
            public_key = "-----BEGIN PUBLIC KEY-----\n" + keycloak_openid.public_key() + "\n-----END PUBLIC KEY-----"
            options = {"verify_signature": True, "verify_aud": False, "exp": True}
            keycloak_openid.decode_token(token, key=public_key, options=options)
        except Exception as e:
            logger.warning(f"WS auth failed for {client_id}: {e}")
            await websocket.close(code=1008, reason="Invalid or expired token")
            return

    await manager.connect(websocket, client_id)
    try:
        while True:
            # Wait for any generic message from the client
            data = await websocket.receive_json()
            logger.debug(f"Received sync msg from {client_id}: {data.get('type')}")
            
        # Simple ping/pong check
        if data.get("type") == "ping":
            await manager.send_personal_message({"type": "pong"}, client_id)
        elif data.get("type") == "broadcast":
            # Relay broadcast to other clients (a peer to peer mimic)
            await manager.broadcast(
                {"type": "peer_message", "from": client_id, "data": data.get("data")},
                exclude_client=client_id
            )
        elif data.get("type") == "subscribe_job":
            # Subscribe to job status updates
            job_id = data.get("job_id")
            if job_id:
                await manager.subscribe_to_job(job_id, client_id)
                await manager.send_personal_message({
                    "type": "subscribed",
                    "job_id": job_id
                }, client_id)
                 
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast({"type": "client_disconnected", "client_id": client_id})
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)
