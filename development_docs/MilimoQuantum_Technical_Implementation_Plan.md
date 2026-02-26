# Milimo Quantum: Phase 3 Exhaustive Technical Implementation Plan

This document outlines the exact technical steps required to transition Milimo Quantum from a localized file-based prototype into a true enterprise-grade multi-tenant platform.

## User Review Required
> [!WARNING]
> This plan advocates for a **complete tear-down of the current local JSON persistence strategy** (`~/.milimoquantum/`) in favor of genuine PostgreSQL database transactions. This is a massive architectural shift but absolutely necessary before building the "12 Missing Dimensions".

---

## Proposed Changes: Core Architecture Overhaul

### 1. Database Adoption (Sunsetting JSON files)

#### [MODIFY] `backend/app/routes/chat.py`
- Strip all `app.storage` and `.json` file reads/writes.
- Implement SQLAlchemy `session.add(Message)` and `session.add(Conversation)`. 
- Ensure SSE endpoints yield DB IDs rather than generated UUIDs saved to a file.

#### [MODIFY] `backend/app/routes/projects.py`
- Create a new DB table `Project` in `app/db/models.py` (which currently doesn't exist).
- Add a relationship linking `Project` to `Conversation`.
- Rewrite the entire router to query the PostgreSQL database rather than listing directory contents in `~/.milimoquantum/projects/`.

#### [MODIFY] `backend/app/routes/analytics.py`
- Remove all fallback logic that attempts to parse local JSON files.
- Restructure the endpoints (e.g., `/api/analytics/summary`) to rely entirely on efficient SQL aggregation queries (`COUNT()`, `GROUP BY`) over the `messages` and `conversations` tables.

#### [MODIFY] `backend/app/routes/settings.py`
- Build a new DB model `UserSettings` linked to the `User` table to persist:
  - Default LLM models per agent
  - Selected theme / explanation level
- Build a generic `ProviderCredential` table to store D-Wave, AWS, IBM, and LLM API keys securely (encrypted at rest), allowing multi-user isolation instead of global `.env` configuration.

---

## Proposed Changes: 12 Missing Dimensions

### 2. Upgrading the "Mocked" Dimensions

#### [MODIFY] `backend/app/routes/academy.py`
- Create SQLAlchemy tables: `AcademyLesson` and `UserProgress`.
- Move the hardcoded Python list (`ACADEMY_LESSONS`) into a database seed script.
- Update endpoints to query PostgreSQL.

#### [MODIFY] `backend/app/routes/marketplace.py`
- Create SQLAlchemy tables: `Plugin` and `UserPluginInstall`.
- Move `COMMUNITY_PLUGINS` to a db seed script.
- Store installation state per-user rather than relying on an ephemeral global Python `set()`.

### 3. Orchestration & Visual Workflows

#### [NEW] `backend/app/routes/workflows.py`
- Create REST endpoints for DAG Pipeline execution.
- Create DB schema for `WorkflowTemplate` (JSON structure representing the DAG).

#### [MODIFY] `frontend/package.json` & `frontend/src/components/quantum/WorkflowBuilder.tsx`
- Add `reactflow` dependency.
- Build a visual drag-and-drop workspace linking agents (e.g. Finance Agent results pipelined directly into Qiskit Sandbox execution).

### 4. True Dynamic Agents (Replacing Templates)

#### [MODIFY] `backend/app/agents/*`
- Currently, agents like `finance_agent.py` and `code_agent.py` intercept user queries via regex and return hardcoded Markdown/Qiskit strings.
- **Action:** Transition these static templates into robust *System Prompts* with distinct tool-use boundaries. The agents must dynamically generate QAOA implementations based on user context rather than relying on `_bell_code()`.

---

## Verification Plan

### Automated Tests
1. **Migrations:** Trigger `alembic upgrade head` and verify the new tables (`Project`, `Plugin`, `AcademyLesson`, `ProviderCredential`) are created successfully.
2. **Integration Tests:** `pytest` the chat routes ensuring they save accurately to the Test DB container. Verify no local `.json` files are created under `~/.milimoquantum/`.

### Manual End-to-End Verification
1. Boot the environment using `docker compose --profile dev up -d`.
2. Send a chat message. Exec into the Postgres container and `SELECT * FROM messages;` to verify actual database insertion.
3. Open two browser windows (simulating two tenants). Update the LLM Key in Settings window A. Verify it does *not* override window B's execution capabilities. 
4. Drag-and-drop a pipeline in the new Workflow Builder UI and verify Celery background task ingestion.
