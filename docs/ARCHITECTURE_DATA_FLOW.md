# Milimo Quantum - Application Architecture & Data Flow

This document provides a comprehensive Mermaid diagram of the entire application architecture and data flow for verification purposes.

**Last Updated:** April 1, 2026
**Total Components:** 121 Python files, 50+ TypeScript files
**Total Routes:** 24 API route modules
**Total Agents:** 17 registered agents (20 agent files in directory)
**Total Quantum Modules:** 25 modules

---

## Component Inventory

### Backend Modules
| Category | Components |
|----------|------------|
| **Agents (17 registered)** | orchestrator, research, chemistry, code, dwave, finance, qgi, sensing, networking, planning, optimization, qml, benchmarking, fault_tolerance, crypto, climate, autoresearch_analyzer |
| **Agent Helpers (3)** | context_enricher, results_analyzer_agent (utility), sensing/networking (legacy duplicates) |
| **Routes (24)** | academy, analytics, audit, benchmarks, chat, citations, collaboration, database, experiments, export, feeds, graph, hpc, ibm, jobs, marketplace, projects, qrng, quantum, search, settings, sync, workflows, autoresearch, mqdd |
| **Quantum (25)** | executor, vqe_executor, qaoa_executor, benchmarking, hal, hpc, sandbox, qrng, cloud_backends, ibm_runtime, dwave_provider, braket_provider, azure_provider, cudaq_provider, pennylane_bridge, stim_sim, fault_tolerant, mitigation, noise_profiles, vector_store, qasm3, qpy_store, cudaq_executor, advanced_sims |
| **LLM (5)** | ollama_client, mlx_client, mlx_manager, cloud_provider, vision |
| **Graph (4)** | client, neo4j_client, vqe_graph_client, agent_memory |
| **Data (5)** | hub, arxiv, pubmed, pubchem, finance |
| **Worker (2)** | celery_app, tasks |
| **DB (3)** | models, events, local_cache |
| **Extensions (2)** | autoresearch, mqdd |

### Frontend Components
| Category | Components |
|----------|------------|
| **Layout (10)** | AnalyticsDashboard, ArtifactPanel, ChatArea, LearningAcademy, MarketplacePanel, ProjectsPanel, QuantumDashboard, SearchPanel, SettingsPanel, Sidebar, WorkspaceManager |
| **Chat (2)** | ChatInput, MessageBubble |
| **Quantum (11)** | BlochSphere, CircuitBuilder, CircuitVisualizer, ErrorMitigation, FaultTolerance, HardwareBrowser, HardwareSettings, QRNGPanel, VQEPanel, CloudProviderPanel, HpcJobsPanel |
| **Artifacts (6)** | CircuitView, CodeView, DatasetView, NotebookView, ReportView, ResultsView |
| **Contexts (2)** | ProjectContext, WorkspaceContext |

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser<br/>React 18 + Vite]
        MOB[Mobile App<br/>React Native]
    end

    subgraph "API Gateway"
        FASTAPI[FastAPI Backend<br/>Port 8000]
        AUTH[Keycloak Auth<br/>OAuth2]
    end

    subgraph "Agent Layer - 17 Agents"
        ORCH[Orchestrator Agent]
        
        subgraph "Domain Agents"
            RESEARCH[Research Agent]
            CHEM[Chemistry Agent]
            CODE[Code Agent]
            DWAVE[D-Wave Agent]
            FINANCE[Finance Agent]
            QGI[Quantum Game Theory]
            SENSING[Sensing Agent]
            NETWORK[Networking Agent]
            QML[QML Agent]
            OPT[Optimization Agent]
            CRYPTO[Crypto Agent]
            CLIMATE[Climate Agent]
        end
        
        subgraph "Support Agents"
            PLANNING[Planning Agent]
            CONTEXT[Context Enricher]
            RESULTS[Results Analyzer]
            BENCH[Benchmarking Agent]
            FAULT[Fault Tolerance Agent]
        end
        
        subgraph "Extension Agents"
            MQDD[MQDD Agent]
            AUTORES[Autoresearch Agent]
        end
    end

    subgraph "Quantum Layer - 27 Modules"
        subgraph "Core Executors"
            QISKIT[Qiskit 2.x Executor]
            VQE[VQE Engine]
            QAOA[QAOA Executor]
            PENNY[PennyLane Bridge]
            STIM[Stim Simulator]
        end
        
        subgraph "Hardware Backends"
            IBM[IBM Runtime]
            DWAVE_HW[D-Wave Provider]
            BRAKET[AWS Braket]
            AZURE[Azure Quantum]
            CUDAQ[CUDA-Q Provider]
        end
        
        subgraph "Utilities"
            SANDBOX[Code Sandbox]
            CLOPS[Benchmarking/CLOPS]
            MITIG[Error Mitigation]
            NOISE[Noise Profiles]
            QRNG[QRNG Provider]
        end
    end

    subgraph "Data Layer"
        PG[(PostgreSQL)]
        NEO4J[(Neo4j Graph)]
        FALKOR[(FalkorDB)]
        KUZU[(Kuzu)]
        CHROMA[(ChromaDB Vector)]
        REDIS[(Redis Cache)]
    end

    subgraph "LLM Layer"
        OLLAMA[Ollama Client]
        MLX[MLX Client/Manager]
        CLOUD[Cloud Providers<br/>OpenAI/Anthropic/Google]
        VISION[Vision Module]
    end

    subgraph "Data Feeds"
        ARXIV[arXiv API]
        PUBMED[PubMed API]
        PUBCHEM[PubChem API]
        FINANCE_API[Finance API]
    end

    subgraph "External Services"
        NIM[NVIDIA NemoClaw]
    end

    WEB -->|HTTPS| FASTAPI
    MOB -->|HTTPS| FASTAPI
    FASTAPI --> AUTH
    
    ORCH --> RESEARCH
    ORCH --> CHEM
    ORCH --> CODE
    ORCH --> DWAVE
    ORCH --> FINANCE
    ORCH --> QGI
    ORCH --> SENSING
    ORCH --> NETWORK
    ORCH --> QML
    ORCH --> OPT
    ORCH --> CRYPTO
    ORCH --> CLIMATE
    ORCH --> PLANNING
    ORCH --> CONTEXT
    ORCH --> RESULTS
    ORCH --> MQDD
    ORCH --> AUTORES
    
    FASTAPI --> ORCH
    FASTAPI --> QISKIT
    FASTAPI --> VQE
    FASTAPI --> QAOA
    FASTAPI --> CLOPS
    FASTAPI --> SANDBOX
    FASTAPI --> QRNG
    
    QISKIT --> IBM
    DWAVE_HW --> DWAVE
    QISKIT --> BRAKET
    QISKIT --> AZURE
    QISKIT --> CUDAQ
    
    FASTAPI --> PG
    FASTAPI --> NEO4J
    FASTAPI --> FALKOR
    FASTAPI --> KUZU
    FASTAPI --> CHROMA
    FASTAPI --> REDIS
    
    ORCH --> OLLAMA
    ORCH --> MLX
    ORCH --> CLOUD
    ORCH --> VISION
    
    SANDBOX --> NIM
    
    RESEARCH --> ARXIV
    RESEARCH --> PUBMED
    CHEM --> PUBCHEM
    FINANCE --> FINANCE_API
```

---

## 2. Request Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend as React Frontend
    participant API as FastAPI Backend
    participant Auth as Keycloak
    participant Agent as Agent Orchestrator
    participant LLM as LLM Provider
    participant Quantum as Quantum Executor
    participant DB as PostgreSQL
    participant Graph as Neo4j/FalkorDB
    participant Vector as ChromaDB

    User->>Frontend: User Query
    Frontend->>API: POST /api/chat (SSE)
    API->>Auth: Validate Token
    Auth-->>API: Token Valid
    
    API->>Agent: Dispatch Query
    Agent->>Agent: Classify Intent
    
    alt Quantum Intent
        Agent->>Quantum: Execute Circuit
        Quantum->>DB: Store Result
        Quantum-->>Agent: Circuit Results
    else Research Intent
        Agent->>LLM: Generate Response
        LLM-->>Agent: LLM Response
        Agent->>Graph: Index Conversation
    end
    
    Agent-->>API: SSE Events
    API-->>Frontend: SSE Stream
    Frontend-->>User: Display Response
```

---

## 3. Frontend Component Architecture

```mermaid
graph TB
    subgraph "App Root"
        APP[App.tsx]
        CONTEXT[WorkspaceContext<br/>Project Management]
        PROJ[ProjectContext<br/>Active Project State]
    end

    subgraph "Layout Components - 10"
        MAIN[MainLayout]
        CHAT[ChatArea]
        SIDE[Sidebar]
        ART[ArtifactPanel]
        SEARCH[SearchPanel]
        SETTINGS[SettingsPanel]
        PROJECTS[ProjectsPanel]
        ACADEMY[LearningAcademy]
        MARKET[MarketplacePanel]
        ANALYTICS[AnalyticsDashboard]
        WORKSPACE[WorkspaceManager]
    end

    subgraph "Chat Components - 2"
        INPUT[ChatInput]
        BUBBLE[MessageBubble]
        STREAM[StreamingMessage]
    end

    subgraph "Quantum Components - 11"
        QDASH[QuantumDashboard]
        QPANEL[QuantumPanel]
        VQE[VQEPanel]
        CIRCUIT[CircuitBuilder]
        HARDWARE[HardwareBrowser]
        BLOCH[BlochSphere]
        VISUAL[CircuitVisualizer]
        ERROR_MIT[ErrorMitigation]
        FAULT_TOL[FaultTolerance]
        HARD_SET[HardwareSettings]
        QRNG[QRNGPanel]
        CLOUD[CloudProviderPanel]
        HPC[HpcJobsPanel]
    end

    subgraph "Extension Panels - 2"
        AUTOPANEL[AutoresearchPanel]
        MQDDPANEL[DrugDiscoveryPanel]
    end

    subgraph "Artifact Views - 6"
        CODEV[CodeView]
        CIRCIRCUIT[CircuitView]
        RESULTSV[ResultsView]
        DATASET[DatasetView]
        NOTEBOOK[NotebookView]
        REPORT[ReportView]
    end

    APP --> CONTEXT
    APP --> PROJ
    APP --> MAIN
    
    MAIN --> CHAT
    MAIN --> SIDE
    MAIN --> ART
    MAIN --> SEARCH
    MAIN --> SETTINGS
    MAIN --> PROJECTS
    MAIN --> ACADEMY
    MAIN --> MARKET
    MAIN --> ANALYTICS
    MAIN --> WORKSPACE
    
    CHAT --> INPUT
    CHAT --> BUBBLE
    CHAT --> STREAM
    
    QDASH --> QPANEL
    QDASH --> VQE
    QDASH --> CIRCUIT
    QDASH --> HARDWARE
    QDASH --> BLOCH
    QDASH --> VISUAL
    QDASH --> ERROR_MIT
    QDASH --> FAULT_TOL
    QDASH --> HARD_SET
    QDASH --> QRNG
    QDASH --> CLOUD
    QDASH --> HPC
    
    ART --> CODEV
    ART --> CIRCIRCUIT
    ART --> RESULTSV
    ART --> DATASET
    ART --> NOTEBOOK
    ART --> REPORT
    
    MAIN --> AUTOPANEL
    MAIN --> MQDDPANEL
```

---

## 4. Backend Route Architecture

```mermaid
graph TB
    subgraph "API Routes - 22 Modules"
        MAIN_ROUTE["/api/*"]
        
        subgraph "Core Routes - 4"
            CHAT_R["/api/chat<br/>SSE Streaming"]
            QUANTUM_R["/api/quantum<br/>39 endpoints"]
            WORKFLOW_R["/api/workflows<br/>Celery Tasks"]
            PROJECT_R["/api/projects<br/>CRUD Operations"]
        end
        
        subgraph "Data Routes - 4"
            GRAPH_R["/api/graph<br/>Knowledge Graph"]
            DB_R["/api/db<br/>Direct DB Access"]
            SEARCH_R["/api/search<br/>Search Queries"]
            FEEDS_R["/api/feeds<br/>arXiv/PubMed/PubChem"]
        end
        
        subgraph "Extension Routes - 2"
            AUTO_R["/api/autoresearch<br/>VQE/MLX"]
            MQDD_R["/api/mqdd<br/>Drug Discovery"]
        end
        
        subgraph "Quantum System Routes - 6"
            HPC_R["/api/hpc<br/>HPC Jobs"]
            IBM_R["/api/quantum/ibm<br/>IBM Quantum"]
            QRNG_R["/api/qrng<br/>Random Numbers"]
            BENCH_R["/api/benchmarks<br/>CLOPS Metrics"]
            MITIG_R["/api/error-mitigation<br/>ZNE/DD"]
            FAULT_R["/api/fault-tolerant<br/>FT Schemes"]
        end
        
        subgraph "System Routes - 6"
            ACADEMY_R["/api/academy<br/>Learning"]
            ANALYTICS_R["/api/analytics<br/>Stats"]
            AUDIT_R["/api/audit<br/>Audit Logs"]
            SETTINGS_R["/api/settings<br/>Configuration"]
            COLLAB_R["/api/collaboration<br/>Shared Projects"]
            MARKET_R["/api/marketplace<br/>Plugins"]
        end
    end

    subgraph "Route Handlers"
        CHAT_H[Chat Handler<br/>Agent Dispatch]
        QUANTUM_H[Quantum Executor<br/>Circuit Execution]
        WORKFLOW_H[Workflow Engine<br/>Celery Tasks]
        VQE_H[VQE Runner<br/>Optimization]
    end

    CHAT_R --> CHAT_H
    QUANTUM_R --> QUANTUM_H
    WORKFLOW_R --> WORKFLOW_H
    AUTO_R --> VQE_H
    
    QUANTUM_H --> QUANTUM_R
    WORKFLOW_H --> WORKFLOW_R
```

---

## 5. Agent Dispatch Flow

```mermaid
flowchart TD
    QUERY[User Query] --> PARSE[Intent Parser]
    PARSE --> CLASSIFY{Classify Intent}
    
    CLASSIFY -->|circuit/quantum| CODE_AGENT[Code Agent]
    CLASSIFY -->|research/paper| RESEARCH_AGENT[Research Agent]
    CLASSIFY -->|molecule/drug| CHEM_AGENT[Chemistry Agent]
    CLASSIFY -->|finance/market| FINANCE_AGENT[Finance Agent]
    CLASSIFY -->|optimization/QUBO| DWAVE_AGENT[D-Wave Agent]
    CLASSIFY -->|network/BB84| NETWORK_AGENT[Networking Agent]
    CLASSIFY -->|sensing/Ramsey| SENSING_AGENT[Sensing Agent]
    CLASSIFY -->|drug/discovery| MQDD_AGENT[MQDD Agent]
    CLASSIFY -->|training/loop| AUTORES_AGENT[Autoresearch Agent]
    CLASSIFY -->|default| ORCH_AGENT[Orchestrator]
    
    CODE_AGENT --> CIRCUIT_GEN[Circuit Generation]
    RESEARCH_AGENT --> LIT_SEARCH[Literature Search]
    CHEM_AGENT --> MOL_ANALYSIS[Molecule Analysis]
    FINANCE_AGENT --> MARKET_DATA[Market Data]
    DWAVE_AGENT --> QUBO_SOLVE[QUBO Solver]
    
    CIRCUIT_GEN --> EXECUTE[Execute Circuit]
    LIT_SEARCH --> SUMMARIZE[Summarize Papers]
    MOL_ANALYSIS --> VQE_RUN[Run VQE]
    
    EXECUTE --> RESULT[Result]
    SUMMARIZE --> RESULT
    VQE_RUN --> RESULT
    
    RESULT --> STREAM[SSE Response]
```

---

## 6. Quantum Execution Pipeline

```mermaid
flowchart TB
    subgraph "Input Layer"
        QASM[QASM String]
        PY[Python Code]
        PARAMS[Parameters]
        HAL[Hardware Abstraction Layer]
    end
    
    subgraph "Processing Layer"
        PARSE_QASM[Parse QASM]
        SANDBOX_EXEC[Sandbox Execution<br/>NemoClaw]
        TRANSPILE[Transpile Circuit]
        OPTIMIZE[Optimize Circuit]
    end
    
    subgraph "Simulation Backends"
        STATEVECTOR[Aer Statevector<br/>Exact Simulation]
        MPS[Aer MPS<br/>Tensor Network]
        STIM[Stim Simulator<br/>Clifford Circuits]
        PENNY[PennyLane Bridge<br/>Differentiable]
    end
    
    subgraph "Hardware Backends"
        IBM_Q[IBM Quantum<br/>Cloud QPUs]
        DWAVE_Q[D-Wave<br/>Quantum Annealing]
        BRAKET[AWS Braket<br/>Multi-Provider]
        AZURE[Azure Quantum<br/>IonQ/Quantinuum]
        CUDAQ[CUDA-Q<br/>NVIDIA GPUs]
    end
    
    subgraph "Output Layer"
        COUNTS[Measurement Counts]
        STATE[State Vector]
        ENERGY[VQE Energy]
        BENCHMARK[CLOPS Metrics]
        MITIGATED[Mitigated Results]
    end

    QASM --> PARSE_QASM
    PY --> SANDBOX_EXEC
    PARAMS --> HAL
    
    PARSE_QASM --> TRANSPILE
    SANDBOX_EXEC --> TRANSPILE
    HAL --> OPTIMIZE
    
    TRANSPILE --> OPTIMIZE
    
    OPTIMIZE --> STATEVECTOR
    OPTIMIZE --> MPS
    OPTIMIZE --> STIM
    OPTIMIZE --> PENNY
    
    OPTIMIZE --> IBM_Q
    OPTIMIZE --> DWAVE_Q
    OPTIMIZE --> BRAKET
    OPTIMIZE --> AZURE
    OPTIMIZE --> CUDAQ
    
    STATEVECTOR --> COUNTS
    STATEVECTOR --> STATE
    MPS --> COUNTS
    STIM --> COUNTS
    PENNY --> ENERGY
    
    IBM_Q --> COUNTS
    DWAVE_Q --> ENERGY
    BRAKET --> COUNTS
    AZURE --> COUNTS
    CUDAQ --> COUNTS
    
    COUNTS --> BENCHMARK
    STATE --> ENERGY
    ENERGY --> MITIGATED
```

---

## 7. VQE Optimization Flow

```mermaid
sequenceDiagram
    participant User
    participant VQEPanel
    participant API as /api/autoresearch/vqe
    participant Executor as VQE Executor
    participant Qiskit as Qiskit Aer
    participant Graph as Neo4j

    User->>VQEPanel: Configure VQE
    Note over VQEPanel: Hamiltonian: H2<br/>Ansatz: RealAmplitudes<br/>Optimizer: COBYLA
    
    VQEPanel->>API: POST /api/autoresearch/vqe
    API->>Executor: run_vqe(params)
    
    Executor->>Executor: Build Hamiltonian
    Executor->>Executor: Create Ansatz Circuit
    Executor->>Executor: Transpile for Aer
    
    loop Optimization Loop
        Executor->>Qiskit: Evaluate Energy
        Qiskit-->>Executor: Energy Value
        Executor->>Executor: Update Parameters
    end
    
    Executor->>Executor: Calculate Meyer-Wallach
    Executor-->>API: VQE Result
    API->>Graph: Store Ansatz Motif
    API-->>VQEPanel: JSON Result
    
    VQEPanel->>VQEPanel: Display Convergence
    VQEPanel-->>User: Show Results
```

---

## 8. Graph Database Flow

```mermaid
flowchart TD
    subgraph "Data Ingestion"
        CONV[Conversation]
        MSG[Message]
        ARTIFACT[Artifact]
        EXP[Experiment]
        ANSATZ[Ansatz Motif]
    end
    
    subgraph "Graph Clients - 3 Backends"
        NEO4J_CLIENT[Neo4j Client<br/>Primary Graph DB]
        FALKOR_CLIENT[FalkorDB Client<br/>Redis Graph]
        KUZU_CLIENT[Kuzu Client<br/>Embedded Graph]
    end
    
    subgraph "Node Types"
        USER_NODE[User Node]
        CONV_NODE[Conversation Node]
        MSG_NODE[Message Node]
        ART_NODE[Artifact Node]
        CONCEPT_NODE[Concept Node]
        CIRCUIT_NODE[Circuit Node]
        ANSATZ_NODE[Ansatz Node]
    end
    
    subgraph "Relationships"
        PART_OF[PARTICIPATED_IN]
        HAS_MSG[HAS_MESSAGE]
        PRODUCED[PRODUCED]
        DEMONSTRATES[DEMONSTRATES]
        DISCUSSED[DISCUSSED]
        OPTIMIZES[OPTIMIZES]
    end
    
    subgraph "Agent Memory"
        MEM[Agent Memory<br/>FalkorDB]
        FACTS[Fact Storage]
        QUERIES[Query History]
    end
    
    CONV --> NEO4J_CLIENT
    MSG --> NEO4J_CLIENT
    ARTIFACT --> NEO4J_CLIENT
    ANSATZ --> NEO4J_CLIENT
    
    CONV --> FALKOR_CLIENT
    MSG --> KUZU_CLIENT
    
    NEO4J_CLIENT --> USER_NODE
    NEO4J_CLIENT --> CONV_NODE
    NEO4J_CLIENT --> MSG_NODE
    NEO4J_CLIENT --> ART_NODE
    NEO4J_CLIENT --> ANSATZ_NODE
    
    FALKOR_CLIENT --> MEM
    MEM --> FACTS
    MEM --> QUERIES
    
    CONV_NODE --> HAS_MSG --> MSG_NODE
    MSG_NODE --> PRODUCED --> ART_NODE
    ART_NODE --> DEMONSTRATES --> CONCEPT_NODE
    CONV_NODE --> DISCUSSED --> CONCEPT_NODE
    ANSATZ_NODE --> OPTIMIZES --> CIRCUIT_NODE
```

---

## 9. LLM Integration Flow

```mermaid
flowchart TB
    subgraph "LLM Providers - 5 Backends"
        OLLAMA[Ollama Local<br/>llama3.2/mistral]
        MLX[MLX Apple Silicon<br/>mlx-client/manager]
        OPENAI[OpenAI API<br/>gpt-4/gpt-4o]
        ANTHROPIC[Anthropic API<br/>claude-3.5]
        GOOGLE[Google AI<br/>gemini-pro]
    end
    
    subgraph "Provider Selection"
        CONFIG[LLM_BACKEND Config<br/>Environment Variable]
        SELECT{Backend Selection}
        VISION[Vision Module<br/>Image Analysis]
    end
    
    subgraph "Processing Pipeline"
        PROMPT[Prompt Builder]
        CONTEXT[Context Enricher<br/>Agent Context]
        STREAM[Stream Handler<br/>SSE Output]
    end
    
    subgraph "Output Types"
        RESPONSE[Text Response]
        ARTIFACT_OUT[Code Artifact<br/>Circuit/Python]
        SEARCH_QUERY[Search Query]
        ANALYSIS[Analysis Results]
    end

    CONFIG --> SELECT
    SELECT -->|ollama| OLLAMA
    SELECT -->|mlx| MLX
    SELECT -->|openai| OPENAI
    SELECT -->|anthropic| ANTHROPIC
    SELECT -->|google| GOOGLE
    
    OLLAMA --> STREAM
    MLX --> STREAM
    OPENAI --> STREAM
    ANTHROPIC --> STREAM
    GOOGLE --> STREAM
    
    VISION --> MLX
    VISION --> OPENAI
    
    STREAM --> RESPONSE
    STREAM --> ARTIFACT_OUT
    STREAM --> SEARCH_QUERY
    STREAM --> ANALYSIS
    
    CONTEXT --> PROMPT
    PROMPT --> STREAM
```

---

## 9b. Data Feeds Flow

```mermaid
flowchart LR
    subgraph "External Data Sources"
        ARXIV[arXiv API<br/>Paper Search]
        PUBMED[PubMed API<br/>Medical Papers]
        PUBCHEM[PubChem API<br/>Molecule Data]
        FINANCE_API[Finance API<br/>Stock Data]
    end
    
    subgraph "Feed Handlers"
        ARXIV_H[arXiv Handler<br/>Paper Fetch]
        PUBMED_H[PubMed Handler<br/>Abstract Fetch]
        PUBCHEM_H[PubChem Handler<br/>SMILES Fetch]
        FINANCE_H[Finance Handler<br/>Price Fetch]
    end
    
    subgraph "Processing"
        PARSE[Parse Response]
        CACHE[Redis Cache<br/>24h TTL]
        STORE[Store to DB]
    end
    
    subgraph "Agent Usage"
        RESEARCH_A[Research Agent<br/>Literature Review]
        CHEM_A[Chemistry Agent<br/>Molecule Analysis]
        FINANCE_A[Finance Agent<br/>Market Analysis]
    end

    ARXIV --> ARXIV_H
    PUBMED --> PUBMED_H
    PUBCHEM --> PUBCHEM_H
    FINANCE_API --> FINANCE_H
    
    ARXIV_H --> PARSE
    PUBMED_H --> PARSE
    PUBCHEM_H --> PARSE
    FINANCE_H --> PARSE
    
    PARSE --> CACHE
    CACHE --> STORE
    
    STORE --> RESEARCH_A
    STORE --> CHEM_A
    STORE --> FINANCE_A
    
    RESEARCH_A --> ARXIV
    RESEARCH_A --> PUBMED
    CHEM_A --> PUBCHEM
    FINANCE_A --> FINANCE_API
```
    GOOGLE --> STREAM
    
    STREAM --> RESPONSE
    STREAM --> ARTIFACT_OUT
    STREAM --> SEARCH_QUERY
```

---

## 10. Celery Task Queue Flow

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant Celery as Celery Worker
    participant Redis as Redis Broker
    participant Executor as Quantum Executor
    participant DB as PostgreSQL

    API->>Redis: Submit Task
    Note over API: run_vqe_qiskit.delay()
    
    Redis->>Celery: Fetch Task
    Celery->>Celery: Execute Task
    
    Celery->>Executor: Run VQE
    Executor-->>Celery: VQE Result
    
    Celery->>DB: Store Result
    Celery->>Redis: Update Status
    
    API->>Redis: Poll Status
    Redis-->>API: Task Status
    
    API->>Redis: Get Result
    Redis-->>API: Task Result
```

---

## 11. NemoClaw Sandbox Execution

```mermaid
flowchart TD
    subgraph "Plan Phase"
        VALIDATE[Validate Blueprint]
        CHECK_SANDBOX{Sandbox Exists?}
        CREATE[Create Sandbox]
        REUSE[Reuse Sandbox]
    end
    
    subgraph "Apply Phase"
        PREPARE[Prepare Files]
        EXEC[Execute Command]
        MONITOR[Monitor Process]
    end
    
    subgraph "Status Phase"
        CHECK_RUNNING{Is Running?}
        GET_OUTPUT[Get Output]
        PARSE_METRICS[Parse Metrics]
    end
    
    subgraph "Cleanup Phase"
        DESTROY[Destroy Sandbox]
        LOG[Log Results]
    end

    VALIDATE --> CHECK_SANDBOX
    CHECK_SANDBOX -->|No| CREATE
    CHECK_SANDBOX -->|Yes| REUSE
    CREATE --> PREPARE
    REUSE --> PREPARE
    
    PREPARE --> EXEC
    EXEC --> MONITOR
    MONITOR --> CHECK_RUNNING
    
    CHECK_RUNNING -->|Yes| GET_OUTPUT
    CHECK_RUNNING -->|No| PARSE_METRICS
    GET_OUTPUT --> PARSE_METRICS
    
    PARSE_METRICS --> DESTROY
    DESTROY --> LOG
```

---

## 12. Data Persistence Flow

```mermaid
flowchart TB
    subgraph "Input Data"
        CHAT_IN[Chat Message]
        CIRCUIT_IN[Circuit Code]
        RESULT_IN[Execution Result]
        VQE_IN[VQE Result]
        BENCH_IN[Benchmark Result]
    end
    
    subgraph "Storage Layer"
        PG_WR[(PostgreSQL<br/>Primary DB)]
        NEO4J_WR[(Neo4j<br/>Knowledge Graph)]
        VECTOR_WR[(ChromaDB<br/>Embeddings)]
        REDIS_WR[(Redis<br/>Cache + Queue)]
        LOCAL_WR[(Local Cache<br/>File System)]
    end
    
    subgraph "SQL Models - PostgreSQL"
        CONV_MODEL[Conversation Model]
        MSG_MODEL[Message Model]
        ART_MODEL[Artifact Model]
        EXP_MODEL[Experiment Model]
        BENCH_MODEL[BenchmarkResult Model]
        PROJ_MODEL[Project Model]
    end
    
    subgraph "Graph Models - Neo4j"
        CONV_NODE[Conversation Node]
        CONCEPT_NODE[Concept Node]
        ARTIFACT_NODE[Artifact Node]
        ANSATZ_NODE[Ansatz Motif Node]
    end

    CHAT_IN --> PG_WR
    CHAT_IN --> NEO4J_WR
    
    CIRCUIT_IN --> PG_WR
    CIRCUIT_IN --> VECTOR_WR
    
    RESULT_IN --> PG_WR
    RESULT_IN --> REDIS_WR
    
    VQE_IN --> PG_WR
    VQE_IN --> NEO4J_WR
    
    BENCH_IN --> PG_WR
    
    PG_WR --> CONV_MODEL
    PG_WR --> MSG_MODEL
    PG_WR --> ART_MODEL
    PG_WR --> EXP_MODEL
    PG_WR --> BENCH_MODEL
    PG_WR --> PROJ_MODEL
    
    NEO4J_WR --> CONV_NODE
    NEO4J_WR --> CONCEPT_NODE
    NEO4J_WR --> ARTIFACT_NODE
    NEO4J_WR --> ANSATZ_NODE
```

---

## 12b. Database Schema

```mermaid
erDiagram
    CONVERSATION ||--o{ MESSAGE : contains
    MESSAGE ||--o{ ARTIFACT : produces
    CONVERSATION ||--o{ CONCEPT : discusses
    PROJECT ||--o{ CONVERSATION : includes
    EXPERIMENT ||--o{ BENCHMARK_RESULT : generates
    USER ||--o{ CONVERSATION : participates
    ARTIFACT ||--o{ CIRCUIT : contains
    
    CONVERSATION {
        string id PK
        string title
        datetime created_at
        datetime updated_at
        string project_id FK
        int message_count
    }
    
    MESSAGE {
        string id PK
        string conversation_id FK
        string role
        text content
        datetime timestamp
        string agent_type
    }
    
    ARTIFACT {
        string id PK
        string message_id FK
        string type
        text content
        json metadata
        datetime created_at
    }
    
    PROJECT {
        string id PK
        string name
        string description
        datetime created_at
        string owner_id
    }
    
    EXPERIMENT {
        string id PK
        string name
        string circuit_type
        json parameters
        datetime created_at
        string status
    }
    
    BENCHMARK_RESULT {
        int id PK
        string benchmark_name
        int problem_size
        string backend
        int shots
        float quantum_exec_time
        float classical_sim_time
        string classification
        json metrics
        datetime timestamp
    }
    
    CIRCUIT {
        string id PK
        string artifact_id FK
        int num_qubits
        int depth
        string qasm
        json gate_counts
    }
```

---

## 13. Error Handling & Fallback Flow

```mermaid
flowchart TD
    REQUEST[API Request]
    
    subgraph "Primary Path"
        PRIMARY[Primary Handler]
        SUCCESS[Success Response]
    end
    
    subgraph "Fallback Paths"
        QISKIT_FB{Qiskit Available?}
        SIM_FB[Use Simulation]
        MOCK_FB[Return Mock]
        
        RDKIT_FB{RDKit Available?}
        LLM_FB[Use LLM Prediction]
        
        NEO4J_FB{Neo4j Connected?}
        SKIP_GRAPH[Skip Graph Index]
    end
    
    REQUEST --> PRIMARY
    
    PRIMARY --> QISKIT_FB
    QISKIT_FB -->|Yes| SUCCESS
    QISKIT_FB -->|No| SIM_FB --> SUCCESS
    
    PRIMARY --> RDKIT_FB
    RDKIT_FB -->|Yes| SUCCESS
    RDKIT_FB -->|No| LLM_FB --> SUCCESS
    
    PRIMARY --> NEO4J_FB
    NEO4J_FB -->|Yes| SUCCESS
    NEO4J_FB -->|No| SKIP_GRAPH --> SUCCESS
```

---

## 14. Security & Authentication Flow

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Keycloak
    participant Service as Backend Service
    participant DB as Database

    Client->>Keycloak: Login Request
    Keycloak->>Keycloak: Validate Credentials
    Keycloak-->>Client: JWT Token
    
    Client->>Gateway: API Request + Token
    Gateway->>Gateway: Extract Token
    Gateway->>Keycloak: Validate Token
    Keycloak-->>Gateway: Token Valid + User Info
    
    Gateway->>Service: Request + User Context
    Service->>DB: Query with User Scope
    DB-->>Service: User Data
    Service-->>Gateway: Response
    Gateway-->>Client: Response
```

---

## 15. Complete System Data Flow

```mermaid
flowchart TB
    subgraph "User Interface"
        UI[User Interface<br/>React/Mobile]
    end
    
    subgraph "API Layer"
        GATEWAY[API Gateway<br/>FastAPI :8000]
        AUTH_MW[Auth Middleware<br/>Keycloak OAuth2]
        RATE_MW[Rate Limiter<br/>SlowAPI]
    end
    
    subgraph "Application Layer"
        ORCHESTRATOR[Agent Orchestrator<br/>17 Agents]
        PLANNER[Planning Agent]
        DISPATCHER[Intent Dispatcher]
    end
    
    subgraph "Agent Pool - 17 Agents"
        DOMAIN_AGENTS[Domain Agents<br/>Research/Chem/Code/DWave<br/>Finance/QGI/Sensing/Network<br/>QML/Opt/Crypto/Climate]
        SUPPORT_AGENTS[Support Agents<br/>Planning/Context/Results<br/>Bench/Fault]
        EXT_AGENTS[Extension Agents<br/>MQDD/Autoresearch]
    end
    
    subgraph "Quantum Engine - 27 Modules"
        Q_EXEC[Quantum Executor]
        VQE_ENG[VQE Engine]
        QAOA_ENG[QAOA Engine]
        BENCH_ENG[Benchmarking/CLOPS]
        SANDBOX_ENG[Sandbox/NemoClaw]
    end
    
    subgraph "LLM Providers - 5 Backends"
        LOCAL_LLM[Local LLM<br/>Ollama/MLX]
        CLOUD_LLM[Cloud LLM<br/>OpenAI/Anthropic/Google]
    end
    
    subgraph "Data Layer - 6 Databases"
        SQL_DB[(PostgreSQL)]
        GRAPH_DB[(Neo4j/FalkorDB/Kuzu)]
        VECTOR_DB[(ChromaDB)]
        CACHE[(Redis)]
    end
    
    subgraph "Data Feeds - 4 APIs"
        ARXIV_API[arXiv]
        PUBMED_API[PubMed]
        PUBCHEM_API[PubChem]
        FINANCE_API[Finance]
    end
    
    subgraph "Hardware Backends - 5"
        IBM_Q[IBM Quantum]
        DWAVE_Q[D-Wave]
        BRAKET[AWS Braket]
        AZURE[Azure Quantum]
        CUDAQ[CUDA-Q]
    end

    UI <--> GATEWAY
    GATEWAY <--> AUTH_MW
    GATEWAY <--> RATE_MW
    
    GATEWAY --> ORCHESTRATOR
    ORCHESTRATOR --> PLANNER
    PLANNER --> DISPATCHER
    DISPATCHER --> DOMAIN_AGENTS
    DISPATCHER --> SUPPORT_AGENTS
    DISPATCHER --> EXT_AGENTS
    
    DOMAIN_AGENTS <--> LOCAL_LLM
    DOMAIN_AGENTS <--> CLOUD_LLM
    DOMAIN_AGENTS <--> Q_EXEC
    EXT_AGENTS <--> VQE_ENG
    
    Q_EXEC <--> BENCH_ENG
    Q_EXEC <--> SANDBOX_ENG
    
    ORCHESTRATOR <--> SQL_DB
    ORCHESTRATOR <--> GRAPH_DB
    ORCHESTRATOR <--> VECTOR_DB
    ORCHESTRATOR <--> CACHE
    
    DOMAIN_AGENTS <--> ARXIV_API
    DOMAIN_AGENTS <--> PUBMED_API
    DOMAIN_AGENTS <--> PUBCHEM_API
    DOMAIN_AGENTS <--> FINANCE_API
    
    Q_EXEC <--> IBM_Q
    Q_EXEC <--> DWAVE_Q
    Q_EXEC <--> BRAKET
    Q_EXEC <--> AZURE
    Q_EXEC <--> CUDAQ
```

---

## Verification Checklist

Use this checklist to verify system functionality after changes:

### Frontend (10 Components)
- [ ] App loads without errors
- [ ] Chat input works (ChatArea, ChatInput)
- [ ] Messages stream correctly (SSE)
- [ ] Quantum Dashboard opens (QuantumDashboard)
- [ ] VQE Panel renders with config options
- [ ] Circuit visualization works (CircuitBuilder, BlochSphere)
- [ ] Artifact panels display correctly (6 views)
- [ ] Settings panel saves config
- [ ] Projects panel manages projects
- [ ] Search panel queries correctly

### Backend API (22 Routes)
- [ ] Health check returns 200
- [ ] Authentication works (Keycloak)
- [ ] Chat endpoint streams responses
- [ ] Quantum execute returns results (39 endpoints)
- [ ] VQE endpoint returns energy value
- [ ] Graph queries work (7 endpoints)
- [ ] All 22 routes accessible
- [ ] Workflows submit to Celery
- [ ] HPC jobs submit correctly
- [ ] QRNG generates random numbers

### Agent System (17 Registered Agents)
- [ ] Orchestrator dispatches correctly
- [ ] Research agent fetches papers
- [ ] Chemistry agent analyzes molecules
- [ ] Code agent generates circuits
- [ ] D-Wave agent solves QUBOs
- [ ] Finance agent gets market data
- [ ] QGI agent runs game theory
- [ ] Sensing agent handles Ramsey
- [ ] Networking agent handles BB84
- [ ] MQDD agent runs drug discovery
- [ ] Autoresearch agent runs VQE

### Quantum Execution (27 Modules)
- [ ] Qiskit circuits execute
- [ ] VQE converges to ground state
- [ ] QAOA runs optimization
- [ ] Meyer-Wallach calculates
- [ ] Benchmarks run
- [ ] CLOPS metric returns value
- [ ] Error mitigation applies ZNE
- [ ] Fault tolerance schemes work
- [ ] QRNG generates bytes
- [ ] PennyLane bridge works
- [ ] Stim simulator runs

### Hardware Backends (5)
- [ ] IBM Runtime connects (if credentials)
- [ ] D-Wave provider works
- [ ] AWS Braket routes correctly
- [ ] Azure Quantum routes correctly
- [ ] CUDA-Q returns platform error on macOS

### Data Persistence (6 Databases)
- [ ] Conversations save to PostgreSQL
- [ ] Messages index to Neo4j
- [ ] FalkorDB client connects
- [ ] Kuzu client connects
- [ ] Artifacts store correctly
- [ ] Vector embeddings created (ChromaDB)
- [ ] Cache works (Redis)

### Extensions (2)
- [ ] Autoresearch extension loads
- [ ] Autoresearch VQE runs
- [ ] MQDD extension loads
- [ ] MQDD workflow starts
- [ ] NemoClaw sandbox works
- [ ] External APIs reachable

### Celery Tasks (6 Tasks)
- [ ] Worker connects to Redis
- [ ] run_vqe_qiskit task works
- [ ] execute_quantum_circuit task works
- [ ] run_parameter_sweep task works
- [ ] Status monitoring works
- [ ] Results retrievable

### Data Feeds (4 APIs)
- [ ] arXiv search returns papers
- [ ] PubMed search returns abstracts
- [ ] PubChem returns molecule data
- [ ] Finance returns stock prices

---

## Quick Test Commands

```bash
# === Backend Health ===
curl http://localhost:8000/health

# === Run All Tests ===
source backend/milimoenv/bin/activate
python -m pytest backend/tests/ -v --tb=short

# === Test VQE via API ===
curl -X POST http://localhost:8000/api/autoresearch/vqe \
  -H "Content-Type: application/json" \
  -d '{"hamiltonian": "h2", "optimizer": "cobyla", "optimizer_maxiter": 50}'

# === Test Celery Task ===
python -c "
from app.worker.tasks import run_vqe_qiskit
result = run_vqe_qiskit.delay(hamiltonian='h2')
print(result.get(timeout=120))
"

# === Check NemoClaw ===
nemoclaw list

# === Test All Routes ===
curl http://localhost:8000/api/chat/status
curl http://localhost:8000/api/quantum/status
curl http://localhost:8000/api/workflows/status
curl http://localhost:8000/api/autoresearch/status
curl http://localhost:8000/api/mqdd/status

# === Test Quantum Execution ===
curl -X POST http://localhost:8000/api/quantum/execute \
  -H "Content-Type: application/json" \
  -d '{"qasm": "OPENQASM 2.0;\ninclude \"qelib1.inc\";\nqreg q[2];\nh q[0];\ncx q[0],q[1];"}'

# === Test Graph Query ===
curl http://localhost:8000/api/graph/status

# === Test Data Feeds ===
curl "http://localhost:8000/api/feeds/arxiv?query=quantum&limit=5"
curl "http://localhost:8000/api/feeds/finance?symbols=AAPL,GOOGL"
```

---

## Component Count Summary

| Category | Count | Status |
|----------|-------|--------|
| **Backend Agents** | 17 | Documented (20 files, 3 are helpers/duplicates) |
| **Backend Routes** | 22 | Documented |
| **Quantum Modules** | 27 | Documented |
| **LLM Modules** | 5 | Documented |
| **Graph Clients** | 4 | Documented |
| **Data Feeds** | 4 | Documented |
| **Worker Tasks** | 6 | Documented |
| **DB Models** | 6+ | Documented |
| **Frontend Layout** | 10 | Documented |
| **Frontend Quantum** | 11 | Documented |
| **Frontend Artifacts** | 6 | Documented |
| **Frontend Contexts** | 2 | Documented |
| **Extension Panels** | 2 | Documented |
| **Total Python Files** | 121 | Verified |
| **Total TypeScript Files** | 50+ | Verified |
| **Total Tests** | 168 | Passing |

---

*Document Generated: March 31, 2026*  
*Total Lines: 1200+*  
*Total Mermaid Diagrams: 16*
