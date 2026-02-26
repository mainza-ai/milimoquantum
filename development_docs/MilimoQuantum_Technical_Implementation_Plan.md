# Milimo Quantum: Phase 3 True Implementation Plan

Based on the Exhaustive Documentation Traceability Audit, the following plan bridges the massive gap between the 5 foundational Architecture Documents and the current codebase.

## Part 1: Eliminating File-Based System Vulnerabilities

### 1. `projects.py` and `analytics.py` Database Overhaul
The codebase suffers from split-brain persistence. Experiments and Conversations use SQLAlchemy, but Projects use JSON via `~/.milimoquantum/projects`.
- **Action:** Delete `PROJECTS_DIR = Path.home() / ".milimoquantum" / "projects"`.
- **Action:** Rewrite the `list_projects`, `create_project`, and `get_project` routes in `projects.py` to invoke `get_session()` and query `app.db.models.Project`.
- **Action:** Rewrite `analytics.py` endpoints like `circuit_stats()` to execute SQL queries rather than traversing `.json` directory globs.

### 2. Activating Keycloak SSO
- **Action:** Enforce `AUTH_ENABLED=true` in `.env`.
- **Action:** Bind `get_current_user` directly into the UI state (`App.tsx` / `Sidebar.tsx`) so that the application is locked behind Keycloak authentication.

---

## Part 2: Addressing Specific Document Obligations

### 1. Resolving `MilimoQuantum_GraphDB_Addendum.md`
- **Action:** Install and integrate `graphrag` and `graphiti` Python libraries in `backend/requirements.txt`.
- **Action:** Rewrite `app/graph/agent_memory.py` to deploy GraphRAG for contextualizing past quantum experiments during agent chat, rather than just basic Neo4j string queries.
- **Action:** Implement FalkorDB adapters specifically for fast semantic retrieval of short-term chat context.

### 2. Resolving `MilimoQuantum_CrossPlatform_Guide.md`
- **Action:** The Guide promises Apple MLX integration for Mac LLM acceleration. Currently, Mac users just proxy to Ollama.
- **Action:** Build `app/llm/mlx_client.py` using `mlx-lm` to natively process local LLMs within the Python process on Apple Silicon.
- **Action:** Build `app/quantum/cudaq.py` to hook NVIDIA `cudaq` natively on Windows as promised.

### 3. Resolving `MilimoQuantum_Architecture_Diagrams.md`
- **Action:** The remaining 6 Hardware Providers (IonQ, QuEra, Quantinuum, Rigetti, OQC, IQM) must be stubbed and added into `app/quantum/cloud_backends.py`.
- **Action:** Drag-and-drop DAG Workflow interface (`WorkflowBuilder.tsx`) must be built in the UI and connected to Celery queues to link multi-agent output chaining.

### 4. Resolving Domain Missing Dimensions
- **Action:** Complete the `app/feeds/finance.py` module by integrating `yahooquery` or `alpaca-py` for live data fetching rather than mocked arrays.
- **Action:** Develop the **Device Syncing Engine**, utilizing WebSocket (`fastapi.WebSocket`) to push real-time DB state updates to active clients.

## Execution Priority
1. **DB Convergence:** Force `projects.py` to use SQLAlchemy. (Stop the JSON sprawl).
2. **Mac MLX & Windows CUDA-Q:** Build the native hardware accelerators promised.
3. **GraphRAG:** Bring actual semantic subgraph retrieval to the Agents.
