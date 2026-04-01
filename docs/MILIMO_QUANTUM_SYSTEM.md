# Milimo Quantum System Documentation

> Comprehensive system overview for AI analysis and implementation improvement proposals.

---

## 1. Executive Summary

**Milimo Quantum** is a **Hybrid Research Operating System** that bridges natural language intent with quantum computing execution. The platform enables autonomous scientific discovery by uniting quantum computing SDKs with a sophisticated multi-agent AI network, designed for Apple Silicon local-first execution with cloud extensibility.

### Core Mission
- Democratize quantum computing through natural language interfaces
- Enable autonomous scientific research loops
- Provide hardware-optimized local execution with cloud fallback
- Bridge classical ML (Apple MLX) with quantum workloads

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React 19)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  Sidebar │ │ChatArea  ││Artifact  ││Workspace ││Extensions│          │
│  │          │ │          ││  Panel   ││ Manager  ││  Panel   │          │
│  └────┬─────┘ └────┬─────┘└────┬─────┘└────┬─────┘└────┬─────┘          │
│       │            │           │           │           │                  │
│       └────────────┴───────────┴───────────┴───────────┘                  │
│                              │ SSE Stream                                   │
└──────────────────────────────┼──────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────────────────┐
│                         BACKEND (FastAPI)                                    │
│  ┌───────────────────────────┼───────────────────────────────────────────┐  │
│  │                     API Layer                                           │  │
│  │  /chat  /quantum  /projects  /settings  /analytics  /autoresearch     │  │
│  └───────────────────────────┬───────────────────────────────────────────┘  │
│                              │                                               │
│  ┌─────────────┐ ┌──────────┴──────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ Orchestrator│ │  Intelligence Hub   │ │   Sandbox   │ │   Quantum   │   │
│  │ (Router)    │ │ (Context Enrichment)│ │ (Executor)  │ │  Executor   │   │
│  └──────┬──────┘ └──────────┬──────────┘ └──────┬──────┘ └──────┬──────┘   │
│         │                   │                   │               │           │
│  ┌──────┴──────┐ ┌──────────┴──────────┐       │               │           │
│  │ Agent Layer │ │    Data Sources     │       │               │           │
│ │ (17 agents)│ │ arXiv/PubMed/Finance│ │ │ │
│  └─────────────┘ └─────────────────────┘       │               │           │
│                                                │               │           │
│  ┌─────────────────────────────────────────────┴───────────────┴───────┐   │
│  │                    LLM Provider Abstraction                          │   │
│  │   MLX-LM (local) │ Ollama (local) │ OpenAI │ Anthropic │ Google    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Quantum Backend Abstraction                       │    │
│  │   Aer (local) │ IBM Quantum │ D-Wave │ Amazon Braket │ Azure │ CUDA-Q│   │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────────────────┐
│                         DATA LAYER                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ PostgreSQL  │ │    Redis    │ │    Neo4j    │ │  ChromaDB   │            │
│  │  (SQL)      │ │(Cache/Queue)│ │   (Graph)   │ │  (Vector)   │            │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

#### Backend (Python 3.12+)
| Layer | Technology | Purpose |
|-------|------------|---------|
| Framework | FastAPI 0.115+ | Async API server |
| Quantum Computing | Qiskit 2.x, Qiskit-Aer, Qiskit-Machine-Learning | Circuit construction and simulation |
| Quantum Cloud | qiskit-ibm-runtime, dimod, braket-sdk | Cloud backend integration |
| LLM Inference | MLX-LM, Ollama, OpenAI, Anthropic, Google GenAI | Multi-provider LLM abstraction |
| Task Queue | Celery + Redis | Async job execution |
| Database | PostgreSQL + SQLAlchemy 2.0 | Persistent storage |
| Graph Database | Neo4j, FalkorDB, Kuzu | Knowledge graph |
| Vector Store | ChromaDB | RAG embeddings |
| Authentication | Keycloak (OAuth2) | Enterprise SSO |

#### Frontend (React 19)
| Layer | Technology | Purpose |
|-------|------------|---------|
| Framework | React 19.2 + TypeScript 5.9 | UI framework |
| Build | Vite 7.3 | Development server |
| Styling | Tailwind CSS 4.2 | Utility-first CSS |
| Editor | Monaco Editor | Code editing |
| Visualization | D3.js, XYFlow React | Circuit diagrams, workflow DAGs |
| Rendering | react-markdown, KaTeX | Rich content display |

#### Infrastructure
| Service | Technology | Purpose |
|---------|------------|---------|
| Containers | Docker Compose | Service orchestration |
| Database | PostgreSQL 15-alpine | Primary storage |
| Cache | Redis 7-alpine | Session + queue broker |
| Graph | Neo4j 5-community | Knowledge graph |
| Auth | Keycloak 24.0 | Identity provider |

---

## 3. Core Components

### 3.1 Multi-Agent Orchestrator

The system routes user queries to specialized agents based on intent classification.

**Agent Types (17 registered):**

| Agent | Domain | Capabilities |
|-------|--------|--------------|
| `orchestrator` | General | Primary routing, intent classification |
| `code` | Quantum Code | Qiskit/Cirq/PennyLane generation |
| `research` | Education | arXiv search, paper summarization |
| `chemistry` | Molecular | VQE, molecular simulation (MQDD) |
| `finance` | Optimization | Portfolio optimization, Monte Carlo |
| `optimization` | Combinatorial | QAOA, Max-Cut, TSP |
| `crypto` | Security | QKD, QRNG, post-quantum crypto |
| `qml` | Machine Learning | QNN, QSVM, quantum kernels |
| `climate` | Materials | Battery research, carbon capture |
| `planning` | Workflows | Multi-step decomposition |
| `qgi` | Graph Intelligence | Memory retrieval, concept linking |
| `sensing` | Metrology | NV-centers, quantum sensors |
| `networking` | Communication | Quantum internet, teleportation |
| `dwave` | Annealing | QUBO, Ising models |
| `benchmarking` | Performance | Quantum volume, CLOPS |
| `fault_tolerance` | Error Correction | Surface codes, QEC |
| `autoresearch_analyzer` | ML Training | Results analysis, optimization suggestions |

**Routing Logic:**
```python
# Intent classification pipeline
1. Slash command detection: /code, /research, /vqe, etc.
2. Keyword matching: "simulate" → code, "molecule" → chemistry
3. Context enrichment: Hardware capabilities, project scope
4. Agent dispatch with specialized system prompt
```

### 3.2 Quantum Execution Pipeline

```python
# Execution flow (executor.py)
1. Parse QASM or Qiskit code from sandbox output
2. Construct QuantumCircuit object
3. HAL selects backend:
   - qubits ≤ 24: Aer statevector (local)
   - qubits ≤ 30: Aer MPS (local, memory-efficient)
   - qubits > 30: Route to IBM Cloud
4. Transpile for target backend
5. Execute with error mitigation (ZNE, calibration)
6. Return counts + statevector for visualization
```

**Hardware Abstraction Layer (HAL):**
```python
# Platform-aware configuration
- macOS ARM64: MPS for PyTorch, MLX for LLM, CPU for Aer
- CUDA: GPU acceleration for Aer simulations
- Automatic routing based on qubit count and memory
```

### 3.3 Intelligence Hub

The Intelligence Hub provides unified context enrichment:

```python
# Hub data sources
1. Knowledge Graph (Neo4j): Concept relationships, agent memory
2. Vector Store (ChromaDB): Semantic similarity search
3. Live Feeds:
   - arXiv: Latest quantum papers
   - PubMed: Medical/biological research
   - PubChem: Molecular compound data
   - Yahoo Finance: Market data for optimization
4. Hardware Context: Available backends, qubit limits, GPU status
5. Project Context: Workspace isolation, conversation history
```

### 3.4 Secure Sandbox

AST-based code execution with security layers:

```python
# Sandbox security model
1. AST Parsing: Extract import statements and function calls
2. Import Validation: Whitelist-only modules (qiskit, numpy, etc.)
3. Builtin Restriction: Remove exec, eval, open, __import__
4. Common Mistake Patching:
   - qiskit.providers.aer → qiskit_aer
   - QuantumCircuit() → QuantumCircuit(num_qubits)
5. Timeout: 15-second execution limit with signal interruption
6. Fingerprinting: Deduplicate identical circuits/results
```

### 3.5 Extension System

Dynamic plugin architecture for modular features:

```python
# Extension registration
class Extension:
    id: str                    # Unique identifier
    name: str                  # Display name
    agent_type: str            # Associated agent
    slash_commands: List[str]  # Trigger commands
    intent_patterns: List[str] # Keyword matching
    system_prompt: str         # Agent instructions
    router: APIRouter          # Additional routes

# Registered Extensions:
- MQDD (Drug Discovery): VQE optimization, molecular properties
- Autoresearch: Training loops, VQE ansatz discovery
```

---

## 4. Data Models

### 4.1 SQL Schema

```sql
-- Core entities
User (id, keycloak_id, email, created_at)
Project (id, name, user_id, settings, created_at)
Conversation (id, project_id, title, agent_type, created_at)
Message (id, conversation_id, role, content, artifacts, created_at)
Artifact (id, message_id, type, title, content, metadata)

-- Quantum execution
Experiment (id, project_id, agent, circuit_code, backend, results, parameters)

-- Analytics
BenchmarkResult (id, experiment_id, metric_name, metric_value, timestamp)
AuditLog (id, user_id, action, resource, timestamp)

-- Plugin system
MarketplacePlugin (id, name, description, version, author, manifest)
UserPlugin (id, user_id, plugin_id, enabled, settings)
```

### 4.2 Graph Schema (Neo4j)

```cypher
// Concept graph
(Concept)-[:RELATED_TO]->(Concept)
(Concept)-[:PART_OF]->(Domain)
(Experiment)-[:ADVANCES]->(Concept)
(Agent)-[:SPECIALIZES_IN]->(Domain)

// Agent memory
(User)-[:ASKED_ABOUT]->(Concept)
(Conversation)-[:COVERED]->(Topic)
(Message)-[:REFERENCES]->(Concept)

// VQE-specific (Phase 3)
(Molecule)-[:HAS_HAMILTONIAN]->(Hamiltonian)
(Hamiltonian)-[:SOLVED_BY]->(AnsatzMotif)
(AutoresearchRun)-[:DISCOVERED]->(AnsatzMotif)
(AnsatzMotif)-[:SUCCESSOR_OF]->(AnsatzMotif)
```

### 4.3 Agent Memory Model

```python
# AgentMemory (agent_memory.py)
class AgentMemory:
    # Per-agent episodic memory with JSON fallback
    # Storage: ~/.milimoquantum/agent_memory/{agent_type}.json
    
    MemoryEntry:
        conversation_id: str
        project_id: str
        content: str  # Capped at 2000 chars
        metadata: dict
        memory_type: interaction | preference | result | insight
        timestamp: float
```

### 4.4 Platform Configuration Model

```python
# PlatformConfig (hal.py)
@dataclass
class PlatformConfig:
    os_name: str           # Darwin, Linux, Windows
    arch: str              # arm64, x86_64
    torch_device: str      # mps, cuda, cpu
    aer_device: str        # GPU, CPU
    llm_backend: str       # mlx, ollama, openai
    gpu_available: bool
    gpu_name: str | None
```

> **See Also:** Complete data model documentation in `docs/DATA_MODEL_STRUCTURE.md`

---

## 5. API Endpoints

### 5.1 Core Routes

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| `chat` | `/api/chat` | `POST /send`, `GET /conversations`, `GET /:id`, `DELETE /:id` |
| `quantum` | `/api/quantum` | `POST /execute`, `GET /circuit/visualize`, `POST /circuit/analyze` |
| `projects` | `/api/projects` | `GET /`, `POST /`, `PUT /:id`, `DELETE /:id` |
| `settings` | `/api/settings` | `GET /`, `PUT /`, `GET /models`, `PUT /model` |
| `analytics` | `/api/analytics` | `GET /usage`, `GET /performance`, `GET /agents` |
| `graph` | `/api/graph` | `POST /query`, `GET /schema`, `POST /index` |

### 5.2 Extension Routes

| Router | Prefix | Endpoints |
|--------|--------|-----------|
| `mqdd` | `/api/mqdd` | `POST /vqe`, `POST /molecule`, `GET /properties` |
| `autoresearch` | `/api/autoresearch` | `GET /status`, `GET /results`, `POST /run`, `POST /vqe`, `POST /analysis` |
| `feeds` | `/api/feeds` | `GET /arxiv`, `GET /pubmed`, `GET /finance` |
| `hpc` | `/api/hpc` | `POST /jobs`, `GET /jobs/:id`, `DELETE /jobs/:id` |

---

## 6. Integration Points

### 6.1 LLM Providers

```python
# Multi-provider abstraction (mlx_client.py)
class MLXClient:
    providers = {
        "mlx": MLXProvider,      # Local Apple Silicon
        "ollama": OllamaProvider, # Local HTTP API
        "openai": OpenAIProvider, # Cloud
        "anthropic": AnthropicProvider, # Cloud
        "google": GoogleProvider,  # Cloud
    }
    
    def generate(self, prompt, system_prompt, stream=True):
        provider = self.get_provider()
        return provider.generate(prompt, system_prompt, stream)
```

### 6.2 Quantum Backends

```python
# Backend selection (executor.py)
BACKEND_PRIORITY = [
    ("aer_statevector", lambda n: n <= 24),
    ("aer_mps", lambda n: n <= 30),
    ("ibm_cloud", lambda n: n > 30),
]

def select_backend(num_qubits: int) -> str:
    for name, condition in BACKEND_PRIORITY:
        if condition(num_qubits):
            return name
    return "ibm_cloud"
```

### 6.3 Graph Databases

```python
# Multi-graph support (graph/__init__.py)
GRAPH_PROVIDERS = {
    "neo4j": Neo4jClient,    # Production (Docker)
    "falkordb": FalkorDBClient, # Alternative (Redis-based)
    "kuzu": KuzuClient,      # Embedded fallback
}
```

---

## 7. Security Model

### 7.1 Authentication Flow

```
1. User clicks "Sign In" → Redirect to Keycloak (port 8081)
2. Keycloak OAuth2 implicit flow → Access token returned
3. Token stored in localStorage (mq_token)
4. Token sent in Authorization header for all API requests
5. Backend validates token via Keycloak OpenID Connect
6. User info cached in request state
```

### 7.2 Sandbox Security

| Layer | Mechanism |
|-------|-----------|
| Import Whitelist | `qiskit`, `numpy`, `scipy`, `math`, `dimod`, etc. |
| Builtin Restrictions | Remove `exec`, `eval`, `open`, `__import__`, `compile` |
| Timeout | 15-second limit with SIGALRM |
| Output Limits | Max 1MB stdout/stderr |
| Fingerprinting | SHA-256 hash for deduplication |

### 7.3 API Security

| Layer | Mechanism |
|-------|-----------|
| CSRF | Custom header requirement (X-Requested-With) |
| Rate Limiting | Slowapi with per-endpoint limits |
| Input Validation | Pydantic models for all endpoints |
| File Upload | MIME type + extension whitelist |

---

## 8. Deployment

### 8.1 Docker Compose Configuration

```yaml
services:
  postgres:
    image: postgres:15-alpine
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
    
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    
  neo4j:
    image: neo4j:5-community
    ports: ["7474:7474", "7687:7687"]
    volumes: [neo4j_data:/data]
    
  keycloak:
    image: quay.io/keycloak/keycloak:24.0.0
    ports: ["8081:8080"]
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
      
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    profiles: [dev]
    
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis, neo4j, keycloak]
    
  celery_worker:
    build: ./backend
    command: celery -A app.worker.celery_app worker
    depends_on: [redis]
```

### 8.2 Environment Configuration

```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost:5432/milimo
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=milimopassword
KC_SERVER_URL=http://localhost:8081/

# LLM Provider Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Quantum Cloud
IBM_QUANTUM_TOKEN=...
DWAVE_API_KEY=...
AWS_BRAKET_BUCKET=...
```

---

## 9. Autoresearch-MLX Integration

### 9.1 Overview

Autoresearch-MLX is the Apple Silicon-native autonomous research loop:

- **Location**: `/autoresearch-mlx/`
- **Technology**: MLX framework for unified memory inference
- **Purpose**: Self-improving ML training with automated hypothesis generation

### 9.2 Components

| Component | Purpose |
|-----------|---------|
| `train.py` | Main training loop with val_bpb optimization |
| `prepare.py` | Data preparation with segment tree packing |
| `vqe_train.py` | VQE ansatz discovery with Meyer-Wallach entanglement metric |
| `packer.py` | O(log N) best-fit document packing |
| `analysis_agent.py` | Self-improving dataloader optimization |

### 9.3 NemoClaw Integration

NemoClaw provides OS-level sandboxing for autonomous code execution:

```yaml
# Blueprint configuration
execution:
  timeout: 600s
  memory_limit: 32GB
  
network:
  mode: whitelist
  allowed_hosts:
    - huggingface.co
    - arxiv.org
    - localhost (PostgreSQL, Redis, Neo4j)
    
filesystem:
  read_write: [/sandbox, /tmp]
  read_only: [/System, /Library, /usr]
  blocked: [/.env, /.ssh, /.aws]
```

---

## 10. Current Implementation Status

### Fully Implemented
- ✅ Multi-agent orchestration (17 agents)
- ✅ SSE streaming chat
- ✅ Local LLM inference (MLX, Ollama)
- ✅ Cloud LLM integration
- ✅ Qiskit 2.x circuit execution with transpilation
- ✅ D-Wave simulated annealing
- ✅ Secure code sandbox (AST + NemoClaw OS-level)
- ✅ Knowledge graph (Neo4j/FalkorDB/Kuzu)
- ✅ Vector search (ChromaDB)
- ✅ Live data feeds
- ✅ Keycloak authentication
- ✅ Project workspace isolation
- ✅ VQE ansatz generation with Qiskit Aer
- ✅ Segment tree packing
- ✅ NemoClaw blueprint runner (plan → apply → status → cleanup)
- ✅ Celery async VQE tasks
- ✅ VQE frontend panel with convergence visualization
- ✅ CLOPS benchmarking metric
- ✅ Comprehensive test coverage (168 tests)
- ✅ Complete data model documentation

### Partially Implemented
- ⚠️ IBM Quantum cloud execution (routing exists, credentials needed)
- ⚠️ CUDA-Q integration (documented limitation - macOS ARM64 not supported)
- ⚠️ Amazon Braket/Azure Quantum (providers defined)

### Recent Fixes (March 2026)
- ✅ Workflow task status using AsyncResult
- ✅ Neo4j performance indexes (10 total)
- ✅ FalkorDB/Kuzu artifact indexing
- ✅ HPC MPI dynamic detection
- ✅ Extension tests (autoresearch, mqdd)
- ✅ Route coverage tests improved

### Architecture Gaps (from Audit)
1. **Sandbox Security**: OS-level via NemoClaw (implemented), roadmap: Firecracker for Linux
2. **Sync Engine**: Last-Write-Wins, need CRDT (ElectricSQL roadmap)
3. **VQE Evolution**: Working with Qiskit Aer, roadmap: Agentic RL for ansatz discovery
4. **Graph Queries**: Natural language, need strict Text2Cypher
5. **Error Mitigation**: Basic ZNE, need comprehensive calibration

---

## 11. Improvement Proposals Requested

AI analysis should propose improvements for:

### 11.1 Performance
- [ ] Optimize LLM inference pipeline latency
- [ ] Improve vector search indexing strategy
- [ ] Reduce Celery task overhead
- [ ] Implement request batching for graph queries

### 11.2 Security
- [ ] Add OS-level sandboxing (gVisor/Firecracker)
- [ ] Implement API request signing
- [ ] Add audit logging for quantum executions
- [ ] Enhance input sanitization

### 11.3 Architecture
- [ ] Implement CRDT-based sync for collaborative features
- [ ] Add GraphQL API layer for flexible queries
- [ ] Implement event sourcing for experiment tracking
- [ ] Add plugin hot-reloading

### 11.4 Features
- [ ] Real quantum hardware integration for VQE
- [ ] Self-evolving ansatz with reinforcement learning
- [ ] Multi-modal input (voice, diagrams)
- [ ] Collaborative workspaces with real-time sync
- [ ] Quantum circuit optimization pass manager

### 11.5 Operations
- [ ] Implement proper observability (OpenTelemetry)
- [ ] Add circuit breakers for external services
- [ ] Implement graceful degradation
- [ ] Add chaos engineering tests

---

## 12. File Structure Reference

```
milimoquantum/
├── backend/
│   ├── app/
│   │   ├── main.py                 # Application entry point
│   │   ├── auth.py                 # Keycloak authentication
│   │   ├── agents/                 # Agent implementations
│   │   │   ├── orchestrator.py     # Multi-agent router
│   │   │   ├── context_enricher.py # Live data injection
│   │   │   └── results_analyzer_agent.py
│   │   ├── routes/                 # API endpoints
│   │   │   ├── chat.py             # SSE streaming
│   │   │   ├── quantum.py          # Execution API
│   │   │   └── ...
│   │   ├── quantum/                # Quantum computing
│   │   │   ├── executor.py         # Backend abstraction
│   │   │   ├── sandbox.py          # Secure execution
│   │   │   └── hal.py              # Hardware abstraction
│   │   ├── extensions/             # Plugin modules
│   │   │   ├── mqdd/               # Drug discovery
│   │   │   └── autoresearch/       # Training loops
│   │   ├── graph/                  # Graph databases
│   │   │   ├── neo4j_client.py
│   │   │   └── vqe_graph_client.py
│   │   ├── data/                   # Data sources
│   │   │   └── hub.py              # Intelligence hub
│   │   ├── llm/                    # LLM providers
│   │   │   └── mlx_client.py
│   │   └── db/                     # Database models
│   ├── tests/                      # Test suite
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Main application
│   │   ├── hooks/
│   │   │   └── useChat.ts          # Chat state management
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── chat/
│   │   │   └── artifacts/
│   │   ├── extensions/
│   │   │   └── autoresearch/
│   │   └── services/
│   │       └── api.ts
│   └── package.json
│
├── autoresearch-mlx/               # Apple Silicon research
│   ├── train.py                    # Main training loop
│   ├── prepare.py                  # Data preparation
│   ├── autoresearch_mlx/
│   │   ├── vqe_train.py           # VQE optimization
│   │   ├── packer.py              # Segment tree packing
│   │   └── analysis_agent.py      # Self-improving dataloader
│   └── nemoclaw/
│       ├── blueprint.yaml         # Sandbox configuration
│       └── orchestrator/
│           └── runner.py          # NemoClaw integration
│
├── NemoClaw/                       # NVIDIA NemoClaw sandboxing
│   └── nemoclaw/                   # OpenShell plugin
│
├── docker-compose.yml
└── docs/
    ├── MILIMO_QUANTUM_SYSTEM.md    # This document
    ├── nemoclaw_autoresearch_integration_analysis.md
    └── implementation_plan_nemoclaw_autoresearch.md
```

---

## 13. Quick Start Commands

```bash
# Start infrastructure
docker-compose up -d postgres redis neo4j keycloak

# Backend (native for MLX)
source backend/milimoenv/bin/activate
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend (dev)
cd frontend && npm install && npm run dev

# Celery worker
celery -A app.worker.celery_app worker --loglevel=info

# Run tests
pytest backend/tests/ -v

# NemoClaw sandbox
nemoclaw my-assistant connect
```

---

## 14. Contact & Resources

- **Repository**: `/Users/mck/Desktop/milimoquantum`
- **Documentation**: `/docs/`
  - `MILIMO_QUANTUM_SYSTEM.md` - This document
  - `DATA_MODEL_STRUCTURE.md` - Complete data model reference
  - `ARCHITECTURE_DATA_FLOW.md` - Architecture diagrams
  - `AUDIT_REPORT.md` - Code quality audit
- **Configuration**: `.env` files in backend/frontend
- **Services Dashboard**:
  - Frontend: http://localhost:5173
  - Backend API: http://localhost:8000/docs
  - Keycloak: http://localhost:8081
  - Neo4j: http://localhost:7474

---

*Document generated for AI analysis. Last updated: March 31, 2026*
