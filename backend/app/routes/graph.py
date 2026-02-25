"""Milimo Quantum — Graph Intelligence Routes.

API endpoints for the quantum knowledge graph (Neo4j) and agent memory system.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter

from app.graph.neo4j_client import neo4j_client
from app.graph.agent_memory import agent_memory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/status")
async def graph_status():
    """Get graph and memory system status."""
    return {
        "neo4j": neo4j_client.get_status(),
        "memory": agent_memory.get_status(),
    }


@router.get("/query")
async def graph_query(cypher: str, limit: int = 25):
    """Execute a read-only Cypher query against the knowledge graph."""
    if not neo4j_client.connected:
        return {
            "error": "Neo4j not connected",
            "hint": "Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD env vars and restart",
            "results": [],
        }

    # Safety: only allow read queries
    upper = cypher.strip().upper()
    if any(kw in upper for kw in ["DELETE", "REMOVE", "DROP", "CREATE", "SET", "MERGE"]):
        return {"error": "Only read-only queries allowed via this endpoint", "results": []}

    results = await neo4j_client.execute_query(cypher)
    return {"results": results[:limit]}


@router.post("/index")
async def index_conversations():
    """Re-index all conversations into the knowledge graph."""
    from app import storage
    from pathlib import Path

    conversations_dir = Path.home() / ".milimoquantum" / "conversations"
    indexed = 0

    if conversations_dir.exists():
        import json
        for filepath in conversations_dir.glob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                conv_id = data.get("id", filepath.stem)
                messages = data.get("messages", [])
                agent = None
                for msg in messages:
                    if msg.get("agent"):
                        agent = msg["agent"]

                await neo4j_client.index_conversation(conv_id, messages, agent)
                indexed += 1
            except Exception:
                continue

    return {"indexed": indexed, "neo4j_connected": neo4j_client.connected}


@router.get("/related")
async def query_related(q: str, limit: int = 10):
    """Find related concepts and conversations via graph traversal."""
    results = await neo4j_client.query_related(q, limit)
    return {"query": q, "results": results}


@router.get("/stats")
async def graph_stats():
    """Get knowledge graph statistics."""
    return await neo4j_client.get_graph_stats()


# ── Agent Memory Endpoints ────────────────────────────

@router.get("/memory/status")
async def memory_status():
    """Get agent memory system status."""
    return {
        "status": agent_memory.get_status(),
        "agent_stats": agent_memory.get_agent_stats(),
    }


@router.get("/memory/{agent_type}")
async def get_agent_context(agent_type: str, query: str = "", limit: int = 5):
    """Retrieve relevant context for an agent."""
    if query:
        context = await agent_memory.retrieve_context(agent_type, query, limit)
    else:
        # Return recent memories
        memories = agent_memory._local.get(agent_type, [])
        context = memories[-limit:]

    return {"agent": agent_type, "context": context}
