# Milimo Quantum: Phase 3 Technical Implementation Plan

This document outlines the exact technical steps required to bridge the gap between the current architecture (scaffolds) and the fully-functional "12 Missing Dimensions" documented in the Gap Analysis.

## User Review Required
> [!IMPORTANT]
> This plan requires structural changes to the PostgreSQL database to replace in-memory mocks (Academy, Marketplace) with persistent storage. Please review the proposed schema additions.
> The Workflow Builder will require a new frontend dependency (`reactflow` or similar) to handle DAG visualization.

---

## Proposed Changes

### 1. Database Schema Additions
The current schema (`backend/app/db/models.py`) only tracks Users, Conversations, Messages, Artifacts, Experiments, and AuditLogs. We must add:

#### [MODIFY] `backend/app/db/models.py`
Add the following SQLAlchemy classes:
- **`AcademyLesson`**: Stores lesson content (Markdown/JSON).
- **`UserProgress`**: Tracks which user completed which lesson and their quiz scores.
- **`Plugin`**: Stores marketplace plugin metadata (Name, Author, Tags, GitHub repo link).
- **`UserPluginInstall`**: Junction table tracking which users installed which plugins.
- **`WorkflowTemplate`**: Stores serialized JSON DAGs (Directed Acyclic Graphs) for quantum experiments.
- **`ProviderCredential`**: Securely stores encrypted API keys (D-Wave, AWS Braket, Azure, IBM) per user or globally.

---

### 2. Backend Orchestration & Routes

#### [MODIFY] `backend/app/routes/academy.py`
- Remove the hardcoded `ACADEMY_LESSONS` list.
- Implement CRUD operations linking to the new `AcademyLesson` and `UserProgress` models.

#### [MODIFY] `backend/app/routes/marketplace.py`
- Remove the hardcoded `COMMUNITY_PLUGINS` list.
- Implement search/filtering against the `Plugin` DB table.
- Implement installation logic targeting `UserPluginInstall`.

#### [NEW] `backend/app/routes/workflows.py`
- Create REST endpoints for the DAG Pipeline Builder.
- Endpoints: `POST /api/workflows/execute` (triggers Celery chains), `GET /api/workflows/status`.

#### [MODIFY] `backend/app/quantum/dwave_provider.py` & `cudaq_provider.py`
- Update providers to fetch their `API_TOKEN` dynamically from the new `ProviderCredential` DB model rather than relying entirely on local `.env` variables, enabling multi-tenant usage.
- Bridge `cudaq_provider.py` to actually execute basic CUDA-Q python kernels rather than returning a static success stub.

---

### 3. Frontend UI Development

#### [MODIFY] `frontend/package.json`
- Add `reactflow` (or similar node-based UI library) for the Workflow orchestration dimension.

#### [NEW] `frontend/src/components/quantum/WorkflowBuilder.tsx`
- Build a visual drag-and-drop workspace where users can connect Quantum Agents, Data Connectors, and Output Visualizers as nodes in a DAG.
- Generate and submit JSON payloads to the new `/api/workflows` router.

#### [MODIFY] `frontend/src/components/layout/LearningAcademy.tsx`
- Update API fetching logic to support pagination and dynamic content from the PostgreSQL backend.
- Remove any assumptions about localized mock data.

#### [MODIFY] `frontend/src/components/layout/MarketplacePanel.tsx`
- Update to support dynamic plugin installs tracking via the backed DB rather than ephemeral React state.

#### [NEW] `frontend/src/components/layout/ProviderSettings.tsx`
- Build a secure UI panel for users to input their D-Wave Ocean tokens, AWS Braket keys, and IBM Quantum keys, securely posting them to the `ProviderCredential` backend.

---

### 4. Live Data Connectors

#### [NEW] `backend/app/feeds/finance.py`
- Implement Yahoo Finance (yfinance) or Alpha Vantage polling to feed live arrays into the `finance_agent.py` for QAOA portfolio optimization.

#### [MODIFY] `backend/app/agents/sensing_agent.py` and `networking_agent.py`
- Expose their existing hardcoded Qiskit circuits as callable API endpoints rather than just returning markdown strings, allowing the new Workflow Builder to actually "run" them in sequence.

---

## Verification Plan

### Automated Tests
1. **Database:** Run Alembic migrations and use `pytest` to assert that writing to the new `AcademyLesson` and `Plugin` tables succeeds.
2. **Backend API:** Run `pytest backend/tests/test_academy.py` and `test_marketplace.py` to ensure the simulated REST calls return 200 OK and valid JSON identical in shape to the original mocks.
3. **Frontend:** Run `npm run test` (Vitest) focusing on the new WorkflowBuilder node rendering.

### Manual Verification
1. Boot the entire stack via `docker compose --profile dev up -d`.
2. Open the UI, navigate to the **Marketplace**, and attempt to "Install" a plugin. Refresh the page and verify the plugin remains installed (proving PostgreSQL DB persistence).
3. Navigate to **Academy**, complete a lesson quiz, refresh, and verify completion persists.
4. Navigate to the new **Workflow Builder**, drag a "Sensing Agent" node, connect it to a "Results Visualization" node, and click "Execute Pipeline". Verify Celery picks up the job in the docker logs.
