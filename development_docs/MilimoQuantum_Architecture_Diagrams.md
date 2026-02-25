# Milimo Quantum — Architecture Diagrams & Data Models

> Full-stack reference document | February 2026 | Blueprint v1.0 + Graph DB Addendum + Missing Dimensions

---

## 1. Platform Layer Map (High-Level)

```mermaid
graph TB
    subgraph L1["Layer 1 · Presentation"]
        UI["React 18 + TypeScript\nChat Interface"]
        AP["Artifact Panel\nMonaco / Plotly / D3"]
        LA["Learning Academy\nBloch Sphere · Challenges"]
        MH["Marketplace Hub\nAlgorithm Store"]
    end

    subgraph L2["Layer 2 · Agent Orchestration (14 Agents)"]
        OA["Orchestrator Agent\nIntent Routing"]
        PA["Planning Agent\nMulti-step pipelines"]
        
        subgraph AGENTS["Domain Agents"]
            A1["Research"]
            A2["Chemistry\nDrug Discovery"]
            A3["Finance"]
            A4["Crypto / QKD"]
            A5["QML"]
            A6["Optimization"]
            A7["Climate / Science"]
            A8["Code"]
            A9["QGI — Graph Intel"]
            A10["Sensing"]
            A11["Networking"]
            A12["D-Wave Annealing"]
        end
    end

    subgraph L3["Layer 3 · Quantum Execution Engine"]
        QK["Qiskit SDK v2.2"]
        AER["Qiskit Aer v0.17"]
        DW["D-Wave Ocean SDK"]
        SQ["SquidASM / NetSquid"]
        ST["Stim (Stabilizer)"]
        CUQ["NVIDIA CUDA-Q"]
        TK["pytket (Quantinuum)"]
    end

    subgraph L4["Layer 4 · Hardware Backends (9 Platforms)"]
        IBM["IBM Nighthawk\n120q"]
        QTM["Quantinuum Helios\nTrapped Ion"]
        IONQ["IonQ Forte\n36q"]
        QUERA["QuEra Aquila\n256q Neutral Atom"]
        RIG["Rigetti Ankaa-3\n84q"]
        GW["Google Willow\n105q"]
        DAD["D-Wave Advantage2\n5000q"]
        CUDAQHW["NVIDIA CUDA-Q\nGPU Sim"]
        SIMS["Local Simulators\nAer / Fake Backends"]
    end

    subgraph L5["Layer 5 · Graph Intelligence"]
        NEO["Neo4j 5.26\nPrimary Graph Store + GDS"]
        FAL["FalkorDB\nAgent Working Memory"]
        KUZ["Kuzu\nEmbedded Analytical"]
        GRP["Graphiti 0.11\nTemporal Agent Memory"]
        GRAG["GraphRAG Pipeline\nLLM Graph Builder"]
    end

    subgraph L6["Layer 6 · Data & Workflow"]
        PG["PostgreSQL\nMetadata"]
        DDB["DuckDB\nAnalytics"]
        CHR["ChromaDB\nVector Embeddings"]
        S3["S3 / MinIO\nArtifact Store"]
        LDF["Live Data Feeds\nFinance · Bio · Climate"]
        WF["Workflow Orchestration\nCelery + Dask + Prefect"]
        QRNG["QRNG Engine\nEntropy Pool"]
    end

    subgraph L7["Layer 7 · Enterprise & Community"]
        SSO["Keycloak SSO / SAML"]
        RBAC["RBAC / Multi-Tenancy"]
        COMP["HIPAA / SOC2 / GDPR"]
        BENCH["Benchmarking Engine\nIBM Benchpress"]
        MKT["App Marketplace"]
        EDU["Learning Academy"]
    end

    subgraph AI["AI Model Layer"]
        MLX["Apple MLX\nmacOS primary"]
        OLLAMA["Ollama\nLocal LLM"]
        CLAUDE["Anthropic Claude\nCloud"]
        OPENAI["OpenAI GPT-4o\nCloud"]
        GEMINI["Google Gemini\nCloud"]
    end

    UI --> OA
    AP --> OA
    OA --> PA
    PA --> AGENTS
    AGENTS --> QK
    QK --> AER
    QK --> L4
    DW --> DAD
    SQ --> L4
    CUQ --> CUDAQHW
    AGENTS --> L5
    L5 --> L6
    AGENTS --> AI
    L7 -.->|governs| L1
    L7 -.->|governs| L2
```

---

## 2. Agentic Framework Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant OA as Orchestrator Agent
    participant PA as Planning Agent
    participant DA as Domain Agent
    participant QE as Quantum Executor
    participant HAL as Hardware Abstraction Layer
    participant GDB as Graph DB (Neo4j/Graphiti)
    participant LLM as LLM (MLX / Ollama / Cloud)
    participant HW as QPU / Simulator

    User->>UI: Natural language query
    UI->>OA: Parsed user message
    OA->>LLM: Intent classification
    LLM-->>OA: Agent routing decision
    OA->>PA: Complex task? Build plan
    PA->>GDB: Pull relevant graph context (Graphiti)
    GDB-->>PA: Prior experiments / knowledge subgraph
    PA->>DA: Dispatch with context + plan
    DA->>LLM: Generate Qiskit code / analysis
    LLM-->>DA: Code artifact
    DA->>QE: Execute circuit
    QE->>HAL: Detect platform (MPS / CUDA / CPU)
    HAL-->>QE: Optimal backend config
    QE->>HW: Submit job
    HW-->>QE: Raw results
    QE-->>DA: Processed results
    DA->>GDB: Write experiment nodes + edges to Neo4j
    DA-->>OA: Structured response + artifacts
    OA-->>UI: Streamed response + artifact panel
    UI-->>User: Chat response + circuit diagram + data
```

---

## 3. Hardware Abstraction Layer (HAL)

```mermaid
flowchart TD
    START([Detect Platform]) --> IS_MAC{macOS ARM64\n+ MPS available?}
    IS_MAC -->|Yes| MPS_PATH
    IS_MAC -->|No| IS_CUDA{torch.cuda\navailable?}
    IS_CUDA -->|Yes| CUDA_PATH
    IS_CUDA -->|No| CPU_PATH

    subgraph MPS_PATH["macOS Apple Silicon Path"]
        MPS_DEV["torch_device = mps\naer_device = CPU\nllm_backend = MLX"]
        MPS_AER["Qiskit Aer CPU\n+ Accelerate Framework\n+ AMX coprocessor"]
        MPS_QML["PyTorch MPS\nQNN/QSVM training\nTorchConnector → mps"]
        MPS_LLM["Apple MLX\nPrimary LLM inference\n50+ tok/s 8B model"]
        MPS_FALL["Ollama fallback\nModel compatibility"]
    end

    subgraph CUDA_PATH["Windows / Linux CUDA Path"]
        CUDA_DEV["torch_device = cuda\naer_device = GPU\nllm_backend = ollama"]
        CUDA_AER["Qiskit Aer GPU\n+ CUDA / cuStateVec\n14x CPU speedup"]
        CUDA_QML["PyTorch CUDA\nFull GPU QML training\nTF32 on Ampere+"]
        CUDA_LLM["Ollama + CUDA\nGPU-accelerated LLM"]
        CUDA_CUQ["NVIDIA CUDA-Q\nHPC simulation"]
    end

    subgraph CPU_PATH["CPU Fallback"]
        CPU_DEV["torch_device = cpu\nAll features work\nSlower simulation"]
    end

    subgraph QUBIT_ROUTING["Qubit-Count Routing"]
        Q_20["≤ 20q → statevector\n<0.1s all platforms"]
        Q_28["21-28q → statevector\nMac: 0.5-5s | GPU: <0.5s"]
        Q_32["29-32q → MPS method\n(Matrix Product State)\nor GPU statevector"]
        Q_35["33-35q → Large Mac wins\n512GB RAM > GPU VRAM"]
        Q_50["50q+ → IBM Quantum\ncloud / D-Wave"]
        Q_CLIF["Clifford-only → Stim\n<0.001s any size"]
    end

    MPS_PATH --> QUBIT_ROUTING
    CUDA_PATH --> QUBIT_ROUTING
    CPU_PATH --> QUBIT_ROUTING
```

---

## 4. Agent Interaction & Tool Registry

```mermaid
graph LR
    subgraph ORCH["Orchestrator"]
        ORC["Orchestrator\nAgent"]
        PLAN["Planning\nAgent"]
    end

    subgraph DOM["Domain Agents"]
        RES["Research\nAgent"]
        CHM["Chemistry\nAgent"]
        FIN["Finance\nAgent"]
        CRY["Crypto\nAgent"]
        QML_A["QML\nAgent"]
        OPT["Optimization\nAgent"]
        SCI["Climate /\nScience Agent"]
        COD["Code\nAgent"]
        QGI["QGI Graph\nAgent"]
        SEN["Sensing\nAgent"]
        NET["Networking\nAgent"]
        ANN["Annealing\nAgent"]
    end

    subgraph TOOLS["Tool Registry"]
        T1["circuit_builder"]
        T2["transpiler"]
        T3["aer_simulator"]
        T4["ibm_runtime"]
        T5["dwave_leap"]
        T6["neo4j_query\n(Text2Cypher)"]
        T7["graphiti_memory"]
        T8["visualizer"]
        T9["file_exporter"]
        T10["arXiv_search"]
        T11["live_data_feed"]
        T12["qrng_pool"]
        T13["error_mitigation\nZNE / PEC / M3"]
        T14["benchpress"]
        T15["squidasm_net"]
        T16["stim_simulator"]
    end

    ORC --> DOM
    PLAN --> DOM
    RES --> T1 & T2 & T3 & T8 & T10
    CHM --> T1 & T2 & T3 & T4 & T13 & T11
    FIN --> T1 & T3 & T4 & T6 & T11 & T12
    CRY --> T1 & T3 & T15 & T12
    QML_A --> T1 & T2 & T3 & T4 & T13
    OPT --> T1 & T2 & T3 & T5 & T6 & T11
    SCI --> T1 & T3 & T4 & T13
    COD --> T1 & T2 & T3 & T8 & T9
    QGI --> T6 & T1 & T3 & T8
    SEN --> T1 & T3
    NET --> T1 & T15
    ANN --> T5
```

---

## 5. Graph Database Architecture

```mermaid
graph TD
    subgraph NEO4J["Neo4j 5.26 — Primary Knowledge Store"]
        MKG["Molecular\nKnowledge Graph"]
        FKG["Financial\nCorrelation Graph"]
        CTG["Circuit Topology\nGraph"]
        SKG["Scientific\nKnowledge Graph"]
        LKG["Logistics\nGraph"]
    end

    subgraph FALKOR["FalkorDB — Agent Working Memory"]
        GRT["Graphiti\nTemporal Knowledge Graph"]
        SES["Session\nGraphs"]
        EPI["Episode\nIngestion"]
    end

    subgraph KUZU["Kuzu — Embedded Analytical"]
        LOC["Local / Offline\nMode Analytics"]
        EXP["Experiment Graph\nAnalysis (no server)"]
    end

    subgraph GRAPHRAG["GraphRAG Pipeline"]
        LGB["LLM Graph Builder\narXiv / PDF / URL ingestion"]
        T2C["Text2Cypher\nNatural language → Cypher"]
        HYB["Hybrid Retrieval\nBM25 + Semantic + Graph"]
        COM["Community Detection\nLouvain + GDS summaries"]
    end

    subgraph GDS["Graph Data Science Library"]
        PR["PageRank"]
        BC["Betweenness Centrality"]
        LV["Louvain Community"]
        N2V["Node2Vec Embeddings"]
        SP["Shortest Path"]
        GSAGE["GraphSAGE"]
    end

    QGI_AG["QGI Agent"] -->|Extract subgraph| NEO4J
    QGI_AG -->|Encode → QuantumCircuit| QK2["Qiskit"]
    QK2 -->|Results| QGI_AG
    QGI_AG -->|Enrich nodes/edges| NEO4J

    FALKOR --> HYB
    NEO4J --> HYB
    HYB -->|Context injection| LLM2["LLM Context Window"]

    NEO4J --> GDS
    GDS --> GRAPHRAG
    LGB --> NEO4J
    T2C --> NEO4J
```

---

## 6. Domain Graph Data Models

```mermaid
erDiagram
    %% ─── Molecular Knowledge Graph ───
    MOLECULE {
        string id PK
        string smiles
        string inchi
        float molecular_weight
        string formula
    }
    ATOM {
        string id PK
        string element
        int atomic_number
    }
    PROTEIN {
        string id PK
        string uniprot_id
        string name
        string sequence
    }
    VQE_RESULT {
        string id PK
        float energy_hartree
        string ansatz
        int shots
        string backend
        datetime timestamp
    }
    DRUG_CANDIDATE {
        string id PK
        string name
        float binding_affinity
        string admet_score
    }

    MOLECULE ||--o{ ATOM : "CONTAINS"
    ATOM ||--o{ ATOM : "BONDS_TO (bond_order, length)"
    MOLECULE ||--o{ VQE_RESULT : "SIMULATED_BY"
    DRUG_CANDIDATE ||--o{ PROTEIN : "INHIBITS / ACTIVATES"
    MOLECULE ||--o{ MOLECULE : "SIMILAR_TO (tanimoto_score)"

    %% ─── Financial Correlation Graph ───
    ASSET {
        string ticker PK
        string name
        string asset_class
        float current_price
    }
    PORTFOLIO {
        string id PK
        string name
        float total_value
        float sharpe_ratio
    }
    QUANTUM_RESULT_FIN {
        string id PK
        string algorithm
        float approximation_ratio
        int p_layers
        datetime run_date
    }
    MARKET_EVENT {
        string id PK
        string type
        datetime occurred_at
    }

    ASSET ||--o{ ASSET : "CORRELATES_WITH (coeff, window)"
    ASSET }o--|| PORTFOLIO : "PART_OF (weight)"
    PORTFOLIO ||--o{ QUANTUM_RESULT_FIN : "OPTIMIZED_BY"
    ASSET ||--o{ MARKET_EVENT : "INFLUENCED_BY"

    %% ─── Circuit Topology Graph ───
    CIRCUIT {
        string id PK
        int num_qubits
        int depth
        string qpy_binary
        string openqasm3
    }
    GATE_NODE {
        string id PK
        string gate_type
        int[] target_qubits
        int moment
    }
    QPU_JOB {
        string id PK
        string backend
        int shots
        string status
        float credits_used
    }
    RESULT_SET {
        string id PK
        float fidelity
        float error_rate
        json counts
    }

    CIRCUIT ||--o{ GATE_NODE : "APPLIES_GATE (moment)"
    GATE_NODE ||--o{ GATE_NODE : "ENTANGLES (qubit→qubit)"
    CIRCUIT ||--o{ CIRCUIT : "TRANSPILED_TO (backend, opt_level)"
    QPU_JOB ||--|| RESULT_SET : "PRODUCED"
    RESULT_SET ||--o{ RESULT_SET : "MITIGATED_BY (ZNE/PEC/M3)"

    %% ─── Scientific Knowledge Graph ───
    PAPER {
        string id PK
        string arxiv_id
        string title
        string abstract
        date published
    }
    ALGORITHM {
        string id PK
        string name
        string family
        int qubits_needed
        int gate_depth
    }
    CONCEPT {
        string id PK
        string name
        float[] embedding
    }

    PAPER ||--o{ PAPER : "CITES"
    PAPER ||--o{ ALGORITHM : "PROPOSES / IMPLEMENTS"
    ALGORITHM ||--o{ ALGORITHM : "BUILT_ON (generalization)"
    CONCEPT ||--o{ CONCEPT : "RELATED_TO (similarity)"
```

---

## 7. Experiment Lifecycle & Storage

```mermaid
stateDiagram-v2
    [*] --> Draft : User submits query
    Draft --> Planning : Orchestrator routes
    Planning --> CodeGen : LLM writes Qiskit code
    CodeGen --> Validation : Sandbox pre-check
    Validation --> Rejected : Syntax / logic error
    Rejected --> CodeGen : Auto-retry (max 3)
    Validation --> Queued : Valid circuit
    Queued --> RunningLocal : Aer simulator
    Queued --> RunningCloud : IBM / Braket / D-Wave
    RunningLocal --> ResultsReady : Simulation complete
    RunningCloud --> ResultsReady : QPU job returned
    ResultsReady --> Mitigated : Apply ZNE / PEC / M3
    ResultsReady --> Raw : No mitigation
    Mitigated --> Graphed : Write to Neo4j
    Raw --> Graphed : Write to Neo4j
    Graphed --> Artifact : Generate notebook / report
    Artifact --> Versioned : Stored in PostgreSQL / S3
    Versioned --> [*] : Displayed to user
```

---

## 8. Data Storage Architecture

```mermaid
graph LR
    subgraph WRITE["Write Paths"]
        EXP_W["Experiment\nRunner"]
        AGT_W["Agent\nResponse"]
        UI_W["User\nAction"]
    end

    subgraph PG_STORE["PostgreSQL — Structured Metadata"]
        PROJ["projects"]
        RUNS["experiment_runs"]
        JOBS["quantum_jobs"]
        USERS["users"]
        TEAMS["teams"]
        AUDIT["audit_log"]
        BUDGET["credit_usage"]
    end

    subgraph DUCK_STORE["DuckDB — Analytical Queries"]
        RESULTS["results_parquet"]
        METRICS["benchmark_metrics"]
        TIMESERIES["energy_timeseries"]
        PERF["backend_performance"]
    end

    subgraph VECTOR_STORE["ChromaDB — Embeddings"]
        EXP_EMB["experiment_embeddings"]
        CIRCUIT_EMB["circuit_embeddings"]
        DOC_EMB["document_embeddings"]
    end

    subgraph GRAPH_STORE["Neo4j — Knowledge Graph"]
        DOM_GRAPHS["Domain Graphs\nMolecular / Financial / Circuit"]
        SCI_GRAPH["Scientific\nKnowledge Graph"]
        EXP_GRAPH["Experiment\nProvenance Graph"]
    end

    subgraph OBJ_STORE["S3/MinIO — Object Storage"]
        NOTEBOOKS["Jupyter Notebooks"]
        CIRCUITS_QPY["QPY Binary Circuits"]
        REPORTS["Research Reports"]
        DIAGRAMS["Circuit Diagrams"]
    end

    subgraph FALKOR_STORE["FalkorDB — Agent Memory"]
        AGENT_MEM["Graphiti Episodes\nPer-user/agent temporal graph"]
    end

    EXP_W --> PG_STORE
    EXP_W --> DUCK_STORE
    EXP_W --> GRAPH_STORE
    EXP_W --> OBJ_STORE
    AGT_W --> FALKOR_STORE
    AGT_W --> VECTOR_STORE
    UI_W --> PG_STORE
```

---

## 9. Live Data Feed Connectors

```mermaid
flowchart LR
    subgraph FEEDS["Live Data Sources"]
        YF["Yahoo Finance\nAlpha Vantage\nPolygon.io"]
        PC["PubChem\n117M compounds"]
        CB["ChEMBL\nBioactive molecules"]
        PDB_F["Protein Data Bank"]
        NCBI["NCBI / UniProt\nGenomics"]
        NOAA["NOAA / NASA\nClimate Data"]
        SAP["SAP / Oracle ERP\nSupply Chain"]
        ARX["arXiv API\nLive papers"]
        IBM_CAL["IBM Quantum\nCalibration Data"]
    end

    subgraph TRANSFORM["Data Transform Pipeline"]
        NORM["Normalize\n& Validate"]
        ENC["Quantum Encoding\nAmplitude / Angle / Basis"]
        EMBED["Generate\nEmbeddings"]
    end

    subgraph AGENTS_DEST["Agent Destinations"]
        FA["Finance Agent"]
        CA["Chemistry Agent"]
        SA["Science / Climate Agent"]
        OA_D["Optimization Agent"]
        RA["Research Agent"]
        QGI_D["QGI Agent"]
    end

    YF --> NORM --> ENC --> FA
    PC & CB & PDB_F --> NORM --> ENC --> CA
    NCBI --> NORM --> EMBED --> CA
    NOAA --> NORM --> ENC --> SA
    SAP --> NORM --> ENC --> OA_D
    ARX --> NORM --> EMBED --> RA & QGI_D
    IBM_CAL --> NORM --> FA & CA & QGI_D
```

---

## 10. Quantum Workflow Orchestration Engine

```mermaid
flowchart TD
    subgraph UI_WF["User / API"]
        WF_DEF["Workflow Definition\n(DAG Builder UI or API)"]
        PARAM_GRID["Parameter Grid\ne.g. angles × depths × backends"]
    end

    subgraph ORCH_WF["Orchestration Layer"]
        PREFECT["Prefect / Airflow\nDAG Scheduler"]
        CELERY["Celery Workers\nClassical pre/post-processing"]
        DASK["Dask / Ray\nDistributed classical compute"]
        REDIS_Q["Redis\nJob Priority Queue"]
    end

    subgraph EXEC_WF["Execution Layer"]
        SIM_POOL["Simulator Pool\nAer / CUDA-Q (parallel)"]
        QPU_POOL["QPU Queue\nIBM Batches / Sessions"]
        DWAVE_Q["D-Wave Hybrid\nSolver Queue"]
    end

    subgraph MONITOR_WF["Monitoring"]
        GANTT["Live Gantt View\nJob status dashboard"]
        COST_G["Credit Budget\nEnforcement"]
        RETRY["Auto-Retry\nExponential backoff"]
        GRAFANA["Grafana\nMetrics / Alerting"]
    end

    WF_DEF --> PREFECT
    PARAM_GRID --> CELERY
    PREFECT --> REDIS_Q
    CELERY --> REDIS_Q
    REDIS_Q --> SIM_POOL & QPU_POOL & DWAVE_Q
    SIM_POOL --> GRAFANA
    QPU_POOL --> COST_G
    DWAVE_Q --> GRAFANA
    COST_G --> RETRY
    GANTT -.-> REDIS_Q
```

---

## 11. Fault-Tolerant Circuit & Error Mitigation Stack

```mermaid
graph TD
    subgraph NOISY["Noisy Circuit Layer (NISQ)"]
        RAW_C["Raw QuantumCircuit"]
        TWIRL["Pauli Twirling\n(BoxOp)"]
        ZNE["Zero-Noise\nExtrapolation"]
        PEC["Probabilistic Error\nCancellation"]
        M3["M3 Readout\nError Mitigation"]
        PNA["PNA Addon\nPropagated Noise Absorption"]
    end

    subgraph FT["Fault-Tolerant Layer (Future)"]
        SC["Surface Code\nEncoder (distance d)"]
        QLDPC["qLDPC Codes\n(IBM Nighthawk/Loon)"]
        MWPM["MWPM Decoder\nPyMatching / Blossom"]
        LOG_Q["Logical Qubits\nTransversal gates"]
        RES_EST["Resource Estimator\nPhysical qubit cost"]
        TIMELINE["Timeline Tracker\n'Your algorithm ≈ 2031'"]
    end

    subgraph STIM_LAYER["Stabilizer Simulation"]
        STIM_SIM["Stim\n(Clifford circuits)"]
        PYMAT["PyMatching\nDecoder"]
    end

    RAW_C --> TWIRL --> ZNE --> PEC --> M3 --> PNA
    RAW_C -.->|Clifford-only| STIM_SIM
    STIM_SIM --> PYMAT
    RAW_C -.->|FT design| SC --> MWPM
    SC --> QLDPC
    LOG_Q --> RES_EST --> TIMELINE
```

---

## 12. QRNG & Cryptography Flow

```mermaid
sequenceDiagram
    participant Q as Qiskit Circuit
    participant QRNG as QRNG Engine
    participant POOL as Entropy Pool (Redis)
    participant FIN as Finance Agent
    participant CRY as Crypto Agent
    participant NET as Networking Agent

    Note over Q,POOL: Hadamard |0⟩ → measure → true random bit
    Q->>QRNG: Generate N random bits
    QRNG->>QRNG: NIST SP 800-22 validation
    QRNG->>POOL: Store certified entropy
    
    FIN->>POOL: Pull random samples (Monte Carlo)
    POOL-->>FIN: QRNG-certified samples
    
    CRY->>POOL: Pull bits for key generation
    POOL-->>CRY: AES / Kyber seed material
    
    NET->>Q: BB84 QKD simulation
    Q-->>NET: Quantum key bits
    NET->>NET: Error estimation + privacy amplification
    NET-->>CRY: Final shared key
```

---

## 13. D-Wave Annealing Pipeline

```mermaid
flowchart LR
    USER_PROB["User Problem\n(natural language)"] --> LLM_QUBO["LLM\nQUBO Formulation"]
    LLM_QUBO --> BQM["BQM / CQM\n(dimod)"]
    BQM --> EMBED["minorminer\nEmbedding"]
    
    EMBED --> SIZE{Problem size?}
    SIZE -->|Small → pure QPU| DWAVE_HW["D-Wave Advantage2\n5000q Pegasus"]
    SIZE -->|Large → hybrid| DWAVE_HYB["D-Wave Hybrid\nSolver (unlimited vars)"]
    SIZE -->|Local test| NEAL["dwave-neal\nSimulated Annealing"]
    
    DWAVE_HW --> RESULT["Annealing Result\nSample set"]
    DWAVE_HYB --> RESULT
    NEAL --> RESULT
    
    RESULT --> COMPARE["Classical Comparison\nGurobi / CPLEX"]
    COMPARE --> BENCH_DB["Benchmark DB\nQuantum vs Classical"]
    RESULT --> NEO_WRITE["Write to Neo4j\nSolution nodes + edges"]
    BENCH_DB --> REPORT["Advantage Report\nPDF / Markdown"]
```

---

## 14. Quantum Sensing Agent Module

```mermaid
graph TD
    subgraph SENSING["Quantum Sensing Agent"]
        ATM["Atom Interferometry\nGyroscope / Gravimeter"]
        NVC["NV-Center\nDiamond Magnetometer\n0.1 fT/√Hz"]
        QCLK["Quantum Clock\n10⁻¹⁸ stability"]
        QLID["Quantum LiDAR\nEntangled photon sensing"]
        BIO["Quantum Bio-imaging\nMRI enhancement"]
        NAV["GPS-Denied Navigation\nQuantum INS"]
    end

    subgraph METRICS["Quantum Advantage Metrics"]
        FI["Fisher Information\nF(θ)"]
        CRB["Cramér-Rao Bound\n1/√(n·F)"]
        SQL["Standard Quantum Limit\n1/√N"]
        HL["Heisenberg Limit\n1/N"]
    end

    subgraph STACK["Sensing Stack"]
        QISKIT_S["Qiskit\n(atom interferometry circuits)"]
        QUTIP["QuTiP\n(open quantum systems)"]
        SCIPY_S["SciPy\n(signal processing)"]
        QCTRL["Q-CTRL Fire Opal\n(software ruggedization)"]
    end

    ATM & NVC & QCLK --> METRICS
    QLID & BIO & NAV --> METRICS
    METRICS --> STACK
    SQL & HL --> FI
```

---

## 15. Competitive Moat Summary

```mermaid
quadrantChart
    title Milimo Quantum — Feature vs Competitor Coverage
    x-axis Low Quantum Depth --> High Quantum Depth
    y-axis Low AI Integration --> High AI Integration
    quadrant-1 Milimo Quantum Zone
    quadrant-2 AI-First (no quantum)
    quadrant-3 Basic Tools
    quadrant-4 Quantum-First (no AI)
    Milimo Quantum: [0.95, 0.95]
    IBM Quantum Lab: [0.75, 0.25]
    Azure Quantum: [0.65, 0.30]
    Amazon Braket: [0.60, 0.25]
    Classiq: [0.70, 0.35]
    ChatGPT: [0.05, 0.80]
    D-Wave Leap: [0.55, 0.20]
    Google Quantum AI: [0.80, 0.30]
```

---

## 16. Complete Technology Stack Reference

```mermaid
mindmap
  root((Milimo Quantum))
    Frontend
      React 18 + TypeScript
      Tailwind CSS
      Monaco Editor
      Plotly.js + D3.js
      Three.js (Bloch sphere)
      MathJax (LaTeX)
      Socket.io (streaming)
      Pyodide (in-browser Python)
    Backend API
      Python 3.12 + FastAPI
      LangChain / LlamaIndex
      Celery + Redis
      Nginx reverse proxy
    Quantum Execution
      Qiskit SDK v2.2
      Qiskit Aer v0.17
      qiskit-ibm-runtime
      qiskit-nature
      qiskit-finance
      qiskit-machine-learning
      qiskit-optimization
      qiskit-algorithms
      Qiskit Addons (PNA/SLC/SQD)
      D-Wave Ocean SDK
      SquidASM / NetSquid
      Stim + PyMatching
      NVIDIA CUDA-Q
      pytket (Quantinuum)
      mitiq (extra mitigation)
    AI Models
      Apple MLX (macOS primary)
      Ollama (local LLM)
      Anthropic Claude API
      OpenAI GPT-4o API
      Google Gemini API
    Graph Intelligence
      Neo4j 5.26 + GDS
      FalkorDB
      Kuzu
      Graphiti 0.11
      NetworkX + rustworkx
      torch_geometric
      node2vec
      pyvis + Plotly
    Data Storage
      PostgreSQL (metadata)
      DuckDB (analytics)
      ChromaDB (vectors)
      S3 / MinIO (artifacts)
      Redis (cache + queue)
    Enterprise
      Keycloak (SSO/SAML)
      OPA (policy engine)
      HashiCorp Vault (secrets)
      OpenTelemetry (audit)
      Stripe (billing)
      CRYSTALS-Kyber (PQC TLS)
    Infrastructure
      Docker + Docker Compose
      Kubernetes (cloud)
      GitHub Actions CI/CD
      Grafana (monitoring)
      Let's Encrypt (TLS)
    Platform (macOS)
      Apple MLX + mlx-lm
      PyTorch MPS (QML GPU)
      Accelerate Framework (AMX)
      Tauri (native desktop)
    Platform (Windows/Linux)
      NVIDIA CUDA (Aer GPU)
      cuQuantum / cuStateVec
      CUDA-Q HPC
      WSL2 Ubuntu
      Docker GPU passthrough
```

---

*Milimo Quantum — The Universe of Quantum, In One Place*
*Qiskit v1.4 · D-Wave · SquidASM · CUDA-Q · Neo4j · Graphiti · Apple MLX · Open Source*
