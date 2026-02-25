# Milimo Quantum — Implementation Rules

## Project Identity
- **Name**: Milimo Quantum
- **Tagline**: "The Universe of Quantum, In One Place"
- **Logo**: `assets/logo_milimo.png` — white/silver + cyan lettermark

## Skills Reference
Before implementing any feature, read the relevant skill(s) in `skills/skills/milimoquantum/`:
- `architecture.md` — 7-layer system, agent roster, storage architecture
- `hal.md` — Hardware Abstraction Layer, platform detection, qubit-count routing
- `agent-system.md` — 14 agents, intent routing, system prompts, SSE protocol
- `quantum-execution.md` — Qiskit v2.x patterns, circuit library, error mitigation
- `frontend.md` — React/TS/TailwindCSS design system, component architecture
- `backend.md` — FastAPI, API endpoints, SSE streaming, project structure

## Design Rules (NON-NEGOTIABLE)

### Color Palette — Logo Only
- **Primary accent**: `#3ecfef` (cyan from logo)
- **Allowed tones**: cyan, teal, silver, white — all derived from the logo
- **FORBIDDEN**: purple, pink, red, gold/yellow, orange, saturated blue, green
- **FORBIDDEN**: generic "AI" rainbow gradients or multi-color accents
- **Background**: Pure black `#000000` and near-black tones only

### Visual Style — Apple.com Inspired
- Glassmorphism with `backdrop-filter: blur(40px+) saturate(180%+)`
- Animations use `cubic-bezier(0.16, 1, 0.3, 1)` easing
- Minimal, clean, premium — not flashy or generic
- The Milimo logo must appear in the sidebar header and welcome screen

## Development Environment

### Frontend
- **Location**: `frontend/`
- **Stack**: Vite 7 + React 18 + TypeScript + TailwindCSS v4
- **Run**: `cd frontend && npm run dev` → `http://localhost:5173`
- **Design tokens**: All in `src/index.css` using `@theme` directive
- **Proxy**: Vite proxies `/api` → `http://localhost:8000`

### Backend
- **Location**: `backend/`
- **Stack**: Python 3.10+ + FastAPI + Qiskit + Ollama
- **Venv**: `milimoenv` (NOT generic `venv`) 
- **Run**: `cd backend && source milimoenv/bin/activate && python run.py` → `http://localhost:8000`
- **Deps**: `requirements.txt` — install into `milimoenv` only

### Development Docs
- **Location**: `development_docs/` — architecture diagrams, project plan, cross-platform guide, graph DB addendum, missing dimensions
- **These are READ-ONLY reference** — never modify these files

## Code Conventions

### Python (Backend)
- Use async route handlers
- Pydantic v2 for all data models
- `from app.module.submodule import X` import pattern
- Use `logging` module, never `print()`
- SSE via `StreamingResponse`, not WebSocket for chat

### TypeScript (Frontend)
- Functional components only, no class components
- Custom hooks for state management (no Redux/Zustand needed yet)
- Emoji icons — no external icon libraries
- All types in `src/types/index.ts`

## Architecture Rules
- **HAL is mandatory** — never hardcode platform assumptions
- **Agents are modular** — each agent is a separate file in `backend/app/agents/`
- **Artifacts are typed** — always use `Artifact` schema with `type`, `title`, `content`, `metadata`
- **Streaming is default** — all chat responses use SSE, never blocking JSON responses
