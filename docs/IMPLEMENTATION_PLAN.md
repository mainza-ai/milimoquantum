# Milimo Quantum — Comprehensive Implementation Plan

## Audit Summary

A full-system audit was conducted across 8 dimensions covering 348 files. The system is **functionally operational** with 192 passing tests, but the audit revealed **31 distinct issues** across critical, high, medium, and low severity levels. The issues span broken endpoints, event-loop blocking, dead code, disconnected integrations, frontend-backend mismatches, and operational gaps.

---

## Phase 1: Critical Bugs (Fix Immediately)

### 1.1 Fix `dispatch_quantum_job` — Missing Function
**Severity:** CRITICAL — 500 on every `/api/quantum/cloud-backends/dispatch` call
**Files:** `backend/app/quantum/cloud_backends.py`, `backend/app/routes/quantum.py:471`
**Problem:** `routes/quantum.py:471` imports `dispatch_quantum_job` from `cloud_backends` but it doesn't exist.
**Fix:**
- Implement `dispatch_quantum_job(provider, circuit, params)` in `cloud_backends.py` that routes to `run_on_braket()` or `run_on_azure()` based on provider name
- Or remove the endpoint if cloud dispatch is not intended for production

### 1.2 Fix Gemini Async Streaming — Event Loop Blocking
**Severity:** CRITICAL — Blocks entire async event loop when Gemini is active
**Files:** `backend/app/llm/cloud_provider.py:263-285`
**Problem:** `_stream_gemini()` uses sync `client.models.generate_content_stream()` inside an async function
**Fix:**
- Replace with `client.aio.models.generate_content_stream()` and `async for` iteration
- Add explicit API key: `genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))`

### 1.3 Fix Hard Imports — App Crash Without Qiskit
**Severity:** CRITICAL — Crashes app startup if Qiskit is missing
**Files:** 
- `backend/app/quantum/fault_tolerant.py:11` — `from qiskit import ...`
- `backend/app/quantum/hpc.py:10` — `from qiskit import transpile`
- `backend/app/quantum/benchmarking.py:11-17` — 6 unprotected imports
**Fix:**
- Wrap all top-level Qiskit/DB imports in `try/except ImportError` guards
- Set module-level availability flags (e.g., `FAULT_TOLERANT_AVAILABLE = True/False`)
- Follow the pattern already used by `vqe_executor.py`, `qaoa_executor.py`, `sandbox.py`

### 1.4 Fix Migration Chain — Duplicate Column Additions
**Severity:** CRITICAL — `alembic upgrade head` will fail
**Files:** `backend/alembic/versions/bc4da2a3b28a_*.py`, `add_projects_related_tables.py`
**Problem:** `bc4da2a3b28a` adds `project_id` columns that `add_projects_related_tables` already added
**Fix:**
- Remove duplicate `add_column` operations from `bc4da2a3b28a`
- Keep only the FK constraint additions (`create_foreign_key`)
- Move `add_vqe_entity_schema.py` Neo4j operations out of Alembic into a startup script

---

## Phase 2: High Priority (Fix This Sprint)

### 2.1 Add VQE/QAOA Direct REST Endpoints
**Severity:** HIGH — Real engines exist but no direct API access
**Files:** `backend/app/routes/quantum.py`
**Problem:** `vqe_executor.py` and `qaoa_executor.py` are fully implemented but only accessible through Celery tasks or the autoresearch extension
**Fix:**
- Add `POST /api/quantum/vqe/run` endpoint accepting hamiltonian, ansatz_type, optimizer params
- Add `POST /api/quantum/qaoa/run` endpoint accepting cost_hamiltonian, edges, reps
- Both should return JSON with energy, convergence, circuit_stats

### 2.2 Fix Celery Task Bugs
**Severity:** HIGH — Broken imports, orphaned tasks, stub implementations
**Files:** `backend/app/worker/tasks.py`
**Fixes:**
- **`run_vqe_optimization` (line 74):** Change import from `pennylane_bridge.run_vqe` → `pennylane_bridge.run_vqe_pennylane` and fix parameter mismatch, OR delete if the workflow.py generator is the intended implementation
- **`run_vqe_qiskit` (line 167):** Connect to an API route or remove as dead code
- **`execute_dag_node` (line 102):** Either implement real node execution logic or mark as scaffolding with a clear TODO
- **Queue routing:** Add `-Q celery,quantum` to worker startup commands, or remove the `task_routes` config

### 2.3 Clean Up Dead Code
**Severity:** HIGH — Confusing codebase, maintenance burden
**Files:** Multiple
**Fixes:**
- Remove `backend/app/agents/sensing.py` and `networking.py` (thin duplicates of `sensing_agent.py` and `networking_agent.py`)
- Remove `backend/app/quantum/advanced_sims` imports from `sensing_agent.py:236` and `networking_agent.py:320` (module doesn't exist)
- Remove `backend/app/quantum/vector_store.py` (simpler duplicate of `backend/app/vector_store.py`) — consolidate to one
- Consolidate `cloud_backends.py` with `braket_provider.py` and `azure_provider.py` — keep the structured provider modules, remove `cloud_backends.py`

### 2.4 Fix Agent Dispatch Gaps
**Severity:** HIGH — 4 agent types have no dispatch handlers
**Files:** `backend/app/agents/orchestrator.py:148-162`
**Fixes:**
- Add `PLANNING`, `BENCHMARKING`, `FAULT_TOLERANCE` to `agent_map` in `dispatch_to_agent()`
- Add `AUTORESEARCH_ANALYZER` system prompt to `SYSTEM_PROMPTS` dict
- Fix `/research` slash command collision — rename autoresearch extension's `/research` to `/loop` or `/pretrain` to avoid overriding core Research agent

### 2.5 Fix Frontend API Response Validation
**Severity:** HIGH — Silent failures on 401/404/500
**Files:** `frontend/src/services/api.ts:5-20`
**Fix:**
- Add `if (!response.ok) throw new Error(...)` check in `fetchWithAuth` or create a `fetchJsonWithAuth` wrapper
- Update all callers to handle thrown errors properly

### 2.6 Fix CloudProviderPanel Settings Shape Mismatch
**Severity:** HIGH — Active provider badge never displays
**Files:** `frontend/src/components/quantum/panels/CloudProviderPanel.tsx:21-28`
**Fix:**
- Change `Settings` interface to match backend response: `cloud_provider: { provider: string, model: string }` instead of flat `active_cloud_provider`
- Update `settings?.active_cloud_provider` → `settings?.cloud_provider?.provider`

---

## Phase 3: Medium Priority (Next Sprint)

### 3.1 Implement Cloud Provider Fallback Chain
**Severity:** MEDIUM — Single provider, no failover
**Files:** `backend/app/llm/cloud_provider.py:186-224`
**Fix:**
- Add fallback logic in `stream_chat_cloud()` that tries the next configured provider if the active one fails
- Implement `is_available()` health check for each provider
- Add exponential backoff retry (max 2 retries per provider)

### 3.2 Activate NemoClaw Integration
**Severity:** MEDIUM — BlueprintRunner imported but never called
**Files:** `backend/app/extensions/autoresearch/workflow.py`
**Fix:**
- Wire `BlueprintRunner` into `run_research_loop()` and `run_autonomous_loop()` as the execution path
- Add a `use_sandbox` flag in the run request to toggle between sandbox and direct subprocess
- Document the NemoClaw CLI dependency in setup instructions

### 3.3 Fix Extension System Integration
**Severity:** MEDIUM — Extensions disconnected from main pipeline
**Files:** Multiple
**Fixes:**
- Add `AgentType.AUTORESEARCH` and `AgentType.MQDD` to the enum
- Add labels for both in `AGENT_LABELS` dict (`chat.py:41-59`)
- Implement auto-router-registration in `main.py` by iterating `registry.extensions`
- Fix intent pattern priority — check extension patterns before hardcoded ones, or use weighted scoring
- Create unified `/api/extensions` discovery endpoint
- Implement `export_mqdd_to_parquet()` to query `Artifact` records instead of `Experiment` table

### 3.4 Add Redis Health Check & App-Level Caching
**Severity:** MEDIUM — No visibility into Redis state, no caching
**Files:** `backend/app/worker/__init__.py`, `backend/app/main.py`
**Fixes:**
- Add Redis connectivity check to `/api/health` endpoint
- Fix `CELERY_AVAILABLE` detection — add logging when Redis ping fails, consider lazy initialization
- Add application-level caching for expensive operations (analytics, agent usage, circuit stats)

### 3.5 Fix Frontend SSE Reliability
**Severity:** MEDIUM — No abort, no reconnection, no timeout
**Files:** `frontend/src/services/api.ts:264-340`, `frontend/src/hooks/useChat.ts`
**Fixes:**
- Add `AbortController` to `streamChat()` with configurable timeout
- Expose abort function from `useChat` hook for cleanup on unmount
- Add reconnection logic with exponential backoff (max 3 retries)
- Add `useEffect` cleanup in `useChat` to abort in-flight streams on unmount

### 3.6 Fix SettingsPanel DOM Query Anti-Pattern
**Severity:** MEDIUM — Fragile API key input handling
**Files:** `frontend/src/components/layout/SettingsPanel.tsx:202-220`
**Fix:**
- Replace `document.getElementById('cloud-api-key-input')` with React state
- Manage `cloudModel` selection as proper state, not implicit from click handlers

### 3.7 Fix MQDD Persistence Gaps
**Severity:** MEDIUM — Knowledge graph updates not pushed to Neo4j
**Files:** `backend/app/extensions/mqdd/workflow.py:143-187`
**Fix:**
- After saving MQDD artifact to SQL, push `knowledgeGraphUpdate` to Neo4j using `neo4j_client.index_artifact()` or similar
- Ensure MQDD results are queryable through the graph API

### 3.8 Fix Data Layer Inconsistencies
**Severity:** MEDIUM — FK mismatches, dual storage, migration issues
**Files:** Multiple
**Fixes:**
- Set `project_id` on `BenchmarkResult` creation in `benchmarking.py`
- Set `Conversation.project_id` on Neo4j Conversation nodes in `index_conversation()`
- Fix Experiment sync — ensure `log_run()` and `get_run()` use the same data source
- Unify session management — adopt `with get_session()` context manager everywhere
- Remove or wire `User` model into auth flow

---

## Phase 4: Low Priority (Polish)

### 4.1 Fix Ollama Blocking Sync Call
**Severity:** LOW — Blocks event loop on model auto-detect
**Files:** `backend/app/llm/ollama_client.py:33-35`
**Fix:** Make model auto-detection async or cache at startup

### 4.2 Fix MLX `enable_thinking` Parameter
**Severity:** LOW — May cause TypeError on unsupported models
**Files:** `backend/app/llm/mlx_client.py:245-246, 351-352`
**Fix:** Conditionally pass `enable_thinking` only for models that support it

### 4.3 Fix D-Wave Availability Check
**Severity:** LOW — Too strict, blocks local simulated annealing
**Files:** `backend/app/quantum/dwave_provider.py:12-15`
**Fix:** Separate `dimod` import from `dwave.system` — allow local fallback when only `dimod` is installed

### 4.4 Fix CUDA-Q Provider Inconsistency
**Severity:** LOW — Dual inconsistent implementations
**Files:** `backend/app/quantum/cudaq_executor.py`, `cudaq_provider.py`
**Fix:** Consolidate into single module with clear interface

### 4.5 Add QRNG Statistical Validation
**Severity:** LOW — Docstring claims validation that doesn't exist
**Files:** `backend/app/quantum/qrng.py`
**Fix:** Add basic chi-squared test or entropy estimation, or update docstring

### 4.6 Fix Noise Profile Device Coverage
**Severity:** LOW — Only 3 IBM devices
**Files:** `backend/app/quantum/noise_profiles.py`
**Fix:** Add profiles for IonQ, Quantinuum, Rigetti devices

### 4.7 Fix Cloud Settings Race Condition
**Severity:** LOW — Non-atomic file writes
**Files:** `backend/app/llm/cloud_provider.py:100-125`
**Fix:** Use file locking (fcntl) or atomic write (write to temp, rename)

### 4.8 Frontend UI Polish
**Severity:** LOW — Missing loading/error states
**Files:** Multiple frontend components
**Fixes:**
- Add loading/error states to QRNGPanel
- Fix ErrorMitigation to display actual results instead of hardcoded values
- Fix HardwareSettings to persist selection to backend
- Add server-side theme persistence
- Add `fetchProject(id)` to API service layer

### 4.9 Agent `__init__.py` Exports
**Severity:** LOW — Empty init file
**Files:** `backend/app/agents/__init__.py`
**Fix:** Add centralized exports for all agent modules

---

## Issue Count Summary

| Phase | Critical | High | Medium | Low | Total |
|-------|----------|------|--------|-----|-------|
| Phase 1 | 4 | — | — | — | 4 |
| Phase 2 | — | 6 | — | — | 6 |
| Phase 3 | — | — | 8 | — | 8 |
| Phase 4 | — | — | — | 9 | 9 |
| **Total** | **4** | **6** | **8** | **9** | **27** |

## Effort Estimate

| Phase | Estimated Effort | Risk |
|-------|-----------------|------|
| Phase 1 | 2-3 hours | Low — targeted fixes, well-understood issues |
| Phase 2 | 4-6 hours | Medium — some refactoring, test updates needed |
| Phase 3 | 6-8 hours | Medium-High — architectural changes, cross-component coordination |
| Phase 4 | 3-4 hours | Low — incremental improvements |
| **Total** | **15-21 hours** | |

## Testing Strategy

After each phase:
1. Run `test_comprehensive.py` — unit + integration tests
2. Run `test_e2e_workflows.py` — real workflow HTTP tests
3. Run `test_nemoclaw_e2e.py` — NemoClaw + Docker + Autoresearch tests
4. Manual verification of affected UI flows
5. Backend restart and health check
