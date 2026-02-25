⬡

**MILIMO QUANTUM**

*Graph Database Integration Addendum*

How a Graph Database Layer Adds a New Dimension to the Milimo Quantum
Platform

Research Investigation \| Neo4j · FalkorDB · GraphRAG · Graphiti ·
Quantum Graph Algorithms

February 2026 \| Supplement to Project Blueprint v1.0

**1. Why Add a Graph Database to Milimo Quantum?**

The core Milimo Quantum architecture stores quantum experiment results,
circuit artifacts, and project metadata in relational (PostgreSQL) and
analytical (DuckDB) stores --- both excellent at what they do. But the
world quantum computing operates on is fundamentally relational in a
different sense: atoms bond to atoms, proteins fold along chains,
financial instruments depend on each other, knowledge concepts connect
to concepts, circuits contain gates that share qubits. Relational tables
flatten these rich webs into rows. A graph database keeps the web.

+-----------------------------------------------------------------------+
| **The Core Insight**                                                  |
|                                                                       |
| Quantum computing is about relationships: entanglement (qubits        |
| connected), molecular bonding (atoms connected),                      |
|                                                                       |
| financial correlation (assets connected), drug targets (proteins      |
| connected), supply routes (nodes connected).                          |
|                                                                       |
| A graph database is the natural data structure to model, store,       |
| query, and reason over these connected realities ---                  |
|                                                                       |
| and when paired with quantum graph algorithms (quantum walks, QAOA on |
| graphs, quantum GNNs), you create                                     |
|                                                                       |
| a feedback loop where the graph feeds the quantum engine and the      |
| quantum engine enriches the graph.                                    |
+-----------------------------------------------------------------------+

Adding a graph database layer introduces five new dimensions to Milimo
Quantum:

- **Knowledge Graphs:** Give AI agents structured, traversable memory of
  every quantum domain --- chemistry, finance, pharma, cryptography ---
  enabling GraphRAG-powered reasoning that dramatically reduces
  hallucination.

- **Quantum Graph Intelligence:** Apply actual quantum algorithms
  (quantum walks, QAOA, quantum GNNs) directly to graph data pulled from
  the database --- e.g., find shortest reaction pathway in a molecular
  graph quantumly.

- **Experiment Graph:** Model every circuit, job, result, parameter, and
  researcher as nodes with rich edges --- enabling queries classical DBs
  can\'t answer: \'find all experiments topologically similar to this
  one that achieved lower error\'.

- **Domain Knowledge Networks:** Drug-molecule-protein graphs, financial
  asset correlation graphs, supply chain graphs, quantum circuit
  topology graphs --- each enriching the relevant domain agent.

- **Real-Time Agent Memory:** Using Graphiti (temporal knowledge graph),
  agents build and update a living memory graph across all sessions,
  user interactions, and results --- persistent, searchable, always
  current.

**2. The Graph Database Stack**

After evaluating six graph database systems against Milimo Quantum\'s
requirements --- performance, AI integration maturity,
quantum-readiness, local deployment, and Python ecosystem --- the
following stack is recommended:

**2.1 Neo4j 5.26 --- Primary Graph Store**

+-----------------------------------------------------------------------+
| **Neo4j: Why It\'s the Core Choice**                                  |
|                                                                       |
| ▸ World\'s most mature graph database with native LLM / AI            |
| integrations (LangChain, LlamaIndex, Graphiti)                        |
|                                                                       |
| ▸ Cypher query language: expressive, readable, LLM-generatable        |
| (Text2Cypher)                                                         |
|                                                                       |
| ▸ Vector + graph hybrid search in a single query (Neo4j 5.x+ with     |
| vector indexes)                                                       |
|                                                                       |
| ▸ GraphRAG-first: LLM Graph Builder (open-source, MIT license)        |
| auto-builds knowledge graphs from PDFs, URLs, papers                  |
|                                                                       |
| ▸ Graph Data Science (GDS) library: 65+ algorithms --- PageRank,      |
| Louvain community detection, node embeddings, shortest paths          |
|                                                                       |
| ▸ MCP server support: Claude and other LLMs can query Neo4j directly  |
| via tool calls                                                        |
|                                                                       |
| ▸ Docker Compose deployable locally; AuraDB free tier for cloud;      |
| enterprise for production                                             |
+-----------------------------------------------------------------------+

**Key Neo4j Capabilities for Milimo Quantum**

- **Cypher + GDS for Graph Algorithms:** Run Louvain community detection
  on molecular graphs, PageRank on knowledge citation networks,
  betweenness centrality on financial correlation graphs --- all from
  Python or directly from agent tool calls.

- **Vector Indexes:** Store embeddings alongside nodes (circuits,
  molecules, papers). Hybrid search: \'find circuits semantically
  similar to this one that also share qubits with this topology\'.

- **Graph Data Science Library:** Node2Vec embeddings, FastRP, GraphSAGE
  for unsupervised graph learning --- feed embeddings to quantum ML
  models.

- **Temporal Graph Features:** Time-stamped relationships enable \'how
  did this molecule\'s simulated energy change across 50 VQE experiments
  over time?\'

- **LLM Graph Builder:** Auto-extract entities and relationships from
  quantum papers, drug discovery literature, financial reports →
  structured knowledge graphs in minutes.

**2.2 FalkorDB --- High-Performance In-Process Graph**

FalkorDB is a Redis-module-based graph database offering extremely
low-latency graph operations in-process. It is the backend for Graphiti
(the temporal agent memory layer). Ideal for agent working memory,
session graphs, and sub-millisecond traversals during active
conversations.

- **When to use FalkorDB vs Neo4j:** FalkorDB: agent short-term memory,
  real-time conversation graph, active session state. Neo4j: persistent
  domain knowledge graphs, experiment history, multi-user shared data,
  GDS analytics.

- **Graphiti Integration:** Graphiti (by Zep) is purpose-built for AI
  agents --- it maintains a temporal knowledge graph per agent/user in
  FalkorDB (or Neo4j/Kuzu) with hybrid BM25+semantic+graph retrieval.
  This is the agent memory backbone of Milimo Quantum.

- **Docker Deployment:** One command: docker run -p 6379:6379 -p
  3000:3000 falkordb/falkordb:latest --- zero config, runs alongside the
  existing Milimo stack.

**2.3 Kuzu --- Embedded Analytical Graph Database**

Kuzu is an embedded, column-oriented graph database (like DuckDB but for
graphs). It runs in-process with zero server overhead, is blazing fast
for analytical queries, and integrates natively with Python, PyArrow,
and Pandas. It is ideal for local Milimo Quantum deployments where
spinning up a Neo4j server is too heavy.

- **Use Case in Milimo:** Offline/local mode graph analytics: run graph
  algorithms on experiment graphs, circuit topology analysis, and
  molecular graphs without a running database server.

- **Cypher Compatible:** Kuzu supports openCypher, so all query patterns
  written for Neo4j run in Kuzu with minimal changes.

- **Graphiti Support:** Graphiti 0.11+ supports Kuzu as a backend
  alongside Neo4j and FalkorDB.

  ---------------------------------------------------------------------------
  **Database**       **Role in Milimo**     **Deployment**     **Best For**
  ------------------ ---------------------- ------------------ --------------
  Neo4j 5.26         Primary knowledge      Docker / AuraDB    Persistent
                     graph + GDS analytics                     domain graphs,
                                                               GDS, GraphRAG

  FalkorDB 1.x       Agent working memory   Docker             Real-time
                     (Graphiti)             (in-process)       agent memory,
                                                               session graphs

  Kuzu 0.11+         Embedded analytical    In-process /       Local mode,
                     graph                  file-based         offline
                                                               analytics,
                                                               no-server

  Amazon Neptune     Optional: cloud-scale  Managed AWS        Enterprise
                     graph                                     multi-region
                                                               production
  ---------------------------------------------------------------------------

**3. GraphRAG --- Supercharging Quantum AI Agents**

Retrieval-Augmented Generation (RAG) is how AI agents ground their
answers in real data rather than hallucinating. Standard vector RAG
retrieves chunks of text. GraphRAG retrieves a subgraph --- nodes AND
their relationships --- providing richer, more accurate context to the
LLM. For quantum domain agents, this difference is profound.

**3.1 Why GraphRAG Over Vector-Only RAG for Quantum Domains**

+----------------------------------+-----------------------------------+
| **Vector-Only RAG (Current)**    | **GraphRAG (Proposed Addition)**  |
|                                  |                                   |
| - Retrieves isolated text chunks | - Retrieves connected subgraph +  |
|                                  |   embeddings                      |
| - No relationship context        |                                   |
|                                  | - Full relationship traversal     |
| - High hallucination risk for    |                                   |
|   multi-hop queries              | - Multi-hop reasoning: A→B→C→D    |
|                                  |                                   |
| - \'What drugs target this       | - \'What drugs target this        |
|   protein pathway?\' → poor      |   protein pathway?\' → excellent  |
|                                  |                                   |
| - Cannot trace experiment        | - Full experiment provenance      |
|   lineage                        |   graph                           |
|                                  |                                   |
| - Loses                          | - Intact                          |
|   molecule-reaction-product      |   molecule→reaction→product       |
|   chains                         |   chains                          |
+----------------------------------+-----------------------------------+

**3.2 Graphiti --- Real-Time Agent Knowledge Graphs**

+-----------------------------------------------------------------------+
| **What Graphiti Brings to Milimo Quantum**                            |
|                                                                       |
| Graphiti (github.com/getzep/graphiti) is purpose-built for AI agent   |
| memory. It maintains a temporal                                       |
|                                                                       |
| knowledge graph that updates in real time as agents interact, run     |
| experiments, and receive results.                                     |
|                                                                       |
| Architecture: Each agent conversation → episodes → extracted entities |
| & relationships → stored in graph                                     |
|                                                                       |
| Retrieval: Hybrid BM25 keyword + semantic embedding + graph traversal |
| --- best of all three worlds                                          |
|                                                                       |
| Temporal: Every fact has a validity window --- agents know \'this     |
| molecule energy was 0.83 eV on day 12\'                               |
|                                                                       |
| Cross-session: Agent remembers user preferences, past experiments,    |
| preferred models, parameter history                                   |
|                                                                       |
| MCP Server: Graphiti ships with a Model Context Protocol server for   |
| direct LLM tool access                                                |
|                                                                       |
| Backends: Neo4j 5.26 / FalkorDB 1.1.2 / Kuzu 0.11.2 / Amazon Neptune  |
+-----------------------------------------------------------------------+

**Graphiti in Practice: Milimo Quantum Scenarios**

- **Scenario 1 --- Chemistry Agent Memory:** User runs VQE on H2 with
  ansatz depth 3 → results stored in graph. Next session: \'try LiH\' →
  Graphiti injects: previous H2 result, best ansatz parameters found,
  noise model used, error mitigation that worked. Agent doesn\'t start
  from zero.

- **Scenario 2 --- Finance Agent Memory:** User builds Markowitz
  portfolio for 10 tech stocks → graph records stock nodes, correlation
  edges, QAOA parameters, result quality. Next query \'add healthcare\'
  → agent traverses existing portfolio graph, identifies low-correlation
  health stocks, proposes quantum-optimized rebalance.

- **Scenario 3 --- Cross-Agent Reasoning:** Drug Discovery agent
  identifies a candidate molecule. QML agent is asked to classify its
  toxicity. Graphiti graph connects: molecule node → VQE energy node →
  QSVM classification node → result node. The QML agent sees the full
  chain without being explicitly told.

**3.3 Neo4j LLM Graph Builder --- Knowledge Ingestion**

The Neo4j LLM Graph Builder (open source, neo4j-labs) is integrated into
Milimo Quantum as a document ingestion pipeline. Users can upload
quantum papers, drug discovery literature, financial reports, patent
databases, or any text --- and the system automatically constructs a
structured knowledge graph.

- **Supported Inputs:** PDFs, .docx, web URLs, YouTube video
  transcripts, Wikipedia pages, arXiv papers (via API), PubMed
  abstracts.

- **Extraction Process:** LLM (Claude/GPT-4o/Llama3) identifies entities
  (molecules, algorithms, drugs, reactions, financial instruments) and
  relationships (INHIBITS, CATALYZES, OPTIMIZES, CORRELATES_WITH,
  IMPLEMENTED_BY) and stores them in Neo4j.

- **Lexical Graph:** Document chunks → embeddings → vector-indexed nodes
  → connected to entity nodes → enables both full-text and semantic
  search alongside graph traversal.

- **Community Summaries:** Louvain community detection groups related
  concepts; LLM generates summaries per community; global search
  synthesizes across communities (Microsoft GraphRAG pattern).

- **Chat Modes:** After ingestion, users query their knowledge graph in
  seven modes: vector, graph+vector, graph, fulltext, global, entity
  vector, and combined --- all accessible from the Milimo chat
  interface.

**4. Domain-Specific Graph Models**

Each Milimo Quantum domain agent gets its own graph data model optimised
for the types of queries and quantum computations it performs. These
graphs live in Neo4j, are queryable via Cypher, and are the target of
quantum graph algorithms run by the Quantum Graph Intelligence Agent
(Section 5).

**4.1 Molecular Knowledge Graph (Drug Discovery Agent)**

+-----------------------------------------------------------------------+
| **Node Types & Relationships**                                        |
|                                                                       |
| Nodes: Molecule \| Atom \| Protein \| Reaction \| DrugCandidate \|    |
| DiseaseTarget \| VQEResult                                            |
|                                                                       |
| Edges: BONDS_TO (atom→atom, with bond_order, bond_length)             |
|                                                                       |
| CATALYZES (molecule→reaction)                                         |
|                                                                       |
| INHIBITS \| ACTIVATES (drug→protein target)                           |
|                                                                       |
| HAS_CONFORMATION (molecule→3D structure)                              |
|                                                                       |
| SIMULATED_BY (molecule→VQEResult, with energy, ansatz, shots,         |
| backend)                                                              |
|                                                                       |
| SIMILAR_TO (molecule→molecule, similarity score via Tanimoto/quantum  |
| kernel)                                                               |
+-----------------------------------------------------------------------+

- **Quantum Graph Operations:** Run quantum walks on molecular bond
  graphs to compute electron delocalization paths. Map molecular QUBO to
  QAOA for lead compound selection. Feed node embeddings (Node2Vec on
  molecule graph) into quantum kernel SVM for activity prediction.

- **Example Query:** \'Find all drug candidates that inhibit BACE1, have
  simulated energy below -1.2 Hartree, and are within 2 hops of aspirin
  in the molecular similarity graph\' --- one Cypher query, instant
  results.

- **CERN-Intel Inspired:** Based on the CERN--Intel quantum database
  project (quantum indices for classical graph data),
  quantum-accelerated molecular graph lookup is implemented for large
  compound libraries.

**4.2 Financial Correlation Graph (Finance Agent)**

+-----------------------------------------------------------------------+
| **Node Types & Relationships**                                        |
|                                                                       |
| Nodes: Asset \| Sector \| Portfolio \| MarketEvent \| QuantumResult   |
| \| RiskFactor                                                         |
|                                                                       |
| Edges: CORRELATES_WITH (asset→asset, correlation_coefficient,         |
| time_window)                                                          |
|                                                                       |
| BELONGS_TO (asset→sector)                                             |
|                                                                       |
| PART_OF (asset→portfolio, weight, allocation)                         |
|                                                                       |
| INFLUENCED_BY (asset→marketEvent)                                     |
|                                                                       |
| OPTIMIZED_BY (portfolio→QuantumResult, QAOA params, Sharpe ratio,     |
| date)                                                                 |
|                                                                       |
| HEDGES (asset→asset, hedge ratio)                                     |
+-----------------------------------------------------------------------+

- **Quantum Graph Operations:** Run quantum walk PageRank on asset
  correlation graph to identify systemically important nodes (assets
  that, if they drop, cascade through the portfolio). Apply QAOA to
  maximum independent set on correlation graph for portfolio
  diversification. Quantum betweenness centrality to identify leverage
  points.

- **Dynamic Graph:** Market correlation edges are time-stamped and
  updated on each quantum Monte Carlo run. Temporal queries: \'how did
  BTC correlation with gold change across 100 experiments last
  quarter?\'

- **Fraud Detection:** Build transaction graphs; apply quantum walk
  anomaly detection to identify suspicious money flow paths that
  classical Dijkstra misses due to obfuscation.

**4.3 Quantum Circuit Topology Graph (Code & Research Agents)**

+-----------------------------------------------------------------------+
| **Node Types & Relationships**                                        |
|                                                                       |
| Nodes: Circuit \| Gate \| Qubit \| Job \| Backend \| Transpile \|     |
| ErrorMitigationRun \| ResultSet                                       |
|                                                                       |
| Edges: APPLIES_GATE (circuit→gate, at_moment, target_qubits)          |
|                                                                       |
| ENTANGLES (qubit→qubit, via CNOT/CZ/ECR gate)                         |
|                                                                       |
| TRANSPILED_TO (circuit→circuit, target_backend, optimization_level)   |
|                                                                       |
| EXECUTED_ON (job→backend, duration, status, credits_used)             |
|                                                                       |
| PRODUCED (job→resultSet, fidelity, error_rate)                        |
|                                                                       |
| MITIGATED_BY (resultSet→mitigatedResult, technique: ZNE/PEC/M3)       |
+-----------------------------------------------------------------------+

- **Circuit Similarity Search:** Embed circuits as graph neural network
  vectors (Node2Vec on circuit topology graph); search for circuits with
  similar entanglement structure for transfer learning of transpiler
  parameters.

- **Error Propagation Graph:** Track how errors propagate through a
  circuit\'s gate dependency graph. Visualize which qubits/gates are
  bottlenecks (high betweenness centrality = high error propagation
  risk).

- **Compilation Lineage:** Every transpilation recorded as a graph edge.
  Query: \'show all circuits that started as this QAOA template and were
  transpiled to Heron backend with optimization level 3 and achieved
  \>90% fidelity\'.

- **Qubit Connectivity Overlay:** Overlay QPU qubit connectivity graph
  on circuit entanglement graph to identify mismatches before execution
  (graph isomorphism check = pre-flight validation).

**4.4 Scientific Knowledge Graph (Research Agent)**

+-----------------------------------------------------------------------+
| **Node Types & Relationships**                                        |
|                                                                       |
| Nodes: Paper \| Author \| Algorithm \| Institution \| Dataset \|      |
| Hardware \| Concept \| Claim                                          |
|                                                                       |
| Edges: CITES (paper→paper)                                            |
|                                                                       |
| PROPOSES (paper→algorithm)                                            |
|                                                                       |
| IMPLEMENTS (paper→algorithm, with fidelity, qubits_needed,            |
| gate_depth)                                                           |
|                                                                       |
| CONTRADICTS \| CONFIRMS (paper→claim)                                 |
|                                                                       |
| BUILT_ON (algorithm→algorithm, relationship:                          |
| generalization/specialization/extension)                              |
|                                                                       |
| CO_AUTHORED (author→paper)                                            |
|                                                                       |
| RELATED_TO (concept→concept, semantic similarity score)               |
+-----------------------------------------------------------------------+

- **arXiv Live Ingestion:** Milimo Quantum continuously pulls new
  quantum computing papers from arXiv via API → LLM Graph Builder
  extracts entities → knowledge graph updated in real time. Agents
  always cite the latest research.

- **Algorithm Genealogy:** Query: \'show me the evolutionary tree from
  original VQE (Peruzzo 2014) to SQD used in IBM-Cleveland Clinic
  experiments\' --- a graph traversal yields a visual algorithm lineage.

- **Concept Clustering:** Louvain community detection on concept graph
  reveals research sub-fields. GDS community summaries generate
  auto-updating survey documents for each cluster.

**4.5 Optimization & Logistics Graph (Optimization Agent)**

+-----------------------------------------------------------------------+
| **Node Types & Relationships**                                        |
|                                                                       |
| Nodes: Location \| Vehicle \| Package \| Warehouse \| Route \|        |
| QAOAResult \| Constraint                                              |
|                                                                       |
| Edges: CONNECTS (location→location, distance, travel_time, cost)      |
|                                                                       |
| ASSIGNED_TO (vehicle→route)                                           |
|                                                                       |
| DELIVERS (package→location)                                           |
|                                                                       |
| OPTIMIZED_BY (route→QAOAResult, p_layers, gamma, beta,                |
| approximation_ratio)                                                  |
|                                                                       |
| VIOLATES \| SATISFIES (route→constraint)                              |
|                                                                       |
| SIMILAR_TO (problem→problem, QUBO structure similarity)               |
+-----------------------------------------------------------------------+

- **QUBO from Graph:** The Optimization Mapper Addon + graph model
  enables: extract vehicle routing graph from Neo4j → auto-formulate
  QUBO → run QAOA → write results back as edges. The graph IS the
  problem formulation.

- **Benchmark Comparison Graph:** Every classical Gurobi / CPLEX
  solution stored alongside QAOA results as parallel graph nodes with
  comparison edges --- clear quantum vs classical tracking.

**5. Quantum Graph Intelligence Agent --- New Agent Module**

The Graph Database integration unlocks an entirely new agent in Milimo
Quantum: the Quantum Graph Intelligence (QGI) Agent. This agent bridges
the graph database and the quantum execution engine --- pulling graph
data from Neo4j, running quantum graph algorithms on it via Qiskit, and
writing enriched results back to the graph.

+-----------------------------------------------------------------------+
| **Agent Tagline**                                                     |
|                                                                       |
| \"I take your real-world graphs --- molecules, markets, supply        |
| chains, knowledge networks --- and run quantum                        |
|                                                                       |
| algorithms on them that classical graph databases can\'t execute.     |
| Then I return the results back to the graph.\"                        |
+-----------------------------------------------------------------------+

**5.1 Quantum Graph Algorithms Catalogue**

**A. Quantum Walks --- Graph Traversal & Search**

Quantum walks are the quantum analogue of classical random walks. On a
graph, a quantum walker exists in a superposition of positions,
interfering constructively at solutions. Qiskit has implemented quantum
walks on IBM QPUs with verified quantum advantage on complete graphs.

- **Spatial Search:** Find marked nodes in a graph with O(√N) complexity
  vs O(N) classical. Applied to: find target protein in a molecular
  graph, identify anomalous transaction in a financial graph, find
  optimal route endpoint.

- **Community Detection:** Quantum walk eigenvectors correspond to graph
  community structure. Research published in 2025 demonstrates quantum
  walk community detection on complex networks via Qiskit circuits, with
  lower circuit depth than prior methods.

- **Node Classification:** Quantum walk probability distributions encode
  node neighborhoods --- use as features for quantum SVM classification
  (e.g., classify molecule nodes as drug-like vs non-drug-like based on
  their graph neighborhood).

- **Graph Isomorphism:** Quantum walks can distinguish non-isomorphic
  graphs with high probability --- critical for circuit topology
  matching and molecular structure comparison.

+-----------------------------------------------------------------------+
| **VLDB 2024 Research: Quantum Graph Algorithms Demonstrated**         |
|                                                                       |
| The VLDB 2024 Q-Data workshop demonstrated three graph algorithms on  |
| real IBM Quantum hardware:                                            |
|                                                                       |
| 1\. All-pairs shortest path --- quantum walk based, demonstrated on   |
| D-Wave and IBM Q                                                      |
|                                                                       |
| 2\. Graph coloring --- QUBO formulation, QAOA solution on IBM Quantum |
|                                                                       |
| 3\. Graph matching / isomorphism --- quantum walk approach on Qiskit  |
|                                                                       |
| These are the exact algorithms the QGI Agent will orchestrate on      |
| Milimo\'s domain graphs.                                              |
+-----------------------------------------------------------------------+

**B. QAOA on Graphs --- Combinatorial Optimization**

- **Max-Cut:** Partition graph nodes into two sets maximizing cut edges.
  Directly maps to portfolio diversification (cut correlated assets),
  network partitioning, supply chain zoning.

- **Graph Coloring:** Assign colours to graph nodes with no two adjacent
  same-coloured. Maps to scheduling (no two overlapping shifts/jobs),
  frequency assignment, register allocation.

- **Minimum Vertex Cover:** Find smallest set of nodes covering all
  edges. Maps to network security (minimum sensors to monitor all
  connections), drug target selection (minimum proteins to affect all
  pathways).

- **Clique Finding:** Find maximum fully connected subgraph. Maps to
  finding tightly correlated asset clusters, highly interconnected
  protein complexes, supply chain bottlenecks.

**C. Quantum Graph Neural Networks (QGNNs)**

- **Hybrid Quantum-Classical GNN:** Replace classical GNN layers with
  variational quantum circuits. Feature vectors from graph nodes →
  quantum feature map → QNN layer → output embedding. Especially
  powerful on small graphs (≤50 nodes) currently achievable on
  simulators.

- **Molecular Property Prediction:** Apply QGNN to molecular graphs
  (atoms=nodes, bonds=edges) to predict drug activity, toxicity,
  solubility. Research from IBM & University of Toronto shows
  competitive accuracy with classical GNNs on small molecules.

- **Quantum Relational Database Learning (QDML):** Research from VLDB
  2024 (Supervised Learning on Relational DBs with Quantum GNNs)
  demonstrates quantum GNNs applied to relational tables converted to
  graphs --- directly applicable to Milimo\'s experiment graphs.

- **Implementation:** qiskit-machine-learning TorchConnector +
  torch_geometric PyG library for graph construction → hybrid QGNN
  training loop.

**D. Quantum Shortest Path & Network Flow**

- **Quantum Shortest Path:** New 2024 research (arXiv:2408.10427)
  demonstrates quantum algorithms for single-pair shortest path with
  polynomial speedup over classical on structured graphs. Applied to:
  optimal reaction pathway in molecular graph, minimum-cost supply
  route, optimal qubit routing in circuit transpilation.

- **Quantum Electrical Resistance (PageRank-like):** Wang\'s quantum
  algorithm computes graph electrical resistance in poly(log n) vs
  classical poly(n) --- exponential speedup. Applied to: quantum
  PageRank on knowledge graphs, influence propagation in financial
  networks, qubit error propagation paths.

- **Min-Cut / Max-Flow:** Quantum algorithms for network flow problems
  (Ambainis 2020) offer polynomial speedup. Applied to: maximum drug
  distribution through biological network, maximum throughput supply
  chains.

**5.2 QGI Agent Architecture**

The QGI Agent operates in a four-phase cycle: extract → encode → execute
→ enrich.

  ---------------------------------------------------------------------------
  **Phase**   **Operation**            **Tools Used**        **Output**
  ----------- ------------------------ --------------------- ----------------
  1\. Extract Pull subgraph from Neo4j Neo4j + Text2Cypher   Adjacency list /
              matching user query                            node features
              (Cypher)                                       

  2\. Encode  Encode graph into        Qiskit + NetworkX +   QuantumCircuit
              quantum circuit          Numpy                 object
              (adjacency matrix, node                        
              embeddings, QUBO)                              

  3\. Execute Run quantum algorithm    Qiskit Aer / IBM      Measurement
              (walk / QAOA / QGNN) on  Runtime               results /
              Aer sim or IBM Quantum                         expectation
                                                             values

  4\. Enrich  Interpret results, write Neo4j write + LLM     Updated graph +
              enriched edges/nodes     interpretation        natural language
              back to Neo4j                                  summary
  ---------------------------------------------------------------------------

- **Natural Language Interface:** User types: \'Run quantum community
  detection on the drug-protein interaction graph for Alzheimer\'s
  research\' → QGI agent extracts relevant subgraph, encodes as quantum
  walk circuit, executes, returns community structure as both a graph
  update and a plain English summary.

- **Artifact Outputs:** Quantum circuit diagram, graph visualization
  with community/path highlights (NetworkX + Plotly), updated Neo4j
  graph, Python notebook with full reproducible pipeline.

**6. Updated System Architecture with Graph Layer**

+-----------------------------------------------------------------------+
| **Revised Architecture --- Five Layers**                              |
|                                                                       |
| Layer 1 → Presentation: React UI (unchanged)                          |
|                                                                       |
| Layer 2 → Agent Orchestration: LLM router + domain agents + NEW: QGI  |
| Agent                                                                 |
|                                                                       |
| Layer 3 → Quantum Execution: Qiskit SDK + Aer + IBM Runtime           |
| (unchanged)                                                           |
|                                                                       |
| Layer 4 → Graph Intelligence: Neo4j + FalkorDB/Graphiti + Kuzu +      |
| GDS + GraphRAG pipeline                                               |
|                                                                       |
| Layer 5 → Data & Storage: PostgreSQL (metadata) + DuckDB              |
| (analytics) + Chroma (vectors) + Neo4j                                |
+-----------------------------------------------------------------------+

**6.1 Data Flow: How Graph Connects Everything**

The graph layer acts as a connective tissue between all components of
Milimo Quantum:

- **User Query → Graphiti:** Every user message is processed by
  Graphiti\'s episode ingestion --- entities extracted, relationships
  identified, stored in the agent\'s temporal knowledge graph
  (FalkorDB).

- **Agent → Neo4j:** Domain agents query their knowledge graphs via
  Text2Cypher tool calls. Finance Agent: \'get assets correlated above
  0.7 with AAPL\'. Chemistry Agent: \'get all proteins that inhibit
  BACE1\'. Research Agent: \'find papers implementing VQE after 2023\'.

- **Quantum Result → Graph:** After every quantum job: circuit node,
  backend node, result node, error mitigation node all written to Neo4j
  as connected entities. Full experiment provenance in the graph.

- **Graph → Quantum:** QGI Agent extracts graph subsets as adjacency
  matrices / QUBO problems → sends to Qiskit for quantum execution →
  results back to graph. Closed loop.

- **Graph → LLM Context:** GraphRAG pipeline injects relevant subgraph
  summaries into LLM context window alongside standard vector RAG
  chunks. Richer, more accurate agent responses with citations to graph
  entities.

**6.2 New Technology Additions to Stack**

+----------------------------------+-----------------------------------+
| **Graph Database Components**    | **Quantum Graph Libraries**       |
|                                  |                                   |
| - Neo4j 5.26 (primary graph      | - NetworkX (classical graph       |
|   store)                         |   manipulation)                   |
|                                  |                                   |
| - Neo4j GDS 2.x (65+ graph       | - rustworkx (Qiskit\'s fast graph |
|   algorithms)                    |   library)                        |
|                                  |                                   |
| - FalkorDB 1.x (agent working    | - torch_geometric (PyG for QGNN)  |
|   memory)                        |                                   |
|                                  | - stellargraph (graph ML)         |
| - Kuzu 0.11+ (embedded local     |                                   |
|   mode)                          | - qiskit-machine-learning         |
|                                  |   (TorchConnector)                |
| - Graphiti 0.11+ (temporal agent |                                   |
|   memory)                        | - mitiq (error mitigation for     |
|                                  |   graph circuits)                 |
| - Neo4j LLM Graph Builder        |                                   |
|   (ingestion pipeline)           | - pyvis / Plotly (interactive     |
|                                  |   graph viz)                      |
| - py2neo / neo4j-driver (Python  |                                   |
|   API)                           | - node2vec (graph embeddings for  |
|                                  |   QML)                            |
| - LangChain Neo4j integration    |                                   |
+----------------------------------+-----------------------------------+

**6.3 Docker Compose Addition**

The following services are added to the existing Milimo Quantum
docker-compose.yml:

  -----------------------------------------------------------------------------------------
  **Service**         **Image**                      **Ports**          **Purpose**
  ------------------- ------------------------------ ------------------ -------------------
  neo4j               neo4j:5.26-community           7474, 7687         Primary graph
                                                                        store + GDS

  falkordb            falkordb/falkordb:latest       6379, 3000         Agent memory
                                                                        (Graphiti backend)

  graphiti            zep/graphiti-mcp:latest        8003               Temporal knowledge
                                                                        graph API

  llm-graph-builder   neo4j-labs/llm-graph-builder   8501               Knowledge graph
                                                                        ingestion UI
  -----------------------------------------------------------------------------------------

**7. Graph-Powered Use Case Scenarios**

The following end-to-end scenarios illustrate exactly how the graph
layer elevates each domain agent beyond what was previously possible.

**Scenario 1: Quantum Drug Discovery with Graph-Guided VQE**

+-----------------------------------------------------------------------+
| **The Workflow**                                                      |
|                                                                       |
| User: \'Find the most promising BACE1 inhibitor candidates from our   |
| compound library\'                                                    |
|                                                                       |
| ① QGI Agent queries Neo4j molecular graph: Cypher traversal finds 340 |
| compounds with INHIBITS edge to BACE1                                 |
|                                                                       |
| ② GDS PageRank on molecular similarity subgraph: identifies 12        |
| compounds as high-centrality hubs (structurally diverse)              |
|                                                                       |
| ③ Chemistry Agent runs VQE on all 12 via Qiskit Aer in parallel:      |
| extracts molecular energies                                           |
|                                                                       |
| ④ Results written to graph: Molecule→VQEResult edges with energy,     |
| ansatz depth, shots used                                              |
|                                                                       |
| ⑤ LLM ranks candidates by energy + centrality + prior toxicity        |
| signals from knowledge graph                                          |
|                                                                       |
| ⑥ Output: Ranked list with full graph provenance, downloadable        |
| notebook, updated molecular graph                                     |
|                                                                       |
| Previous approach (no graph): User manually provides molecules. No    |
| structural context. No cross-molecule insights.                       |
+-----------------------------------------------------------------------+

**Scenario 2: Quantum Financial Network Analysis**

+-----------------------------------------------------------------------+
| **The Workflow**                                                      |
|                                                                       |
| User: \'Identify systemically important assets in my portfolio and    |
| rebalance using quantum optimization\'                                |
|                                                                       |
| ① Finance Agent queries Neo4j: pull portfolio graph (50 assets,       |
| correlation edges from last 90 days)                                  |
|                                                                       |
| ② QGI Agent runs quantum walk PageRank on correlation graph:          |
| identifies 5 \'systemic risk\' nodes                                  |
|                                                                       |
| ③ QGI Agent formulates Max-Cut QUBO from correlation graph: partition |
| assets into uncorrelated buckets                                      |
|                                                                       |
| ④ QAOA executed on Qiskit with 5 layers: returns optimal partition    |
| with approximation ratio 0.94                                         |
|                                                                       |
| ⑤ Results: new portfolio weights written back to graph; risk          |
| reduction quantified vs classical Markowitz                           |
|                                                                       |
| ⑥ Output: visual network graph with highlighted systemic assets +     |
| rebalance recommendation                                              |
|                                                                       |
| Classical equivalent: Manual correlation matrix inspection + linear   |
| programming. No network topology insight.                             |
+-----------------------------------------------------------------------+

**Scenario 3: Quantum Supply Chain Optimisation**

+-----------------------------------------------------------------------+
| **The Workflow**                                                      |
|                                                                       |
| User: \'Optimise our European distribution network for Q4 with 12     |
| warehouses and 200 delivery points\'                                  |
|                                                                       |
| ① Optimization Agent ingests logistics data → builds graph in Neo4j   |
| (Location nodes, CONNECTS edges with distance/cost/time)              |
|                                                                       |
| ② GDS betweenness centrality: identifies 3 warehouses as critical     |
| routing hubs                                                          |
|                                                                       |
| ③ QGI Agent extracts routing QUBO from graph: vehicle routing problem |
| → QUBO formulation via Optimization Mapper Addon                      |
|                                                                       |
| ④ QAOA (p=3) on 127-qubit IBM Quantum Eagle: finds near-optimal       |
| routes across 12 warehouses                                           |
|                                                                       |
| ⑤ Route nodes + cost edges written back to Neo4j; comparison with     |
| classical CPLEX solution stored as parallel path                      |
|                                                                       |
| ⑥ Output: Interactive map overlay, cost comparison report, full       |
| circuit artifact                                                      |
+-----------------------------------------------------------------------+

**Scenario 4: Living Quantum Research Knowledge Graph**

+-----------------------------------------------------------------------+
| **The Workflow**                                                      |
|                                                                       |
| User: \'What are the latest approaches to error mitigation for VQE on |
| noisy hardware? Find gaps in the literature.\'                        |
|                                                                       |
| ① Research Agent queries Neo4j scientific knowledge graph: subgraph   |
| of Papers→Algorithm\[VQE\]→Concept\[error mitigation\]                |
|                                                                       |
| ② GDS community detection on citation graph: identifies 4 research    |
| clusters (ZNE, PEC, symmetry verification, post-selection)            |
|                                                                       |
| ③ LLM generates community summaries from Neo4j community nodes        |
| (GraphRAG global search pattern)                                      |
|                                                                       |
| ④ Gap analysis: concept nodes with few CONFIRMS edges and many        |
| PROPOSES edges = open research questions                              |
|                                                                       |
| ⑤ arXiv live ingestion checks for papers published in last 7 days;    |
| new entities auto-added to graph                                      |
|                                                                       |
| ⑥ Output: Structured literature survey with citation graph            |
| visualization, identified research gaps, arXiv links                  |
+-----------------------------------------------------------------------+

**8. Graph Integration Implementation Plan**

The graph layer is implemented across three phases, slotting into the
existing Milimo Quantum roadmap. Each phase is independently valuable
--- Phase G1 alone already dramatically improves agent quality.

**Phase G1 --- Foundation Graph Layer (Add to Phase 1-2, Months 1-4)**

+-----------------------------------------------------------------------+
| **G1 Deliverables**                                                   |
|                                                                       |
| ✓ Neo4j 5.26 + FalkorDB added to Docker Compose stack                 |
|                                                                       |
| ✓ Graphiti integrated as agent memory layer (replaces bare Chroma     |
| vector store)                                                         |
|                                                                       |
| ✓ Graph data models defined for: experiment graph, circuit topology   |
| graph, scientific knowledge graph                                     |
|                                                                       |
| ✓ Experiment pipeline writes to graph: every circuit/job/result       |
| stored as connected nodes                                             |
|                                                                       |
| ✓ Neo4j LLM Graph Builder deployed: ingest quantum papers from        |
| arXiv + user-uploaded PDFs                                            |
|                                                                       |
| ✓ Basic GraphRAG: domain agents query Neo4j for context alongside     |
| vector store                                                          |
|                                                                       |
| ✓ Graph Explorer UI panel: visual Neo4j browser embedded in Milimo    |
| right sidebar                                                         |
|                                                                       |
| ✓ Text2Cypher tool: agents can generate and execute Cypher queries    |
| via natural language                                                  |
+-----------------------------------------------------------------------+

**Phase G2 --- Domain Graph Models (Add to Phase 3, Months 5-8)**

+-----------------------------------------------------------------------+
| **G2 Deliverables**                                                   |
|                                                                       |
| ✓ Molecular knowledge graph: PubChem / ChEMBL / UniProt data imported |
| into Neo4j                                                            |
|                                                                       |
| ✓ Financial correlation graph: live market data → correlation edges   |
| updated on each job run                                               |
|                                                                       |
| ✓ Optimization logistics graph: import / export tools for user supply |
| chain data                                                            |
|                                                                       |
| ✓ Quantum Graph Intelligence Agent v1: quantum walks + QAOA-on-graphs |
| pipeline                                                              |
|                                                                       |
| ✓ QGI Agent: molecular graph → quantum walk community detection       |
|                                                                       |
| ✓ QGI Agent: financial correlation graph → QAOA Max-Cut rebalancing   |
|                                                                       |
| ✓ Graph visualization: interactive force-directed graphs in Milimo    |
| artifact panel (Plotly/D3)                                            |
|                                                                       |
| ✓ Community detection UI: Louvain communities shown as colored        |
| clusters in graph viewer                                              |
+-----------------------------------------------------------------------+

**Phase G3 --- Quantum Graph Intelligence Full Stack (Add to Phase 4,
Months 9-14)**

+-----------------------------------------------------------------------+
| **G3 Deliverables**                                                   |
|                                                                       |
| ✓ Quantum GNN (QGNN) training pipeline: torch_geometric +             |
| TorchConnector hybrid training                                        |
|                                                                       |
| ✓ QGNN molecular property predictor: active/inactive drug             |
| classification on molecular graphs                                    |
|                                                                       |
| ✓ Quantum PageRank on knowledge graphs: find most influential quantum |
| algorithms / papers                                                   |
|                                                                       |
| ✓ Quantum shortest path on molecular reaction graphs: optimal         |
| synthesis route finding                                               |
|                                                                       |
| ✓ Graph time-travel queries: \'show how experiment graph evolved over |
| last 30 days\'                                                        |
|                                                                       |
| ✓ Cross-graph reasoning: QGI Agent traverses across molecular +       |
| financial + research graphs in one query                              |
|                                                                       |
| ✓ Graph export: publish knowledge graphs as public/private datasets,  |
| integrating with Zenodo / Figshare                                    |
|                                                                       |
| ✓ Neo4j Aura cloud sync: local graph mirrors to cloud for team        |
| collaboration                                                         |
+-----------------------------------------------------------------------+

**9. Why This Makes Milimo Quantum Uniquely Powerful**

No existing quantum computing platform combines a persistent domain
knowledge graph, real-time agent memory graphs, and quantum graph
algorithms in a unified application. This combination is Milimo
Quantum\'s strongest moat.

  -------------------------------------------------------------------------------------
  **Platform**     **Vector   **Graph      **Quantum      **GraphRAG**   **Quantum
                   RAG**      Database**   Algorithms**                  Graph
                                                                         Algorithms**
  ---------------- ---------- ------------ -------------- -------------- --------------
  IBM Quantum Lab  No         No           Yes (Qiskit)   No             No

  Azure Quantum    No         No           Yes            No             No
                                           (Q#/Qiskit)                   

  Amazon Braket    No         No           Yes            No             No
                                           (multi-SDK)                   

  Classiq          No         No           Yes (Classiq   No             No
                                           lang)                         

  Generic AI       Yes        No           No             No             No
  (ChatGPT)                                                              

  Milimo Quantum   Yes        Yes          Yes (Qiskit    Yes            Yes --- FIRST
                                           v2.2)                         
  -------------------------------------------------------------------------------------

+-----------------------------------------------------------------------+
| **Summary: The New Dimensions Graph Adds**                            |
|                                                                       |
| 1\. MEMORY DIMENSION --- agents remember everything across all        |
| sessions, projects, and users (Graphiti)                              |
|                                                                       |
| 2\. RELATIONSHIP DIMENSION --- queries traverse rich multi-hop        |
| connections no SQL table can express                                  |
|                                                                       |
| 3\. KNOWLEDGE DIMENSION --- living, self-updating knowledge graphs    |
| ground agents in domain truth                                         |
|                                                                       |
| 4\. QUANTUM DIMENSION --- quantum walks, QAOA, QGNNs run directly on  |
| graph data (world first in one UI)                                    |
|                                                                       |
| 5\. PROVENANCE DIMENSION --- every experiment, circuit, and result is |
| a node in a traceable graph                                           |
|                                                                       |
| 6\. DISCOVERY DIMENSION --- GDS community detection + quantum         |
| PageRank surface non-obvious insights                                 |
+-----------------------------------------------------------------------+

*⬡ Milimo Quantum --- Where Quantum Circuits Meet Knowledge Graphs ⬡*

Neo4j · FalkorDB · Graphiti · Qiskit v2.2 · GraphRAG · Quantum Graph
Intelligence
