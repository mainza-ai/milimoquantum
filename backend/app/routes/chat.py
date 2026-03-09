"""Milimo Quantum — Chat Routes with SSE streaming.

Architecture:
  1. LLM with domain-specific system prompts generates dynamic responses
     with runnable Qiskit code blocks.
  2. Sandbox extracts and executes any code blocks from the LLM response,
     capturing circuits and measurements as artifacts.
  3. Artifacts stream to the frontend alongside the explanation text.

Every response is unique, dynamic, and contextual — no static shortcuts.
"""
import json
import logging
import uuid
import shutil
from typing import Any
from pathlib import Path

from fastapi import APIRouter, Request, Depends, UploadFile, File
from fastapi.responses import StreamingResponse

from app.limiter import limiter

from app.audit import log_action

from app.agents.orchestrator import (
    classify_intent,
    detect_slash_command,
    get_system_prompt,
    dispatch_multi_agent,
)
from app.agents.planning_agent import needs_planning, decompose_task, format_plan
from app.llm.ollama_client import ollama_client
from app.llm.mlx_client import mlx_client
from app.llm.cloud_provider import get_current_provider, stream_chat_cloud
from app.models.schemas import AgentType, ChatRequest
from app import storage
from app.auth import get_current_user

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
    AgentType.BENCHMARKING: "Benchmarking & Advantage",
    AgentType.FAULT_TOLERANCE: "Fault Tolerance Lab",
    AgentType.PLANNING: "Planning",
    AgentType.ORCHESTRATOR: "Milimo Quantum",
}

UPLOAD_DIR = Path.home() / ".milimoquantum" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/chat", 
    tags=["chat"],
    dependencies=[Depends(get_current_user)]
)

# In-memory store (backed by file persistence)
conversations: dict[str, list[dict[str, Any]]] = {}


def _load_or_init(conversation_id: str) -> list[dict[str, Any]]:
    """Load conversation from memory or disk."""
    if conversation_id in conversations:
        return conversations[conversation_id]
    saved = storage.load_conversation(conversation_id)
    if saved and "messages" in saved:
        conversations[conversation_id] = saved["messages"]
        return conversations[conversation_id]
    conversations[conversation_id] = []
    return conversations[conversation_id]


@router.post("/upload")
@limiter.limit("5/minute")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Upload a file to attach to a chat message."""
    # Restrict MIME types
    ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "application/pdf", "text/plain", "text/csv", "application/json"]
    if file.content_type not in ALLOWED_MIME_TYPES:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {file.content_type}")

    file_id = str(uuid.uuid4())
    # Sanitize filename strictly to alphanumeric and common safe characters
    safe_filename = "".join(c for c in (file.filename or "") if c.isalnum() or c in "._-")
    
    # Restrict extensions
    ext = safe_filename.split('.')[-1].lower() if '.' in safe_filename else ''
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "pdf", "txt", "csv", "json"}
    if ext and ext not in ALLOWED_EXTENSIONS:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")

    safe_name = f"{file_id}.{ext}" if ext else file_id
    file_path = UPLOAD_DIR / safe_name
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    import os
    return {
        "id": file_id,
        "filename": safe_filename or file_id,
        "path": str(file_path),
        "content_type": file.content_type,
        "size": os.path.getsize(file_path)
    }

@router.post("/send")
@limiter.limit("10/minute")
async def send_message(request: Request, payload: ChatRequest):
    """Send a message and get a streaming SSE response."""
    conversation_id = payload.conversation_id or str(uuid.uuid4())
    msgs = _load_or_init(conversation_id)

    # Detect agent
    agent_type = payload.agent or classify_intent(payload.message)
    _, clean_message = detect_slash_command(payload.message)

    # Auto-detect QASM file content → route to Code Agent
    if 'OPENQASM' in payload.message or 'qreg' in payload.message:
        agent_type = AgentType.CODE

    image_path = None
    if getattr(payload, "attached_file_id", None):
        found = list(UPLOAD_DIR.glob(f"{payload.attached_file_id}.*"))
        if found:
            file_path = found[0]
            ext = file_path.suffix.lower()
            if ext in ['.png', '.jpg', '.jpeg', '.webp']:
                image_path = str(file_path)
                payload.message = f"[Attached Image: {file_path.name}]\n\n{payload.message}"
                clean_message = f"[Attached Image: {file_path.name}]\n\n{clean_message}"
                logger.info(f"Image attachment detected: {image_path}")
            else:
                try:
                    content = file_path.read_text(errors='replace')
                    payload.message = f"[Attached File: {file_path.name}]\n\n{content}\n\n---\n\n{payload.message}"
                    clean_message = f"[Attached File: {file_path.name}]\n\n{content}\n\n---\n\n{clean_message}"
                except Exception as e:
                    logger.error(f"Failed to read attached file: {e}")

    # Store user message
    msgs.append({"role": "user", "content": payload.message})

    # Audit log
    await log_action("user", "chat_message", f"conversation/{conversation_id}",
                     {"agent": agent_type, "length": len(payload.message)})

    async def event_stream():
        """Generate SSE events."""
        all_message_artifacts = []

        # ── Step 0: Multi-agent planning (if needed) ──────────
        multi_agent_context = ""
        if agent_type == AgentType.PLANNING or needs_planning(clean_message):
            steps = decompose_task(clean_message)
            plan_text = format_plan(steps)
            
            from app.agents.planning_agent import get_workflow_artifact
            wf_art = get_workflow_artifact(steps)
            all_message_artifacts.append(wf_art)
            yield f"event: artifact\ndata: {json.dumps(wf_art, default=str)}\n\n"

            # Stream the plan to the user
            for chunk in _chunk_text(plan_text, 12):
                yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"

            # Execute each step
            results = dispatch_multi_agent(steps)
            for r in results:
                step_header = f"\n### Step {r['step']} — {r['agent']}\n"
                yield f"event: token\ndata: {json.dumps({'content': step_header})}\n\n"

                step_body = str(r.get('response', ''))
                for chunk in _chunk_text(step_body, 12):
                    yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"

                # Send any artifacts from the step
                for art in r.get('artifacts', []):
                    art_dict = art.model_dump() if hasattr(art, 'model_dump') else art
                    all_message_artifacts.append(art_dict)
                    yield f"event: artifact\ndata: {json.dumps(art_dict, default=str)}\n\n"

                multi_agent_context += f"\n[Step {r['step']} - {r['agent']}]: {step_body[:400]}"

            yield f"event: token\ndata: {json.dumps({'content': '\n---\n\n'})}\n\n"

        # ── Step 1: LLM with enriched system prompt ───────────
        # Every agent has a detailed system prompt. The context
        # enricher dynamically injects live data (stock prices,
        # arXiv papers, molecular data, agent memory) based on
        # what the user is asking about.
        from app.agents.context_enricher import enrich_prompt, save_interaction_memory, build_data_preamble
        base_prompt = get_system_prompt(agent_type)  # explain-level aware
        system_prompt = await enrich_prompt(agent_type, clean_message, base_prompt)
        history = msgs[-20:]

        # Per-agent model override
        from app.config import settings as app_settings
        agent_model = app_settings.agent_models.get(agent_type, None)

        full_response = ""

        # ── Step 1a: Stream live data preamble DIRECTLY ────────
        # Build a formatted data section (price tables, papers,
        # molecule data) and stream it as tokens to the user first.
        # This GUARANTEES the user sees real data regardless of
        # how well the LLM incorporates it.
        preamble = await build_data_preamble(agent_type, clean_message)
        if preamble:
            # Stream preamble in word-sized chunks for natural feel
            for chunk in _chunk_text(preamble, 12):
                full_response += chunk
                yield f"event: token\ndata: {json.dumps({'content': chunk})}\n\n"

        cloud = get_current_provider()
        if mlx_client.is_loaded:
            # ── Apple Silicon Native MLX loaded
            model_override = agent_model if agent_model else None
            async for token_str in mlx_client.stream_chat(
                messages=history, system_prompt=system_prompt, model=model_override, image_path=image_path
            ):
                # parse the json to extract content for the full response accumulation
                try:
                    payload = json.loads(token_str)
                    if "message" in payload and "content" in payload["message"]:
                        token_content = payload["message"]["content"]
                        full_response += token_content
                        # MLX client already yields formatted API JSON strings
                        yield f"event: token\ndata: {json.dumps({'content': token_content})}\n\n"
                    elif "error" in payload:
                        yield f"event: token\ndata: {json.dumps({'content': payload['error']})}\n\n"
                except Exception:
                    # just stream the raw string if not json
                    full_response += str(token_str)
                    yield f"event: token\ndata: {json.dumps({'content': str(token_str)})}\n\n"
        elif cloud.get("provider") != "ollama" and cloud.get("provider"):
            # ── Cloud AI provider active (Anthropic / OpenAI / Gemini)
            async for token in stream_chat_cloud(messages=history, system_prompt=system_prompt):
                full_response += str(token)
                yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"
        else:
            # ── Default: local Ollama
            model_override = agent_model if agent_model else None
            async for token in ollama_client.stream_chat(
                messages=history, system_prompt=system_prompt, model=model_override
            ):
                full_response += str(token)
                yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"

        msgs.append({"role": "assistant", "content": full_response})

        # ── Step 2: Sandbox — Execute via Celery Cluster ────────
        # Extract code from the LLM response, submit to Celery queue,
        # poll for completion, and stream status/artifacts back over SSE.
        MAX_RETRIES = 2

        async def _stream_llm_generate(prompt: str, sys_prompt: str):
            """Streaming LLM generation for retry loop."""
            cloud = get_current_provider()
            if mlx_client.is_loaded:
                model_override = None
                async for token_str in mlx_client.stream_chat(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt=sys_prompt,
                    model=model_override
                ):
                    # parse the json to extract content
                    try:
                        payload = json.loads(token_str)
                        if "message" in payload and "content" in payload["message"]:
                            token_content = payload["message"]["content"]
                            yield token_content
                        elif "error" in payload:
                            yield payload["error"]
                    except Exception:
                        yield str(token_str)
            elif cloud.get("provider") != "ollama" and cloud.get("provider"):
                async for t in stream_chat_cloud(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt=sys_prompt,
                ):
                    yield t
            else:
                async for t in ollama_client.stream_chat(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt=sys_prompt
                ):
                    yield t

        try:
            import asyncio
            from app.quantum.sandbox import extract_code_blocks
            from app.worker.tasks import run_code_sandbox
            
            code_blocks = extract_code_blocks(full_response)
            sandbox_error = None
            sandbox_artifacts = []
            
            if code_blocks:
                code_to_run = code_blocks[0]
                
                for attempt in range(1, MAX_RETRIES + 2):
                    if attempt > 1:
                        yield f"event: retry\ndata: {json.dumps({'attempt': attempt-1, 'max': MAX_RETRIES, 'error': str(sandbox_error)[:300]})}\n\n"
                        logger.info(f"Auto-retry attempt {attempt-1}/{MAX_RETRIES}")
                        
                        fix_prompt = (
                            f"The following code failed with an error. "
                            f"Fix the code and return ONLY the corrected Python code in a ```python block.\n\n"
                            f"**Failed Code:**\n```python\n{code_to_run}\n```\n\n"
                            f"**Error:**\n{str(sandbox_error)[:500]}\n\n"
                            f"Return ONLY the fixed ```python code block."
                        )
                        fix_sys = "You are a Qiskit code debugger. Fix the code. Use Qiskit v1.4 API with qiskit_aer.AerSimulator. Return only the corrected code."
                        
                        fixed_response = ""
                        async for token_chunk in _stream_llm_generate(fix_prompt, fix_sys):
                            fixed_response += str(token_chunk)
                            yield f"event: token\ndata: {json.dumps({'content': token_chunk})}\n\n"
                        
                        fixed_blocks = extract_code_blocks(fixed_response)
                        if fixed_blocks:
                            code_to_run = fixed_blocks[0]
                        else:
                            failure_notice = "\n\n⚠️ *Auto-correction failed to return a code block.*\n"
                            yield f"event: token\ndata: {json.dumps({'content': failure_notice})}\n\n"
                            full_response += failure_notice
                            msgs[-1]["content"] = full_response
                            break # stop retrying

                    # Dispatch to Celery
                    yield f"event: token\ndata: {json.dumps({'content': chr(10) + chr(10) + '🚀 *Dispatching job ' + ('(Retry)' if attempt > 1 else '') + ' to Celery Orchestration Cluster...*' + chr(10)})}\n\n"
                    
                    task = run_code_sandbox.delay(code=code_to_run)
                    
                    # Async Polling Loop
                    last_status = ""
                    while not task.ready():
                        await asyncio.sleep(0.5)
                        info = task.info
                        status_msg = info.get("status", "Executing Sandbox Code...") if isinstance(info, dict) else "Executing Sandbox Code..."
                        if status_msg != last_status:
                            status_stream = f"⏳ *Worker Status:* {status_msg}\n"
                            yield f"event: token\ndata: {json.dumps({'content': status_stream})}\n\n"
                            last_status = status_msg

                    # Task Finished
                    if task.successful():
                        result_data = task.get()
                        if result_data.get("success"):
                            # Map dict artifacts back to Artifact
                            from app.models.schemas import Artifact
                            sandbox_artifacts = []
                            for art_dict in result_data.get("artifacts", []):
                                sandbox_artifacts.append(Artifact(**art_dict))
                            
                            logger.info(f"CELERY RETURNED ARTIFACTS: {[a.type for a in sandbox_artifacts]}")
                            logger.info(f"CELERY SUCCESS RESULT_DATA ATTRS: {list(result_data.keys())}")
                            
                            sandbox_error = None
                            if attempt > 1:
                                fix_notice = f"\n✅ *Code auto-corrected on attempt {attempt-1}.*\n"
                                yield f"event: token\ndata: {json.dumps({'content': fix_notice})}\n\n"
                                full_response += fix_notice
                                msgs[-1]["content"] = full_response
                            break
                        else:
                            sandbox_error = result_data.get("error", "Unknown execution error")
                    else:
                        sandbox_error = str(task.info)
                        
                if sandbox_error:
                    logger.warning(f"Celery Execution failed/exhausted. Final error: {str(sandbox_error)[:200]}")

                # No trailing code here since the logic is handled in the retry block above

            for artifact in sandbox_artifacts:
                art_dict = artifact.model_dump()
                all_message_artifacts.append(art_dict)
                yield f"event: artifact\ndata: {json.dumps(art_dict, default=str)}\n\n"

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")

        # Attach all generated artifacts to the assistant's message before saving
        if all_message_artifacts:
            msgs[-1]["artifacts"] = all_message_artifacts

        storage.save_conversation(conversation_id, msgs, is_new_append=True)

        # ── Step 3: Auto-index for search ──
        try:
            from app.vector_store import index_conversation
            # Extract title for search indexing
            title = ""
            for m in msgs:
                if m.get("role") == "user":
                    val = m.get("content", "")
                    title = str(val)[:60] if val else ""
                    break
            await index_conversation(conversation_id, msgs, title=title)
        except Exception as e:
            logger.warning(f"Search indexing failed (non-critical): {e}")

        # ── Step 4: Save to agent memory ──
        try:
            summary_text = str(full_response)[:300] if full_response else ""
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
        conversations.pop(conversation_id, None)
    success = storage.delete_conversation(conversation_id)
    return {"deleted": success}


def _chunk_text(text: str, chunk_size: int = 4) -> list[str]:
    """Split text into small chunks for simulated streaming."""
    return [str(text)[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
