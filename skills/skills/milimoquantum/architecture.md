---
description: Milimo Quantum platform architecture — 7-layer system with 14 agents, HAL, quantum execution engine, and graph intelligence
---

# Architecture Skill

## Platform Layers (Top → Bottom)

| Layer | Purpose | Key Components |
|-------|---------|----------------|
| L1 — Presentation | User interface | React 18 + TS, Artifact Panel, Learning Academy, Marketplace |
| L2 — Agent Orchestration | Intent routing + domain logic | 14 agents: Orchestrator, Planning, Research, Chemistry, Finance, Crypto, QML, Optimization, Climate/Science, Code, QGI, Sensing, Networking, D-Wave Annealing |
| L3 — Quantum Execution | Circuit compilation + simulation | Qiskit SDK v1.4, Aer v0.17, D-Wave Ocean, SquidASM, Stim, CUDA-Q, pytket |
| L4 — Hardware Backends | QPU access | IBM (120q), Quantinuum (trapped ion), IonQ (36q), QuEra (256q), Rigetti (84q), Google Willow (105q), D-Wave (5000q), CUDA-Q GPU, Local Aer |
| L5 — Graph Intelligence | Knowledge graph + memory | Neo4j 5.26, FalkorDB (agent memory), Kuzu (embedded), Graphiti 0.11, GraphRAG |
| L6 — Data & Workflow | Storage + orchestration | PostgreSQL, DuckDB, ChromaDB, S3/MinIO, Live Data Feeds, Celery+Dask+Prefect, QRNG |
| L7 — Enterprise | Governance | Keycloak SSO, RBAC, HIPAA/SOC2/GDPR, Benchpress, Marketplace, Academy |

## Agent Flow

```
User query → React UI → Orchestrator Agent → Intent Classification (LLM)
  → If complex: Planning Agent → builds execution plan → dispatches to domain agents
  → If simple: direct routing to domain agent via slash command or keyword match

Domain Agent → LLM generates Qiskit code → Quantum Executor → HAL detects platform
  → results → agent writes to Neo4j → structured response + artifacts → UI
```

## Agent → Tool Mapping

- **Code Agent**: circuit_builder, transpiler, aer_simulator, visualizer, file_exporter
- **Research Agent**: circuit_builder, aer_simulator, visualizer, arXiv_search
- **Chemistry Agent**: circuit_builder, transpiler, aer_simulator, ibm_runtime, error_mitigation, live_data_feed
- **Finance Agent**: circuit_builder, aer_simulator, ibm_runtime, neo4j_query, live_data_feed, qrng_pool
- **Optimization Agent**: circuit_builder, transpiler, aer_simulator, dwave_leap, neo4j_query, live_data_feed
- **QGI Agent**: neo4j_query, circuit_builder, aer_simulator, visualizer

## Experiment Lifecycle

```
Draft → Planning → CodeGen → Validation (sandbox) → Queued
  → RunningLocal (Aer) or RunningCloud (IBM/Braket/D-Wave)
  → ResultsReady → Mitigated (ZNE/PEC/M3) or Raw
  → Graphed (write to Neo4j) → Artifact (notebook/report) → Versioned → Display
```

## Storage Architecture

- **PostgreSQL**: projects, experiment_runs, quantum_jobs, users, teams, audit_log, credits
- **DuckDB**: results_parquet, benchmark_metrics, energy_timeseries
- **ChromaDB**: experiment/circuit/document embeddings
- **Neo4j**: domain graphs (molecular, financial, circuit, scientific)
- **FalkorDB + Graphiti**: agent working memory, temporal knowledge graph
- **S3/MinIO**: Jupyter notebooks, QPY circuits, reports, diagrams
