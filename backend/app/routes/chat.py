"""Milimo Quantum — Chat Routes with SSE streaming.

Architecture:
  1. LLM with domain-specific system prompts generates dynamic responses
     with runnable Qiskit code blocks.
  2. Sandbox extracts and executes any code blocks from the LLM response,
     capturing circuits and measurements as artifacts.
  3. Artifacts stream to the frontend alongside the explanation text.

Every response is unique, dynamic, and contextual — no static shortcuts.
"""
from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents.orchestrator import (
    SYSTEM_PROMPTS,
    classify_intent,
    detect_slash_command,
)
from app.quantum.sandbox import execute_and_build_artifacts
from app.llm.ollama_client import ollama_client
from app.models.schemas import AgentType, ChatRequest
from app import storage

# Agent type → human-readable label for artifact titles
AGENT_LABELS: dict[AgentType, str] = {
    AgentType.CODE: "Code Agent",
    AgentType.RESEARCH: "Research",
    AgentType.CHEMISTRY: "Chemistry",
    AgentType.FINANCE: "Finance",
    AgentType.OPTIMIZATION: "Optimization",
    AgentType.CRYPTO: "Cryptography",
    AgentType.QML: "Quantum ML",
    AgentType.CLIMATE: "Climate & Materials",
    AgentType.QGI: "Graph Intelligence",
    AgentType.SENSING: "Quantum Sensing",
    AgentType.NETWORKING: "Quantum Networking",
    AgentType.DWAVE: "D-Wave Annealing",
    AgentType.PLANNING: "Planning",
    AgentType.ORCHESTRATOR: "Milimo Quantum",
}

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory store (backed by file persistence)
conversations: dict[str, list[dict]] = {}


def _load_or_init(conversation_id: str) -> list[dict]:
    """Load conversation from memory or disk."""
    if conversation_id in conversations:
        return conversations[conversation_id]
    saved = storage.load_conversation(conversation_id)
    if saved and "messages" in saved:
        conversations[conversation_id] = saved["messages"]
        return conversations[conversation_id]
    conversations[conversation_id] = []
    return conversations[conversation_id]


@router.post("/send")
async def send_message(request: ChatRequest):
    """Send a message and get a streaming SSE response."""
    conversation_id = request.conversation_id or str(uuid.uuid4())
    msgs = _load_or_init(conversation_id)

    # Detect agent
    agent_type = request.agent or classify_intent(request.message)
    _, clean_message = detect_slash_command(request.message)

    # Store user message
    msgs.append({"role": "user", "content": request.message})

    async def event_stream():
        """Generate SSE events."""

        # ── Step 1: LLM with domain-specific system prompt ────
        # Every agent has a detailed system prompt that instructs
        # the LLM to generate runnable Qiskit code. The LLM is
        # the brain — it decides what circuit to build based on
        # the user's request. Every response is unique.
        system_prompt = SYSTEM_PROMPTS.get(agent_type, SYSTEM_PROMPTS[AgentType.ORCHESTRATOR])
        history = msgs[-20:]

        full_response = ""
        async for token in ollama_client.stream_chat(messages=history, system_prompt=system_prompt):
            full_response += token
            yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"

        msgs.append({"role": "assistant", "content": full_response})

        # ── Step 2: Sandbox — Execute any code in the LLM response ──
        # The sandbox extracts ```python blocks, runs them safely, and
        # captures QuantumCircuit objects + measurement counts as artifacts.
        # This is what makes every agent dynamic — the LLM writes the
        # code, the sandbox executes it, artifacts appear in the UI.
        agent_label = AGENT_LABELS.get(agent_type, "Milimo Quantum")
        try:
            sandbox_artifacts, sandbox_error = execute_and_build_artifacts(
                full_response, agent_label=agent_label
            )
            for artifact in sandbox_artifacts:
                yield f"event: artifact\ndata: {json.dumps(artifact.model_dump(), default=str)}\n\n"
            if sandbox_error and not sandbox_artifacts:
                logger.warning(f"Sandbox error (no artifacts): {sandbox_error[:200]}")
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")

        storage.save_conversation(conversation_id, msgs)

        # ── Step 3: Auto-index for search ──
        try:
            from app.vector_store import index_conversation
            await index_conversation(conversation_id, msgs)
        except Exception:
            pass  # Search indexing is best-effort

        yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/conversations")
async def list_conversations_endpoint():
    """List all conversations (from disk)."""
    return {"conversations": storage.list_conversations()}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get messages for a conversation."""
    data = storage.load_conversation(conversation_id)
    if data and "messages" in data:
        return {"messages": data["messages"], "title": data.get("title", "Untitled")}
    return {"messages": []}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    if conversation_id in conversations:
        del conversations[conversation_id]
    success = storage.delete_conversation(conversation_id)
    return {"deleted": success}


def _chunk_text(text: str, chunk_size: int = 4) -> list[str]:
    """Split text into small chunks for simulated streaming."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
