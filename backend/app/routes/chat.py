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
from app.quantum.sandbox import (
    execute_and_build_artifacts,
    extract_code_blocks,
    execute_code,
    build_artifacts_from_result,
)
from app.llm.ollama_client import ollama_client
from app.llm.cloud_provider import get_current_provider, stream_chat_cloud
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

        # ── Step 1: LLM with enriched system prompt ───────────
        # Every agent has a detailed system prompt. The context
        # enricher dynamically injects live data (stock prices,
        # arXiv papers, molecular data, agent memory) based on
        # what the user is asking about.
        from app.agents.context_enricher import enrich_prompt, save_interaction_memory, build_data_preamble
        base_prompt = SYSTEM_PROMPTS.get(agent_type, SYSTEM_PROMPTS[AgentType.ORCHESTRATOR])
        system_prompt = await enrich_prompt(agent_type, clean_message, base_prompt)
        history = msgs[-20:]

        full_response = ""

        # ── Step 1a: Stream live data preamble DIRECTLY ────────
        # Build a formatted data section (price tables, papers,
        # molecule data) and stream it as tokens to the user first.
        # This GUARANTEES the user sees real data regardless of
        # how well the LLM incorporates it.
        preamble = build_data_preamble(agent_type, clean_message)
        if preamble:
            # Stream preamble in word-sized chunks for natural feel
            for chunk in _chunk_text(preamble, 12):
                full_response += chunk
                yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"

        cloud = get_current_provider()
        if cloud.get("provider") != "ollama" and cloud.get("provider"):
            # ── Cloud AI provider active (Anthropic / OpenAI / Gemini)
            async for token in stream_chat_cloud(messages=history, system_prompt=system_prompt):
                full_response += token
                yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"
        else:
            # ── Default: local Ollama
            async for token in ollama_client.stream_chat(messages=history, system_prompt=system_prompt):
                full_response += token
                yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"

        msgs.append({"role": "assistant", "content": full_response})

        # ── Step 2: Sandbox — Execute with auto-retry ──────────
        # Extract code from the LLM response, execute it safely,
        # and if it fails, ask the LLM to fix the code (up to 2 retries).
        agent_label = AGENT_LABELS.get(agent_type, "Milimo Quantum")
        MAX_RETRIES = 2

        async def _llm_generate(prompt: str, sys_prompt: str) -> str:
            """Non-streaming LLM generation for retry loop."""
            cloud = get_current_provider()
            if cloud.get("provider") != "ollama" and cloud.get("provider"):
                result_text = ""
                async for t in stream_chat_cloud(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt=sys_prompt,
                ):
                    result_text += t
                return result_text
            else:
                return await ollama_client.generate(prompt=prompt, system_prompt=sys_prompt)

        try:
            sandbox_artifacts, sandbox_error = execute_and_build_artifacts(
                full_response, agent_label=agent_label
            )

            # ── Auto-retry: if code failed, ask the LLM to fix it
            if sandbox_error and not sandbox_artifacts:
                code_blocks = extract_code_blocks(full_response)
                failed_code = code_blocks[0] if code_blocks else ""

                for attempt in range(1, MAX_RETRIES + 1):
                    yield f"event: retry\ndata: {json.dumps({'attempt': attempt, 'max': MAX_RETRIES, 'error': sandbox_error[:300]})}\n\n"
                    logger.info(f"Auto-retry attempt {attempt}/{MAX_RETRIES}")

                    fix_prompt = (
                        f"The following Qiskit code failed with an error. "
                        f"Fix the code and return ONLY the corrected Python code in a ```python block.\n\n"
                        f"**Failed Code:**\n```python\n{failed_code}\n```\n\n"
                        f"**Error:**\n{sandbox_error[:500]}\n\n"
                        f"Return ONLY the fixed ```python code block, no explanation."
                    )
                    fix_sys = "You are a Qiskit code debugger. Fix the code. Use Qiskit v1.4 API with qiskit_aer.AerSimulator. Return only the corrected code."

                    fixed_response = await _llm_generate(fix_prompt, fix_sys)
                    fixed_blocks = extract_code_blocks(fixed_response)

                    if fixed_blocks:
                        fixed_code = fixed_blocks[0]
                        result = execute_code(fixed_code)
                        if not result.error:
                            # Success! Build artifacts from the fixed code
                            sandbox_artifacts = build_artifacts_from_result(result, fixed_code, agent_label)
                            sandbox_error = None
                            # Stream a notice about the fix
                            fix_notice = f"\n\n✅ *Code auto-corrected on attempt {attempt}.*\n"
                            yield f"event: token\ndata: {json.dumps({'content': fix_notice})}\n\n"
                            full_response += fix_notice
                            msgs[-1]["content"] = full_response
                            break
                        else:
                            failed_code = fixed_code
                            sandbox_error = result.error
                    else:
                        break  # LLM didn't return code, stop retrying

                if sandbox_error:
                    logger.warning(f"Auto-retry exhausted. Final error: {sandbox_error[:200]}")

            for artifact in sandbox_artifacts:
                yield f"event: artifact\ndata: {json.dumps(artifact.model_dump(), default=str)}\n\n"

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")

        storage.save_conversation(conversation_id, msgs)

        # ── Step 3: Auto-index for search ──
        try:
            from app.vector_store import index_conversation
            await index_conversation(conversation_id, msgs)
        except Exception:
            pass  # Search indexing is best-effort

        # ── Step 4: Save to agent memory ──
        try:
            summary_text = full_response[:300] if full_response else ""
            await save_interaction_memory(
                agent_type, conversation_id, clean_message, summary_text
            )
        except Exception:
            pass  # Memory saving is best-effort

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
