---
description: Backend architecture — FastAPI with SSE streaming, agent routing, Ollama LLM integration, and quantum execution API
---

# Backend Skill

## Tech Stack
- **Framework**: Python 3.10+ with FastAPI
- **Server**: Uvicorn with auto-reload
- **LLM**: Ollama (local, async httpx client)
- **Quantum**: Qiskit v1.4 + Qiskit Aer
- **Streaming**: SSE via `StreamingResponse` (NOT sse-starlette)
- **Validation**: Pydantic v2 schemas

## Project Structure

```
backend/
├── app/
│   ├── main.py           — FastAPI app, CORS, lifespan, route registration
│   ├── config.py          — Settings (env vars, platform detection)
│   ├── models/
│   │   └── schemas.py     — Pydantic models (ChatRequest, Artifact, etc.)
│   ├── routes/
│   │   ├── chat.py        — POST /api/chat/send (SSE streaming)
│   │   ├── quantum.py     — GET/POST /api/quantum/* (execution)
│   │   └── projects.py    — GET /api/projects (placeholder)
│   ├── agents/
│   │   ├── orchestrator.py — Intent classification + routing
│   │   ├── code_agent.py   — Circuit generation + Qiskit execution
│   │   └── research_agent.py — Quick topics + knowledge base
│   ├── quantum/
│   │   ├── hal.py          — Hardware Abstraction Layer
│   │   └── executor.py     — Qiskit Aer execution engine
│   └── llm/
│       └── ollama_client.py — Async Ollama client (stream + generate)
├── milimoenv/             — Dedicated virtual environment
├── requirements.txt
└── run.py                 — Uvicorn runner
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/chat/send` | Chat with SSE streaming |
| GET | `/api/chat/conversations` | List conversations |
| GET | `/api/chat/conversations/{id}` | Get conversation messages |
| GET | `/api/quantum/status` | Platform + Qiskit status |
| GET | `/api/quantum/circuits` | List built-in circuits |
| POST | `/api/quantum/execute` | Execute QASM circuit |
| GET | `/api/quantum/execute/{name}` | Execute named circuit |
| GET | `/api/projects/` | List projects |
| GET | `/api/health` | Health check (Ollama + Qiskit) |

## SSE Streaming Implementation

```python
async def event_stream():
    # 1. Check quick handlers (code agent, research agent)
    # 2. Fall through to Ollama LLM
    async for token in ollama_client.stream_chat(messages, system_prompt):
        yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"
    yield f"event: done\ndata: {json.dumps({'conversation_id': cid})}\n\n"

return StreamingResponse(event_stream(), media_type="text/event-stream")
```

## Running the Backend

```bash
cd backend
source milimoenv/bin/activate  # dedicated venv
python run.py                   # → http://localhost:8000
```

## IMPORTANT Conventions
- **CORS**: Allow `localhost:5173` (Vite dev) and `localhost:3000`
- **Venv**: Always use `milimoenv`, never generic `venv`
- **Imports**: Use `from app.module.submodule import X` pattern
- **Logging**: Use Python `logging` module, not print statements
- **Async**: All route handlers are async, use `httpx.AsyncClient` for HTTP
