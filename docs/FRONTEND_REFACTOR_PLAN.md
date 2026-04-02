# Milimo Quantum Frontend Refactor Plan

**Date:** April 2, 2026  
**Status:** In Progress  
**Version:** 1.0  
**Last Updated:** April 2, 2026

---

## Implementation Progress

### ✅ Completed (April 2, 2026)

| Phase | Task | Status |
|-------|------|--------|
| 1 | Wire HardwareBrowser to backend | ✅ Done |
| 1 | Wire QRNGPanel to backend | ✅ Done |
| 1 | Fix ErrorMitigation hardcoded result | ✅ Done |
| 2 | Implement expandable module drawer | ✅ Done |
| 3 | Register HPC extension | ✅ Done |
| 3 | Register Workflow extension | ✅ Done |
| 3 | Register Audit extension | ✅ Done |
| 3 | Create & register Graph Intelligence panel | ✅ Done |

### 🔄 In Progress

| Phase | Task | Status |
|-------|------|--------|
| 4 | Split SettingsPanel into sub-components | Pending |
| 4 | Add error boundaries to extensions | Pending |
| 4 | Add loading/skeleton states | Pending |
| 5 | Add keyboard shortcuts | Pending |
| 5 | Performance optimization | Pending |

### New Files Created

- `frontend/src/components/layout/ModuleDrawer.tsx` - Expandable module drawer component
- `frontend/src/components/graph/GraphPanel.tsx` - Graph Intelligence panel
- `frontend/src/extensions/hpc/index.ts` - HPC Portal extension registration
- `frontend/src/extensions/workflow/index.ts` - Workflow Builder extension registration
- `frontend/src/extensions/audit/index.ts` - Audit Dashboard extension registration
- `frontend/src/extensions/graph/index.ts` - Graph Intelligence extension registration

### Files Modified

- `frontend/src/components/layout/Sidebar.tsx` - Integrated module drawer, added quick access buttons
- `frontend/src/components/quantum/HardwareBrowser.tsx` - Wired to backend API
- `frontend/src/components/quantum/QRNGPanel.tsx` - Wired to backend API
- `frontend/src/components/quantum/ErrorMitigation.tsx` - Uses API response data
- `frontend/src/main.tsx` - Added new extension registrations

---

## Executive Summary

This document outlines a comprehensive refactoring plan for the Milimo Quantum frontend to align with the vision of a **Hybrid Research Operating System** as described in `docs/MILIMO_QUANTUM_SYSTEM.md`. The current frontend suffers from several issues including a crowded/hidden sidebar, missing backend wiring, hardcoded stub data, and inconsistent UX patterns.

---

## Part 1: Current State Assessment

### 1.1 Critical Issues Found

| Issue | Component | File | Severity |
|-------|-----------|------|----------|
| **HardwareBrowser uses hardcoded mock data** | HardwareBrowser.tsx | `frontend/src/components/quantum/HardwareBrowser.tsx:13-18` | CRITICAL |
| **QRNGPanel uses fake entropy** | QRNGPanel.tsx | `frontend/src/components/quantum/QRNGPanel.tsx:16` | HIGH |
| **ErrorMitigation hardcoded result** | ErrorMitigation.tsx | `frontend/src/components/quantum/ErrorMitigation.tsx:73` | HIGH |
| **Academy "run code" event orphan** | LearningAcademy.tsx | `frontend/src/components/layout/LearningAcademy.tsx:88-92` | MEDIUM |
| **Crowded footer icons (8 in ~260px)** | Sidebar.tsx | `frontend/src/components/layout/Sidebar.tsx:288-296` | HIGH |
| **Settings not in extension loop** | Sidebar.tsx | `frontend/src/components/layout/Sidebar.tsx:300` | MEDIUM |
| **Silent null return on missing extension** | WorkspaceManager.tsx | `frontend/src/components/layout/WorkspaceManager.tsx:14-17` | MEDIUM |

### 1.2 Components Requiring Backend Wiring

| Component | Current State | Missing API Endpoint |
|-----------|--------------|---------------------|
| `HardwareBrowser.tsx` | Hardcoded mock data | `/api/quantum/hardware-backends` |
| `QRNGPanel.tsx` | Fake entropy (Math.random()) | `/api/qrng/bits/:length` (exists, not called) |
| `ErrorMitigation.tsx` | Hardcoded +12.4% | `/api/quantum/mitigate/:circuit` (exists, not used) |

---

## Part 2: Backend-Frontend Wiring Inventory

### 2.1 Complete API Coverage Matrix

| Frontend Function | API Endpoint | Backend Route | Status |
|-------------------|--------------|---------------|--------|
| **Chat** | | | |
| Send message | `POST /api/chat/send` | `routes/chat.py` | ✅ Wired |
| SSE streaming | `streamChat()` | `routes/chat.py` | ✅ Wired |
| Get conversations | `GET /api/chat/conversations` | `routes/chat.py` | ✅ Wired |
| Delete conversation | `DELETE /api/chat/conversations/:id` | `routes/chat.py` | ✅ Wired |
| **Quantum** | | | |
| Quantum status | `GET /api/quantum/status` | `routes/quantum.py` | ✅ Wired |
| Execute circuit | `POST /api/quantum/execute/:name` | `routes/quantum.py` | ✅ Wired |
| Error mitigation | `POST /api/quantum/mitigate/:circuit` | `routes/quantum.py` | ❌ Not wired (ErrorMitigation.tsx) |
| Hardware providers | `GET /api/quantum/providers` | `routes/quantum.py` | ✅ Wired |
| Hardware backends | `GET /api/quantum/hardware-backends` | `routes/quantum.py` | ❌ Missing endpoint + component |
| Fault tolerance | `GET /api/quantum/ft/resource-estimation` | `routes/quantum.py` | ✅ Wired |
| **QRNG** | | | |
| Random bits | `GET /api/qrng/bits/:length` | `routes/qrng.py` | ❌ Not wired (QRNGPanel.tsx) |
| **Benchmarks** | | | |
| Run benchmark | `POST /api/benchmarks/run` | `routes/benchmarks.py` | ✅ Wired |
| Benchmark history | `GET /api/benchmarks/history` | `routes/benchmarks.py` | ✅ Wired |
| **VQE/Autoresearch** | | | |
| Run VQE | `POST /api/autoresearch/vqe` | `extensions/autoresearch/extension.py` | ✅ Wired |
| Run autoresearch | `POST /api/autoresearch/run` | `extensions/autoresearch/extension.py` | ✅ Wired |
| Prepare data | `POST /api/autoresearch/prepare` | `extensions/autoresearch/extension.py` | ✅ Wired |
| Fetch results | `GET /api/autoresearch/results` | `extensions/autoresearch/extension.py` | ✅ Wired |
| **Projects** | | | |
| List projects | `GET /api/projects/` | `routes/projects.py` | ✅ Wired |
| Create project | `POST /api/projects/` | `routes/projects.py` | ✅ Wired |
| Delete project | `DELETE /api/projects/:id` | `routes/projects.py` | ✅ Wired |
| **Settings** | | | |
| Get settings | `GET /api/settings/` | `routes/settings.py` | ✅ Wired |
| Update settings | `PUT /api/settings/` | `routes/settings.py` | ✅ Wired |
| Get MLX models | `GET /api/settings/mlx/models` | `routes/settings.py` | ✅ Wired |
| Pull MLX model | `POST /api/settings/mlx/pull` | `routes/settings.py` | ✅ Wired |
| Cloud providers | `GET /api/settings/cloud-providers` | `routes/settings.py` | ✅ Wired |
| Set cloud provider | `PUT /api/settings/cloud-provider` | `routes/settings.py` | ✅ Wired |
| **Analytics** | | | |
| Analytics summary | `GET /api/analytics/summary` | `routes/analytics.py` | ✅ Wired |
| Circuit stats | `GET /api/analytics/circuits` | `routes/analytics.py` | ✅ Wired |
| **Graph** | | | |
| Graph status | `GET /api/graph/status` | `routes/graph.py` | ✅ Wired |
| Related nodes | `GET /api/graph/related` | `routes/graph.py` | ✅ Wired |
| Graph stats | `GET /api/graph/stats` | `routes/graph.py` | ✅ Wired |
| Agent memory | `GET /api/graph/memory/:agentType` | `routes/graph.py` | ✅ Wired |
| **Academy** | | | |
| Get lessons | `GET /api/academy/lessons` | `routes/academy.py` | ✅ Wired |
| Get lesson | `GET /api/academy/lessons/:id` | `routes/academy.py` | ✅ Wired |
| Save progress | `POST /api/academy/progress` | `routes/academy.py` | ✅ Wired |
| **Feeds** | | | |
| arXiv search | `GET /api/feeds/arxiv` | `routes/feeds.py` | ✅ Wired |
| PubChem search | `GET /api/feeds/pubchem` | `routes/feeds.py` | ✅ Wired |
| Stock prices | `GET /api/feeds/finance` | `routes/feeds.py` | ✅ Wired |
| **HPC** | | | |
| HPC status | `GET /api/hpc/status` | `routes/hpc.py` | ✅ Wired |
| **Marketplace** | | | |
| Get plugins | `GET /api/marketplace/algorithms` | `routes/marketplace.py` | ✅ Wired |
| Install plugin | `POST /api/marketplace/install/:id` | `routes/marketplace.py` | ✅ Wired |
| **MQDD** | | | |
| MQDD workflow | `POST /api/mqdd/workflow` | `extensions/mqdd/extension.py` | ✅ Wired |
| **Jobs** | | | |
| Execute code | `POST /api/jobs/execute-code` | `routes/jobs.py` | ✅ Wired |
| Job status | `GET /api/jobs/:id/status` | `routes/jobs.py` | ✅ Wired |

### 2.2 Missing Backend Endpoints

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `GET /api/quantum/hardware-backends` | Fetch real hardware backend status | HIGH |

---

## Part 3: Sidebar & Navigation Redesign

### 3.1 Current Problems

1. **Crowded Footer Icons**: 8 icons in ~260px sidebar width = ~32px per icon with 2px gaps
2. **14 Agents Hidden**: All agents in a dropdown, categories not visible
3. **No "More" Overflow**: Only 8 extensions shown, rest inaccessible
4. **Inconsistent Settings**: Hardcoded outside extension loop
5. **No Active Indicator**: Footer icons don't show which extension is open

### 3.2 Proposed Redesign

#### Option A: Expandable Module Drawer (Recommended)

Create a **collapsible module drawer** that slides out from the bottom:

```
┌─────────────────────────────────────────────────────────────┐
│ [Logo]                                          [+] [⚙️]   │
├─────────────────────────────────────────────────────────────┤
│ [+ New Chat]                                                │
│                                                             │
│ [Agent: 💻 Code Agent ▼]                                    │
│   ├── Core: ⚛️ Milimo, 💻 Code, 📚 Research, 📋 Planning  │
│   ├── Science: 🧪 Chemistry, 🌍 Climate, 📡 Sensing        │
│   ├── Industry: 📈 Finance, ⚡ Optimize, 🔐 Crypto, ❄️ D-Wave│
│   └── Advanced: 🧠 QML, 🕸️ QGI, 🌐 Networking              │
├─────────────────────────────────────────────────────────────┤
│ [💬 Conversations...]                                        │
├─────────────────────────────────────────────────────────────┤
│ [Connected ●]                              [MQDD] [Auto]   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │ MODULE DRAWER (expandable)                          │   │
│  │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐     │   │
│  │ │Search│ │Analytics│ │Projects│ │Dashboard│ │Academy│ │Marketplace│
│  │ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘     │   │
│  │ ┌─────┐ ┌─────┐ ┌─────┐                              │   │
│  │ │ HPC │ │Graph│ │Workflow│                          │   │
│  │ └─────┘ └─────┘ └─────┘                              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### Option B: Two-Row Footer with Categories

Group extensions by category with a two-row footer:

```
┌─────────────────────────────────────────────────────────────┐
│ [Logo]                                          [+] [⚙️]   │
├─────────────────────────────────────────────────────────────┤
│ [+ New Chat]                                                │
│                                                             │
│ [💻 Code Agent ▼]                                           │
├─────────────────────────────────────────────────────────────┤
│ [💬 Conversations...]                                       │
├─────────────────────────────────────────────────────────────┤
│ TOOLS:  [🔍] [📊] [📁] [⚛️] [🎓] [🏪]                       │
│ PANELS: [🧬 MQDD] [🚀 Auto] [🔧 HPC] [🕸️ Graph] [⏱️ Jobs] │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Recommended Implementation

**Implement Option A** - the expandable module drawer because:
- Provides space for all modules without crowding
- Maintains quick access to top 2 (MQDD, Autoresearch)
- Allows expansion to reveal all modules
- Scales well as more modules are added
- Consistent with modern OS conventions (e.g., macOS Dock)

---

## Part 4: Component Refactor Checklist

### 4.1 CRITICAL - Must Fix Before Release

| Component | Issue | Fix | Effort |
|-----------|-------|-----|--------|
| `HardwareBrowser.tsx` | Hardcoded mock data | Wire to backend or create proper API + UI | 2h |
| `QRNGPanel.tsx` | Fake entropy | Wire to `/api/qrng/bits/:length` | 1h |
| `ErrorMitigation.tsx` | Hardcoded +12.4% | Use `result.improvement` from API | 1h |
| `Sidebar.tsx` | Crowded footer | Implement expandable module drawer | 4h |

### 4.2 HIGH - Important for UX

| Component | Issue | Fix | Effort |
|-----------|-------|-----|--------|
| `WorkspaceManager.tsx` | Silent null return | Add warning/error state | 1h |
| `SettingsPanel.tsx` | 844 lines, complex | Split into sub-components | 4h |
| `Sidebar.tsx` | Settings hardcoded | Move to extension registry | 1h |
| `LearningAcademy.tsx` | Orphan event | Wire to code execution or remove | 2h |

### 4.3 MEDIUM - Polish

| Component | Issue | Fix | Effort |
|-----------|-------|-----|--------|
| `QuantumDashboard.tsx` | Indentation issues | Format code | 1h |
| `QuantumDashboard.tsx` | String(simulators[name]) | Verify API returns strings | 1h |
| Add keyboard navigation | N/A | Add keyboard shortcuts | 3h |
| Extension search/filter | N/A | Add search to drawer | 2h |

---

## Part 5: Extension Registry Enhancement

### 5.1 Current Extensions (9 registered)

| ID | Name | Icon | Category | Status |
|----|------|------|----------|--------|
| search | Search | 🔍 | tool | ✅ Working |
| analytics | Analytics | 📊 | tool | ✅ Working |
| projects | Projects | 📁 | tool | ✅ Working |
| dashboard | Dashboard | ⚛️ | tool | ✅ Working |
| academy | Academy | 🎓 | tool | ✅ Working |
| marketplace | Marketplace | 🏪 | tool | ✅ Working |
| settings | Settings | ⚙️ | tool | ✅ Working |
| mqdd | Drug Discovery | 🧬 | science | ✅ Working |
| autoresearch | Autoresearch-MLX | 🚀 | science | ✅ Working |

### 5.2 Missing Extensions (Should be registered)

| ID | Name | Icon | Category | Notes |
|----|------|------|----------|-------|
| hpc | HPC Portal | 🔧 | tool | Component exists at `components/hpc/HPCPortal.tsx` |
| graph | Graph Intelligence | 🕸️ | tool | Component should be created |
| workflows | Workflow Builder | ⏱️ | tool | Component exists at `components/workflow/WorkflowBuilder.tsx` |
| audit | Audit Dashboard | 📋 | admin | Component exists at `components/admin/AuditDashboard.tsx` |

### 5.3 Proposed Extension Registration Flow

```typescript
// In main.tsx, extend registration:
registerCorePlugins();    // Existing 7 extensions
registerMQDDExtension(); // Existing 1 extension  
registerAutoresearchExtension(); // Existing 1 extension
registerHPCExtension();    // NEW
registerGraphExtension(); // NEW
registerWorkflowExtension(); // NEW
registerAuditExtension(); // NEW
```

---

## Part 6: Visual Design Alignment

### 6.1 Design System Gaps

Based on `docs/MILIMO_QUANTUM_SYSTEM.md`, the frontend should embody:

1. **"Hybrid Research OS"** - Professional, scientific aesthetic
2. **"17 Specialized Agents"** - Clear agent identity and selection
3. **"Quantum Execution Pipeline"** - Visual circuit/workflow representation
4. **"Knowledge Graph"** - Graph visualizations

### 6.2 Color Palette (from codebase)

```css
/* Current - should be formalized in design tokens */
--cyan-400: #22d3ee;    /* Primary accent (glowing effects) */
--cyan-500: #06b6d4;    /* Primary buttons, active states */
--slate-900: #0f172a;  /* Dark mode backgrounds */
--slate-800: #1e293b;  /* Card backgrounds */
--slate-700: #334155;  /* Borders, dividers */
```

### 6.3 Typography

- **Primary Font**: System font stack (no external dependency)
- **Monospace**: For code/circuits - should use `ui-monospace, SFMono-Regular, monospace`

### 6.4 Spacing & Layout

- **Sidebar width**: Fixed 260px
- **Grid system**: Tailwind CSS default (12-column)
- **Breakpoints**: sm (640px), md (768px), lg (1024px), xl (1280px)

---

## Part 7: Implementation Phases

### Phase 1: Critical Backend Wiring (Week 1)
**Goal**: Fix all non-functional components

| Task | Component | Time |
|------|-----------|------|
| 1.1 | Wire HardwareBrowser to backend | 2h |
| 1.2 | Wire QRNGPanel to backend | 1h |
| 1.3 | Wire ErrorMitigation to backend | 1h |
| 1.4 | Add missing `/api/quantum/hardware-backends` endpoint | 2h |
| 1.5 | Test all wired endpoints | 2h |

**Deliverables**: All components functional with real backend data

### Phase 2: Sidebar Redesign (Week 2)
**Goal**: Resolve crowded/hidden navigation issue

| Task | Description | Time |
|------|-------------|------|
| 2.1 | Create ModuleDrawer component | 2h |
| 2.2 | Implement collapsible drawer in Sidebar | 2h |
| 2.3 | Add extension search/filter | 1h |
| 2.4 | Move Settings to extension registry | 1h |
| 2.5 | Add active state indicators | 1h |
| 2.6 | Test with keyboard navigation | 1h |

**Deliverables**: Clean, expandable module navigation

### Phase 3: Missing Extensions (Week 2-3)
**Goal**: Register all existing components as extensions

| Task | Extension | Time |
|------|-----------|------|
| 3.1 | Register HPC Portal | 2h |
| 3.2 | Register Workflow Builder | 2h |
| 3.3 | Create & register Graph Intelligence panel | 4h |
| 3.4 | Register Audit Dashboard | 2h |
| 3.5 | Update WorkspaceManager to handle new extensions | 2h |

**Deliverables**: All components accessible via module drawer

### Phase 4: Code Quality (Week 3)
**Goal**: Clean up technical debt

| Task | Description | Time |
|------|-------------|------|
| 4.1 | Split SettingsPanel into sub-components | 4h |
| 4.2 | Add error boundaries to extensions | 2h |
| 4.3 | Fix QuantumDashboard type issues | 1h |
| 4.4 | Add loading/skeleton states | 2h |
| 4.5 | Format code (Prettier) | 1h |

### Phase 5: Polish & Advanced Features (Week 4)
**Goal**: Professional finish

| Task | Description | Time |
|------|-------------|------|
| 5.1 | Add keyboard shortcuts | 3h |
| 5.2 | Implement notification system | 3h |
| 5.3 | Add tour/onboarding for new users | 4h |
| 5.4 | Performance optimization (lazy loading) | 3h |
| 5.5 | Mobile responsiveness check | 2h |

---

## Part 8: File Structure

### 8.1 Current Structure

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx           # 330 lines
│   │   ├── ChatArea.tsx
│   │   ├── ArtifactPanel.tsx
│   │   ├── WorkspaceManager.tsx
│   │   ├── QuantumDashboard.tsx  # 300+ lines
│   │   ├── SettingsPanel.tsx     # 844 lines ⚠️ TOO LONG
│   │   ├── MarketplacePanel.tsx
│   │   ├── AnalyticsDashboard.tsx
│   │   ├── ProjectsPanel.tsx
│   │   ├── LearningAcademy.tsx
│   │   └── SearchPanel.tsx
│   ├── quantum/
│   │   ├── VQEPanel.tsx
│   │   ├── CircuitBuilder.tsx
│   │   ├── CircuitVisualizer.tsx
│   │   ├── BlochSphere.tsx
│   │   ├── QRNGPanel.tsx         # Needs wiring
│   │   ├── ErrorMitigation.tsx   # Hardcoded result
│   │   ├── FaultTolerance.tsx
│   │   ├── HardwareSettings.tsx
│   │   ├── HardwareBrowser.tsx   # Hardcoded data ❌
│   │   └── panels/
│   │       ├── CloudProviderPanel.tsx
│   │       └── HpcJobsPanel.tsx
│   ├── chat/
│   │   ├── ChatInput.tsx
│   │   └── MessageBubble.tsx
│   ├── artifacts/
│   │   ├── CodeView.tsx
│   │   ├── CircuitView.tsx
│   │   ├── ResultsView.tsx
│   │   ├── NotebookView.tsx
│   │   ├── ReportView.tsx
│   │   └── DatasetView.tsx
│   ├── hpc/
│   │   └── HPCPortal.tsx          # Not registered as extension
│   ├── admin/
│   │   └── AuditDashboard.tsx     # Not registered as extension
│   └── workflow/
│       └── WorkflowBuilder.tsx    # Not registered as extension
├── extensions/
│   ├── registry.ts
│   ├── core-plugins.ts
│   ├── mqdd/
│   └── autoresearch/
├── contexts/
│   ├── WorkspaceContext.tsx
│   └── ProjectContext.tsx
├── hooks/
│   └── useChat.ts
├── services/
│   └── api.ts                     # 466 lines - well organized
└── types/
    └── index.ts                   # Agent definitions
```

### 8.2 Proposed Restructure

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── Sidebar/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ModuleDrawer.tsx      # NEW
│   │   │   ├── AgentSelector.tsx     # NEW - extracted
│   │   │   ├── ConversationList.tsx  # NEW - extracted
│   │   │   └── FooterStatus.tsx      # NEW - extracted
│   │   ├── ChatArea/
│   │   ├── ArtifactPanel/
│   │   ├── WorkspaceManager/
│   │   ├── Settings/                    # SPLIT SettingsPanel
│   │   │   ├── SettingsPanel.tsx
│   │   │   ├── LLMProviderSettings.tsx
│   │   │   ├── QuantumSettings.tsx
│   │   │   └── DisplaySettings.tsx
│   │   └── ...
│   ├── quantum/
│   │   ├── VQEPanel/
│   │   ├── CircuitBuilder/
│   │   └── ...
│   └── ...
├── extensions/
│   ├── registry.ts
│   ├── core-plugins.ts
│   ├── mqdd/
│   ├── autoresearch/
│   ├── hpc/                          # NEW registration
│   ├── graph/                       # NEW - create component
│   ├── workflow/                    # NEW registration
│   └── audit/                       # NEW registration
└── ...
```

---

## Part 9: Testing Strategy

### 9.1 Unit Tests
- All API service functions (mock fetch)
- Component rendering with React Testing Library
- Hook behavior with @testing-library/react-hooks

### 9.2 Integration Tests
- SSE streaming chat flow
- Extension open/close lifecycle
- Project CRUD operations

### 9.3 E2E Tests (Playwright)
- Full user flows (chat → artifact → circuit execution)
- Module drawer expansion
- Settings changes persist

---

## Part 10: Success Metrics

After refactor, the frontend should achieve:

| Metric | Target |
|--------|--------|
| Components with proper backend wiring | 100% |
| Extension accessibility | 100% (all accessible, none hidden) |
| API endpoint coverage | 100% |
| Test coverage | >80% |
| Lighthouse performance | >90 |
| Zero hardcoded mock data in UI | ✅ Achieved |

---

## Appendix A: Quick Wins Checklist

- [x] Wire `HardwareBrowser` to real backend
- [x] Wire `QRNGPanel` to `/api/qrng/bits/:length`
- [x] Fix `ErrorMitigation` to use API result
- [x] Move Settings to extension registry (already in registry, now in module drawer)
- [ ] Add `GET /api/quantum/hardware-backends` backend endpoint (using existing `/api/quantum/providers`)
- [x] Implement expandable module drawer
- [x] Add missing extensions (HPC, Graph, Workflow, Audit)
- [ ] Split `SettingsPanel.tsx` (844 lines → 4 files)
- [ ] Add error boundaries
- [ ] Add keyboard navigation

---

## Appendix B: Priority Order

1. **Critical** (Blocker for release) - ✅ COMPLETED:
   - HardwareBrowser hardcoded data → Fixed: Now fetches from `/api/quantum/providers`
   - QRNGPanel fake entropy → Fixed: Now uses `quantum_certified` from API
   - ErrorMitigation hardcoded result → Fixed: Now uses `result.improvement` from API

2. **High** (Major UX improvement) - ✅ COMPLETED:
   - Sidebar module drawer → Implemented expandable drawer with search
   - Missing extensions registration → Added HPC, Workflow, Audit, Graph extensions
   - Settings in registry → Already registered, now accessible via module drawer
   - Sidebar module drawer
   - Missing extensions registration
   - Settings in registry

3. **Medium** (Technical debt):
   - SettingsPanel split
   - Code formatting
   - Error boundaries

4. **Low** (Polish):
   - Keyboard shortcuts
   - Onboarding tour
   - Mobile optimization
