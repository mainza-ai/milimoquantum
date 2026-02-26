# Milimo Quantum: Exhaustive Phase 3 Technical Implementation Plan

This document outlines the mandatory technical steps required to transition Milimo Quantum from a localized file-based prototype into a true enterprise-grade multi-tenant platform, fixing the exhaustive architectural gaps discovered during the file-by-file audit.

## User Review Required
> [!WARNING]
> This plan outlines a **structural teardown of the hidden JSON persistence strategy** (`~/.milimoquantum/`) globally overriding the system in favor of genuine PostgreSQL database transactions. It also addresses the required secure migration of globally shared AI API keys.

---

## Proposed Changes: Part 1 — Security & Persistence Overhaul

### 1. Migrating to Relational Persistence (Database Adoption)

#### [MODIFY] `backend/app/routes/chat.py` & `projects.py`
- Strip all `app.storage` and local `.json` file reads/writes.
- Implement `session.add(Message)` and `session.add(Conversation)` logic querying by Keycloak User IDs.
- Create a new DB table `Project` in `app/db/models.py`. Rewrite the entire `projects.py` router to use SQL JOINs for associated conversations.

#### [MODIFY] `backend/app/routes/analytics.py`
- Remove fallback parsing of massive local JSON files.
- Restructure endpoints (`/api/analytics/summary`) to rely entirely on efficient SQL aggregation queries (`COUNT()`, `GROUP BY`) over partitioned rows.

#### [MODIFY] `backend/app/routes/graph.py`
- Connect Neo4j indexing strictly to the PostgreSQL Commit Hooks (Event-Driven) rather than manually scraping the `.json` filesystem.

### 2. Multi-Tenant Secure Configurations

#### [NEW] `backend/app/db/models.py` -> `ProviderCredential` & `UserSettings`
- Currently, `backend/app/llm/cloud_provider.py` overwrites `os.environ` affecting all users globally.
- Build a generic `ProviderCredential` schema to securely store API keys (Anthropic, D-Wave, AWS Braket, IBM, Azure Quantum) *encrypted and partitioned by User ID*.
- Modify `cloud_provider.py` and `ibm_runtime.py` to extract credentials from the DB session of the requesting user per-request, rather than from global environmental variables.

---

## Proposed Changes: Part 2 — Building The 12 Missing Dimensions

### 1. Hardening "Mocked" Capabilities

#### [MODIFY] `backend/app/routes/academy.py`
- Create SQLAlchemy tables: `AcademyLesson` and `UserProgress`.
- Move the hardcoded Python list (`ACADEMY_LESSONS`) into a database seed script.
- Update endpoints to query PostgreSQL to permanently save Quiz and Lesson completion states.

#### [MODIFY] `backend/app/routes/marketplace.py`
- Create SQLAlchemy tables: `Plugin` and `UserPluginInstall`.
- Store installation state per-user securely in the database.

### 2. Orchestration & Graph Visualization

#### [NEW] `backend/app/routes/workflows.py`
- Create REST endpoints for DAG Pipeline execution.
- Create DB schema for `WorkflowTemplate` (JSON structure representing the user's DAG graph state).

#### [NEW] `frontend/src/components/quantum/WorkflowBuilder.tsx`
- Add a new dependency (e.g., `reactflow`) to `package.json`.
- Build a visual drag-and-drop workspace where users can link Agents (Finance) directly into Quantum Hardware providers (Execution) visually bridging `quantum/hpc.py` and `cloud_backends.py`.

### 3. Dynamic Agents & Live Feeds

#### [MODIFY] `backend/app/agents/*`
- Delete static markdown string templates (`QUICK_TOPICS`). 
- Re-prompt the base agents to dynamically generate targeted Qiskit/Pennylane code specifically constrained by the user's requests rather than returning `_bell_code()`.

#### [MODIFY] `backend/app/feeds/finance.py`
- Write an actual scraping integration (e.g. `yfinance` API) rather than holding empty stubs. Ensure the `finance_agent.py` pulls from this endpoint contextually before writing optimizations.

---

## Verification Plan

### Automated Tests
1. **Migrations:** Trigger `alembic upgrade head` and verify the new tables (`Project`, `Plugin`, `AcademyLesson`, `ProviderCredential`, `UserSettings`) are created successfully.
2. **Integration Tests:** Execute `pytest` emphasizing tenant isolation (User A attempting to use User B's IBM token fails).

### Manual End-to-End Verification
1. Open two separate browser profiles (simulating two tenants). Set the LLM Key in Settings window A. Verify it does *not* override window B's LLM routing, proving true isolation.
2. Navigate to **Academy**, complete a lesson quiz, refresh the browser, and verify completion persists precisely.
3. Drag-and-drop a node pipeline in the Workflow Builder UI, passing Finance JSON Data to a Quantum Backend node, and verify Celery background task ingestion.
