"""Milimo Quantum — Chat Routes with SSE streaming."""
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
from app.agents.code_agent import try_quick_circuit as code_quick_circuit
from app.agents.research_agent import try_quick_topic as research_quick_topic
from app.agents.chemistry_agent import (
    try_quick_circuit as chem_quick_circuit,
    try_quick_topic as chem_quick_topic,
)
from app.agents.finance_agent import (
    try_quick_circuit as finance_quick_circuit,
    try_quick_topic as finance_quick_topic,
)
from app.agents.optimization_agent import (
    try_quick_circuit as opt_quick_circuit,
    try_quick_topic as opt_quick_topic,
)
from app.agents.crypto_agent import (
    try_quick_circuit as crypto_quick_circuit,
    try_quick_topic as crypto_quick_topic,
)
from app.agents.qml_agent import (
    try_quick_circuit as qml_quick_circuit,
    try_quick_topic as qml_quick_topic,
)
from app.agents.climate_agent import (
    try_quick_circuit as climate_quick_circuit,
    try_quick_topic as climate_quick_topic,
)
from app.llm.ollama_client import ollama_client
from app.models.schemas import AgentType, ChatRequest
from app import storage

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
        # ── Code Agent ──────────────────────────────────
        if agent_type == AgentType.CODE:
            artifacts, summary = code_quick_circuit(clean_message)
            if summary:
                for artifact in artifacts:
                    yield f"event: artifact\ndata: {json.dumps(artifact.model_dump(), default=str)}\n\n"
                for chunk in _chunk_text(summary, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": summary})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return

        # ── Research Agent ──────────────────────────────
        if agent_type == AgentType.RESEARCH:
            topic = research_quick_topic(clean_message)
            if topic:
                for chunk in _chunk_text(topic, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": topic})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return

        # ── Chemistry Agent ─────────────────────────────
        if agent_type == AgentType.CHEMISTRY:
            # Try circuit first, then topic
            artifacts, summary = chem_quick_circuit(clean_message)
            if summary:
                for artifact in artifacts:
                    yield f"event: artifact\ndata: {json.dumps(artifact.model_dump(), default=str)}\n\n"
                for chunk in _chunk_text(summary, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": summary})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return
            topic = chem_quick_topic(clean_message)
            if topic:
                for chunk in _chunk_text(topic, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": topic})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return

        # ── Finance Agent ───────────────────────────────
        if agent_type == AgentType.FINANCE:
            artifacts, summary = finance_quick_circuit(clean_message)
            if summary:
                for artifact in artifacts:
                    yield f"event: artifact\ndata: {json.dumps(artifact.model_dump(), default=str)}\n\n"
                for chunk in _chunk_text(summary, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": summary})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return
            topic = finance_quick_topic(clean_message)
            if topic:
                for chunk in _chunk_text(topic, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": topic})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return

        # ── Optimization Agent ──────────────────────────
        if agent_type == AgentType.OPTIMIZATION:
            artifacts, summary = opt_quick_circuit(clean_message)
            if summary:
                for artifact in artifacts:
                    yield f"event: artifact\ndata: {json.dumps(artifact.model_dump(), default=str)}\n\n"
                for chunk in _chunk_text(summary, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": summary})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return
            topic = opt_quick_topic(clean_message)
            if topic:
                for chunk in _chunk_text(topic, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": topic})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return

        # ── Crypto Agent ─────────────────────────────────
        if agent_type == AgentType.CRYPTO:
            artifacts, summary = crypto_quick_circuit(clean_message)
            if summary:
                for artifact in artifacts:
                    yield f"event: artifact\ndata: {json.dumps(artifact.model_dump(), default=str)}\n\n"
                for chunk in _chunk_text(summary, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": summary})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return
            topic = crypto_quick_topic(clean_message)
            if topic:
                for chunk in _chunk_text(topic, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": topic})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return

        # ── QML Agent ────────────────────────────────────
        if agent_type == AgentType.QML:
            artifacts, summary = qml_quick_circuit(clean_message)
            if summary:
                for artifact in artifacts:
                    yield f"event: artifact\ndata: {json.dumps(artifact.model_dump(), default=str)}\n\n"
                for chunk in _chunk_text(summary, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": summary})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return
            topic = qml_quick_topic(clean_message)
            if topic:
                for chunk in _chunk_text(topic, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": topic})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return

        # ── Climate Agent ────────────────────────────────
        if agent_type == AgentType.CLIMATE:
            artifacts, summary = climate_quick_circuit(clean_message)
            if summary:
                for artifact in artifacts:
                    yield f"event: artifact\ndata: {json.dumps(artifact.model_dump(), default=str)}\n\n"
                for chunk in _chunk_text(summary, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": summary})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return
            topic = climate_quick_topic(clean_message)
            if topic:
                for chunk in _chunk_text(topic, 4):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"
                msgs.append({"role": "assistant", "content": topic})
                storage.save_conversation(conversation_id, msgs)
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return

        # ── LLM Fallback ────────────────────────────────
        system_prompt = SYSTEM_PROMPTS.get(agent_type, SYSTEM_PROMPTS[AgentType.ORCHESTRATOR])
        history = msgs[-20:]

        full_response = ""
        async for token in ollama_client.stream_chat(messages=history, system_prompt=system_prompt):
            full_response += token
            yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"

        msgs.append({"role": "assistant", "content": full_response})
        storage.save_conversation(conversation_id, msgs)
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
