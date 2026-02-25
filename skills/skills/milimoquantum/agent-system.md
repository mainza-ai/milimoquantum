---
description: Agent system — 14 specialized agents with orchestration, intent routing, tool registry, and domain-specific system prompts
---

# Agent System Skill

## Agent Roster (14 Total)

### Core Agents (Phase 1)
1. **Orchestrator** — routes all user queries to the right agent via intent classification
2. **Code Agent** — Qiskit code generation, circuit execution, visualization
3. **Research Agent** — quantum concepts, education, arXiv search

### Domain Agents (Phase 2+)
4. **Planning Agent** — multi-step pipeline builder for complex tasks
5. **Chemistry Agent** — VQE, molecular simulation, drug discovery (qiskit-nature)
6. **Finance Agent** — portfolio optimization (QAOA), risk analysis (qiskit-finance)
7. **Crypto Agent** — BB84 QKD simulation, QRNG, post-quantum crypto
8. **QML Agent** — quantum neural networks, QSVM, kernel methods
9. **Optimization Agent** — QAOA, VQE, combinatorial problems, D-Wave integration
10. **Climate/Science Agent** — environmental modeling, quantum advantage analysis
11. **QGI Agent** — Quantum Graph Intelligence, graph → circuit encoding via Neo4j
12. **Sensing Agent** — atom interferometry, NV-center magnetometry, quantum LiDAR
13. **Networking Agent** — SquidASM/NetSquid, quantum repeater chains
14. **D-Wave Annealing Agent** — QUBO formulation, minorminer embedding, hybrid solvers

## Intent Classification Pipeline

```
1. Slash command detection: /code, /research, /chemistry, /finance, /optimize
   → Direct routing, no LLM needed

2. Keyword matching (fast path):
   - "circuit", "code", "qiskit", "bell", "ghz", "qft" → Code Agent
   - "explain", "what is", "concept", "learn" → Research Agent
   - "molecule", "drug", "vqe", "protein" → Chemistry Agent
   - "portfolio", "stock", "risk", "option" → Finance Agent
   - "optimize", "qaoa", "combinatorial", "tsp" → Optimization Agent

3. LLM-based classification (fallback):
   → Send user message + agent descriptions to LLM
   → LLM returns agent type
```

## Agent System Prompt Pattern

```python
SYSTEM_PROMPTS = {
    AgentType.ORCHESTRATOR: """You are Milimo Quantum, a quantum computing AI assistant.
        You help users understand quantum computing, write Qiskit code, and run simulations.
        Use Markdown with LaTeX notation (e.g., |ψ⟩ = α|0⟩ + β|1⟩).
        When users ask about circuits, generate Qiskit code.""",
    AgentType.CODE: """You are the Code Agent. Generate executable Qiskit code.
        Always include: imports, circuit creation, transpilation, execution, result display.
        Use the latest Qiskit v1.4 API (QuantumCircuit, transpile, AerSimulator).""",
    AgentType.RESEARCH: """You are the Research Agent. Explain quantum concepts clearly.
        Use analogies, diagrams, and LaTeX notation.
        Reference original papers when applicable.""",
}
```

## Agent Response Structure

Each agent returns:
- **Streamed text** — markdown formatted explanation
- **Artifacts** — typed objects (code, circuit, results, notebook, report)
- **Metadata** — execution time, backend used, qubit count, depth

## SSE Event Protocol

```
event: token
data: {"content": "partial text..."}

event: artifact
data: {"id": "...", "type": "code|circuit|results", "title": "...", "content": "..."}

event: done
data: {"conversation_id": "...", "agent": "code"}
```
