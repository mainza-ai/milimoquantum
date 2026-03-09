# Milimo Quantum Remediation Plan

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Prioritized Issue Registry](#2-prioritized-issue-registry)
3. [Phase-by-Phase Remediation Roadmap](#3-phase-by-phase-remediation-roadmap)
4. [Dependency Upgrade Plan](#4-dependency-upgrade-plan)
5. [Testing Strategy](#5-testing-strategy)
6. [Refactoring Guidelines](#6-refactoring-guidelines)
7. [Definition of Done](#7-definition-of-done)
8. [Risk Register](#8-risk-register)

---

## 1. Executive Summary

Following a comprehensive audit of the Milimo Quantum platform, the overall health of the codebase shows a strong "Scientific Skeleton" on the backend with significant UI integration gaps on the frontend. While all existing unit tests pass, the test suite only covers 15% of the application. More critically, there are severe architectural and security vulnerabilities—such as bypassed authentication, unencrypted P2P syncing, and destructive chat persistence—that prevent the platform from being production-ready.

This remediation plan outlines the structured, prioritized approach required to resolve these issues, harden the security posture, eliminate tech debt, and seamlessly expose the powerful backend engine safely and intuitively to end users.

---

## 2. Prioritized Issue Registry

| Issue ID | Category | Issue | Affected File(s) / Lines | Recommended Fix | Effort | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CRIT-01** | Security | Authentication Bypass | `backend/app/auth.py:28-45` | Remove hardcoded `dev-user-id` fallback. Enforce `AUTH_ENABLED=True` by default and complete Keycloak integration. | M | Backend |
| **CRIT-02** | Data / Perf | Destructive Chat Persistence | `backend/app/storage.py` | Refactor the save logic to perform delta appends on messages instead of full delete/re-insert. | M | Backend |
| **HIGH-01** | Architecture | Missing UI Integrations | `frontend/src/` | Build dedicated UI components for HPC job routing, error mitigation, and 9 cloud providers. | XL | Frontend |
| **HIGH-02** | Security | Hardcoded Secrets | `backend/app/graph/neo4j_client.py:30` | Remove hardcoded `milimo-quantum-graph` password. Move completely to environment variables. | S | DevOps |
| **HIGH-03** | Architecture | Polling Loop in Sync Engine | `backend/app/experiments/sync_engine.py` | Replace 10-second polling loop with event-driven WebSockets or SQLAlchemy `after_commit` hooks. | L | Backend |
| **HIGH-04** | Security | Insecure P2P WebSockets | `backend/app/routes/sync.py` | Implement WSS (TLS), JWT auth, and channel authorization for device syncing. | L | Backend |
| **MED-01** | Quality | Low Test Coverage (15%) | `backend/app/` globally | Implement tests covering cloud providers, pubchem feeds, and mitigation models to hit 70%+ baseline. | XL | Backend |
| **MED-02** | Dependencies| Frontend XSS Vulnerability | `frontend/package.json` | Upgrade `dompurify` to version >3.3.1 via `npm audit fix`. | S | Frontend |
| **MED-03** | Quality | Frontend Linting Errors | `frontend/src/` globally | Refactor React components to remove conditional hook calls (e.g., `CircuitVisualizer.tsx:142`) and type `any`. | M | Frontend |
| **MED-04** | Security | Path Traversal Risk | `upload_file` endpoints | Sanitize filenames using secure UUID generation; restrict allowed MIME types. | S | Backend |
| **MED-05** | Security | Missing CSRF Tokens | FastApi Backend | Implement a CSRF middleware for all state-modifying requests. | M | Backend |
| **LOW-01** | Code Quality | Unused Imports / Undefined | `backend/app/worker/tasks.py` etc. | Run `ruff check --fix` and manually resolve undefined variables across the backend. | S | Backend |
| **LOW-02** | Dependencies| Unpinned Python Dependencies| `backend/requirements.txt` | Pin indirect dependencies natively (`qiskit`, `torch`, `python-jose`, etc.) using poetry or pip-tools. | S | DevOps |
| **LOW-03** | Code Quality | Hardcoded Dates & Anti-patterns | `backend/app/agents/` | Extract hardcoded dates and model versions into `config.py` variables. Remove `TODO`/`HACK` logs. | S | Backend |
| **LOW-04** | Architecture | Volatile Benchmarking Storage | `backend/app/quantum/benchmarking.py` | Migrate `BENCHMARK_HISTORY` from an in-memory list to PostgreSQL via SQLAlchemy. | M | Backend |
| **ADV-01** | Architecture | GraphRAG / FalkorDB stubs | `backend/app/graph/agent_memory.py` | Implement semantic vector retrieval and graph traversal logic safely. | XL | Backend |
| **ADV-02** | Data | Mocked Live Connectors | `backend/app/feeds/` | Build functional API web scraping and REST integration for sources. | L | Backend |
| **ADV-03** | Architecture | Missing QPU Adapters | `backend/app/quantum/cloud_backends.py` | Create routing execution schemas for QuEra, IonQ, Quantinuum, Willow. | M | Backend |
| **ADV-04** | Architecture | Incomplete Sim Agents | `sensing` / `networking` agents | Write dedicated QuTiP and SquidASM/NetSquid integrations for these agents. | XL | Backend |
| **ADV-05** | Enterprise | Weak Multi-Tenancy / Plugins | Backend DB Modules | Enforce strict RBAC sharing schemas and scaffold plugin persistence for Marketplace. | L | Backend |
| **ADV-06** | UI/UX | Missing DAG Workflow UI | Frontend / Celery Workers | Adopt React Flow for visually mapping multi-step execution workflows to Celery DAGs. | XL | Fullstack |

---

## 3. Phase-by-Phase Remediation Roadmap

### Phase 1 – Critical Fixes (Weeks 1-2)
**Goal:** Seal security holes, stop data destruction, and establish baseline compliance.
*   **Fix CRIT-01:** Remove `dev-user-id` bypass. Strictly validate Keycloak JWTs across API access edges.
*   **Fix CRIT-02:** Rewrite the `storage.py` conversation saving loop to use UPSERT / specific ID appending.
*   **Fix HIGH-02:** Strip all hardcoded passwords out of the repository. Update `.env.template`.
*   **Fix MED-02:** Run `npm audit fix` in `/frontend`, verify DOMPurify patch against XSS.
*   **Fix MED-04:** Add sanitization middleware wrapper to all file uploads.

### Phase 2 – High Priority Refactors (Weeks 3-5)
**Goal:** Address architecture issues, structural vulnerabilities, and major tech debt.
*   **Fix HIGH-04:** Implement secure, authenticated, WSS channels for device peer-to-peer sync engine.
*   **Fix HIGH-03:** Rip out 10-second polling. Use SQLAlchemy listener events to push state changes directly. 
*   **Fix MED-05:** Apply cross-site request forgery prevention headers to the frontend requests and validate on API routes.
*   **Fix LOW-04:** Migrate benchmarking analytics to relational persistent storage, ending the "reboot data-loss" bug.

### Phase 3 – Medium Improvements (Weeks 6-8)
**Goal:** Bridge the UI gap, overhaul automated test stability, and stabilize types.
*   **Fix HIGH-01:** Scaffold frontend generic panels for Cloud Providers, Fault Tolerance Lab, and HPC Submissions.
*   **Fix MED-01:** Dedicated sprint to push backend coverage from 15% out to target minimums. Add mocks for Quantum HAL boundaries.
*   **Fix MED-03:** Eliminate `any` inside the Typescript source. Re-arrange conditional React `useEffect` / `useCallback` invocations to comply with hook rules.
*   **Dependencies:** Complete **LOW-02** by locking Python dependencies.

### Phase 4 – Low / Polish (Weeks 9-10)
**Goal:** Document correctly, strip anti-patterns, maintain formatting.
*   **Fix LOW-01:** General sweep of Ruff warnings (`--fix` runs, variable initialization checks).
*   **Fix LOW-03:** Clean out all `# TODO` and `# HACK` comments either by resolving the technical deficit or converting them into Jira/GitHub tracked issues. 
*   **Documentation:** Re-align `/docs` architecture definitions to reflect the actual deployed HAL and Keycloak dependencies.

### Phase 5 – Advanced Feature Implementation (Missing Dimensions)
**Goal:** Complete the mocked and stubbed features identified in the Deep Dive Audit to achieve full enterprise grade equivalence.
*   **ADV-01 (Graph Intelligence):** Fully map semantic vector retrieval and sub-graph traversals across Neo4j and temporal agent memory utilizing FalkorDB and Kuzu.
*   **ADV-02 (Live Data Connectors):** Implement functional API ingestion for `arxiv.py`, `pubchem.py`, and `finance.py`, replacing the existing placeholder mocks.
*   **ADV-03 (Hardware Expansions):** Formally define Direct Adapters for missing cloud hardware (IonQ, QuEra, Quantinuum, Google Willow) within `cloud_backends.py`.
*   **ADV-04 (Advanced Simulators):** Solidify the Quantum Sensing Agent (NV-center magnetometry, atom interferometry) and Networking Agent (SquidASM/NetSquid, CV-QKD) simulations.
*   **ADV-05 (Enterprise & Marketplace):** Scaffold actual PostgreSQL-backed RBAC data schemas for secure project sharing, and implement the backend models for the App Marketplace plugin manager.
*   **ADV-06 (DAG Orchestration):** Integrate a functional React Flow UI with the Celery backend allowing for drag-and-drop complex DAG-based quantum workflow scheduling.

---

## 4. Dependency Upgrade Plan

| Package | Current Version | Target Version | Focus / Breaking Changes |
| :--- | :--- | :--- | :--- |
| `dompurify` (npm) | `3.1.3` | `^3.3.1` | **Security (XSS)**. Re-test all markdown artifact renders via `ArtifactPanel` post-upgrade. |
| `qiskit` (pip) | `<2.0.0` (Unpinned) | `1.x.x` (Pinned) | **Stability**. Lock to a designated `1.x` release prior to Qiskit 2.0 to avoid breaking imports (`qiskit.algorithms` deprecations). |
| `torch` (pip) | Unpinned | `==2.1.0` | **HPC Compatibility**. Lock for deterministic MLX & CPU modeling environments natively on Apple Silicon/CUDA. |
| `sentence-transformers`| Unpinned | `==2.2.2` | **Reproducibility**. Lock down feature sets mapped to expected ChromaDB output embeddings. |
| `python-jose` (pip)| `>=3.3.0` | `==3.3.0` | **Security**. Strict pin required by `safety` scanner; investigate replacement with `PyJWT` if `jose` becomes unmaintained. |

---

## 5. Testing Strategy

The current 15% code coverage is unacceptable for production readiness.
*   **Frameworks:** `pytest` (Backend), `Vitest` + `React Testing Library` (Frontend).
*   **Target Coverage:** Minimum **70%** backend `app/` line coverage required prior to PR merges.
*   **New Tests Required:**
    *   **Cloud Providers:** Create `patch` based unit tests simulating `qiskit_ibm_runtime` and `boto3` for Amazon Braket.
    *   **Feeds:** Mock external API calls for PubChem, Finance, and arXiv interfaces.
    *   **Storage Tiers:** Implement delta-patching `storage.py` and benchmark tests utilizing an in-memory SQLite fixture to simulate DB behaviors heavily.
    *   **Auth Gates:** Route-level permission checks for valid, expired, and absent JWTs.

---

## 6. Refactoring Guidelines

To prevent the re-introduction of existing technical debt, the team must adhere to the following conventions during remediation:
1.  **Strict Typing:** Both TypeScript and Python must be strictly typed. Pydantic models must be utilized for *all* inbound JSON payloads. The usage of `any` in TS is prohibited.
2.  **No Secrets in Code:** Utilize `.env` config environments relying on `pydantic-settings` to manage default falls/raises. No hardcoded password assignments (e.g., `password="default123"`).
3.  **Hooks at the Top:** React hooks (`useState`, `useEffect`, `useRef`) must be defined at the absolute top level of the component block without conditional wrappers.
4.  **Delta Overwrites:** Never use a complete row deletion approach to overwrite data relationships (like the persistent chat storage). Utilize Upserts / SQL merges.
5.  **Event Driven Design:** Replace `while/sleep` polling loops with asynchronous observers, WebSockets, or SQLAlchemy ORM hooks.

---

## 7. Definition of Done

A phase is considered complete when:
*   All tests are passing in CI/CD pipeline.
*   Backend unit test coverage check hits `>= 70%`.
*   Frontend unit test suite runs with no ESLint errors/warnings (`npm run lint`).
*   Vulnerability scanners (`npm audit` & `safety check`) return zero immediate/moderate/critical alerts.
*   Peer review has been conducted by at least one secondary owner.
*   The application launches properly locally without hardcoded dependencies causing boot failure.

---

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Authentication Lockout** | High | High | Resolving **CRIT-01** (enforcing Keycloak over the dev-bypass) will lock out frontend developers without running Keycloak instances. *Mitigation:* Supply a 1-click `docker-compose.auth.yml` initialization script specifically for local DEV Keycloak seeding. |
| **Data Migration Loss** | Medium | Severe | Fixing **CRIT-02** and **LOW-04** involves altering database schema models around chat arrays and benchmark storage. *Mitigation:* Ensure Alembic migration scripts are tested on a backup dump of the DB before enforcing. |
| **P2P WebSocket Destabilization** | Medium | Medium | Upgrading WebSockets to secure protocols (WSS/JWT) might break offline-sync compatibility temporarily. *Mitigation:* Roll this out individually mapped to specific versioning headers, separating V1 and V2 clients gracefully. |
| **Cloud Provider Deprecations** | High | Low | If updating `qiskit` or provider SDKs during pinning, cloud endpoint APIs might have silently updated syntax. *Mitigation:* Write integration "smoke tests" against the cloud hardware to hit `/status` endpoints natively as tests prior to releasing. |
