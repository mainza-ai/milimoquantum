"""Milimo Quantum — Chat Routes with SSE streaming."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents.orchestrator import (
    SYSTEM_PROMPTS,
    classify_intent,
    detect_slash_command,
)
from app.agents.code_agent import try_quick_circuit
from app.agents.research_agent import try_quick_topic
from app.llm.ollama_client import ollama_client
from app.models.schemas import (
    AgentType,
    Artifact,
    ChatMessage,
    ChatRequest,
    MessageRole,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory conversation store
conversations: dict[str, list[dict]] = {}


@router.post("/send")
async def send_message(request: ChatRequest):
    """Send a message and get a streaming SSE response."""
    conversation_id = request.conversation_id or str(uuid.uuid4())

    if conversation_id not in conversations:
        conversations[conversation_id] = []

    # Detect agent
    agent_type = request.agent or classify_intent(request.message)
    _, clean_message = detect_slash_command(request.message)

    # Store user message
    conversations[conversation_id].append({
        "role": "user",
        "content": request.message,
    })

    async def event_stream():
        """Generate SSE events."""
        # First, check if code agent can handle this directly
        if agent_type == AgentType.CODE:
            artifacts, summary = try_quick_circuit(clean_message)
            if summary:
                # Send artifacts first
                for artifact in artifacts:
                    yield f"event: artifact\ndata: {json.dumps(artifact.model_dump(), default=str)}\n\n"

                # Stream the summary text
                for char_chunk in _chunk_text(summary, 4):
                    yield f"event: token\ndata: {json.dumps({'content': char_chunk})}\n\n"

                conversations[conversation_id].append({
                    "role": "assistant",
                    "content": summary,
                })
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return

        # Check research agent quick topics
        if agent_type == AgentType.RESEARCH:
            topic_response = try_quick_topic(clean_message)
            if topic_response:
                for char_chunk in _chunk_text(topic_response, 4):
                    yield f"event: token\ndata: {json.dumps({'content': char_chunk})}\n\n"

                conversations[conversation_id].append({
                    "role": "assistant",
                    "content": topic_response,
                })
                yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"
                return

        # Fall through to LLM
        system_prompt = SYSTEM_PROMPTS.get(agent_type, SYSTEM_PROMPTS[AgentType.ORCHESTRATOR])

        # Build message history (last 20 messages for context)
        history = conversations[conversation_id][-20:]

        full_response = ""
        async for token in ollama_client.stream_chat(
            messages=history,
            system_prompt=system_prompt,
        ):
            full_response += token
            yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"

        # Store assistant response
        conversations[conversation_id].append({
            "role": "assistant",
            "content": full_response,
        })

        yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'agent': agent_type.value})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations")
async def list_conversations():
    """List all conversations."""
    return {
        "conversations": [
            {
                "id": cid,
                "message_count": len(msgs),
                "last_message": msgs[-1]["content"][:100] if msgs else "",
            }
            for cid, msgs in conversations.items()
        ]
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get messages for a conversation."""
    if conversation_id not in conversations:
        return {"messages": []}
    return {"messages": conversations[conversation_id]}


def _chunk_text(text: str, chunk_size: int = 4) -> list[str]:
    """Split text into small chunks for simulated streaming."""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks
