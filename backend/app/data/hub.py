"""Milimo Quantum — Unified Intelligence Hub.

Centralized service to fuse context from Relational (PostgreSQL), 
Graph (Memory), and Research Feeds into a single retrieved context.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict

from app.db import get_session
from app.db.models import Experiment, BenchmarkResult
from app.graph.client import graph_client
from app.quantum.vector_store import search_similar
from app.quantum.hal import hal_config
from app.feeds.arxiv import search_papers as search_arxiv
from app.feeds.finance import get_ticker_data as get_market_sentiment
from app.feeds.pubmed import search_pubmed
from app.feeds.pubchem import search_compound
import anyio

logger = logging.getLogger(__name__)

class IntelligenceHub:
    """Orchestrator for hybrid context retrieval."""

    async def get_context(
        self, 
        query: str, 
        conversation_id: str | None = None,
        agent_type: str = "general",
        limit: int = 5,
        project_id: str | None = None
    ) -> Dict[str, Any]:
        """Retrieve fused context for a query."""
        logger.info(f"Hub: Orchestrating context for query='{query}' (agent={agent_type})")
        
        # 1. Hybrid RAG (Graph + Vector)
        is_qgi = agent_type == "qgi"
        is_history_query = any(kw in query.lower() for kw in ["last session", "previous", "history", "memory", "what did i do"])
        
        # A. Relational/Episodic Graph Memory via Unified Client
        # We query the unified graph client which supports Neo4j, Falkor, and Kuzu
        graph_memories = await graph_client.query_related(query, limit=limit, project_id=project_id)
        
        # If project_id provided, filter results to this project's graph traversal if possible
        # (Future optimization: pass pid to query_related)
        
        # B. Semantic Vector Memory (ChromaDB)
        vector_results = []
        try:
            vector_data = search_similar(query, n_results=limit, project_id=project_id)
            if "results" in vector_data:
                vector_results = vector_data["results"]
        except Exception as e:
            logger.debug(f"Vector search failed: {e}")
        
        # 2. Research Context (ArXiv/Finance)
        research = []
        if any(kw in query.lower() for kw in ["paper", "research", "arxiv", "latest", "study"]):
            arxiv_results = await search_arxiv(query)
            research.extend(arxiv_results[:2])
            
        if any(kw in query.lower() for kw in ["market", "stock", "sentiment", "finance", "price"]):
            market = await anyio.to_thread.run_sync(get_market_sentiment, "QUANTUM") # Default to quantum sector
            research.append({"type": "market_sentiment", "data": market})
            
        if any(kw in query.lower() for kw in ["medicine", "drug", "disease", "medical", "pubmed"]):
            pubmed_results = await anyio.to_thread.run_sync(search_pubmed, query, 2)
            for p in pubmed_results:
                research.append({"type": "pubmed", "data": p})

        if any(kw in query.lower() for kw in ["molecule", "compound", "chemistry", "pubchem", "protein"]):
            # Robust extraction: look for target compound name
            potential_compound = ""
            # Try to find a known molecule from our dictionary first
            from app.agents.context_enricher import _MOLECULES
            for key, canonical in _MOLECULES.items():
                if key in query.lower():
                    potential_compound = canonical
                    break
            
            if not potential_compound:
                # Fallback: look for the last word or specific patterns
                match = re.search(r'(?:formula for|about|simulating|of|molecule)\s+([a-zA-Z0-9]+)', query, re.IGNORECASE)
                if match:
                    potential_compound = match.group(1)
                else:
                    # Very simple fallback
                    words = query.strip().rstrip('?.!').split()
                    potential_compound = words[-1] if words else ""
            
            if potential_compound:
                compound = await search_compound(potential_compound)
                if compound:
                    research.append({"type": "molecule_data", "data": compound})

        # 3. SQL Context (Experiments & Benchmarks)
        past_exps = []
        benchmarks = []
        with get_session() as session:
            q_term = f"%{query}%"
            # Past Experiments - Scoped by project_id
            exp_query = session.query(Experiment).filter(
                (Experiment.name.ilike(q_term)) | 
                (Experiment.backend.ilike(q_term))
            )
            if project_id:
                exp_query = exp_query.filter(Experiment.project_id == project_id)
            
            exps = exp_query.limit(limit).all()
            past_exps = [
                {
                    "id": e.id, "name": e.name, "backend": e.backend,
                    "results": e.results, "timestamp": e.created_at.isoformat()
                } for e in exps
            ]

            # Benchmarks (Performance Context)
            if any(kw in query.lower() for kw in ["performance", "speed", "clops", "advantage", "benchmark"]):
                b_results = session.query(BenchmarkResult).limit(2).all()
                benchmarks = [
                    {
                        "name": b.benchmark_name, "backend": b.backend,
                        "prepare": b.preparation_time, "exec": b.quantum_exec_time
                    } for b in b_results
                ]

        return {
            "graph_memory": graph_memories,
            "vector_memory": vector_results,
            "research": research,
            "past_experiments": past_exps,
            "benchmarks": benchmarks,
            "hardware": {
                "os": hal_config.os_name,
                "arch": hal_config.arch,
                "gpu": hal_config.gpu_available,
                "gpu_name": hal_config.gpu_name,
                "device": hal_config.torch_device
            },
            "query": query,
            "fused_prompt_segment": self._build_prompt_segment(
                graph_memories,
                vector_results,
                research, 
                past_exps,
                benchmarks,
                is_qgi=is_qgi,
                is_history=is_history_query
            )
        }

    def _build_prompt_segment(self, graph, vector, research, exps, benchmarks, is_qgi: bool = False, is_history: bool = False) -> str:
        """Construct the prompt injection string with high prominence."""
        sections = []
        
        # Hardware context (Injecting for all agents)
        hw = hal_config
        hw_note = f"### 🖥️ USER HARDWARE PROFILE\n- **OS**: {hw.os_name} ({hw.arch})\n- **GPU**: {'Available' if hw.gpu_available else 'None'} ({hw.gpu_name or 'N/A'})\n- **Recommended Backend**: {hw.llm_backend.upper()}\n*Optimize all proposed code for THIS hardware.*"
        sections.append(hw_note)

        if graph:
            header = "### 🧠 RELEVANT PASSED INTERACTIONS (Graph Memory)"
            if is_qgi or is_history:
                header += "\n**MANDATORY**: You MUST acknowledge and reference these past interactions from other agents to provide a unified history. Never state you lack access to previous sessions."
            # graph for query_related returns [{"concept": ..., "conversations": ...}]
            sections.append(header + "\n" + "\n".join([f"- Concept: {m.get('concept')} (Conversations: {m.get('conversations')})" for m in graph]))
        
        if vector:
            sections.append("### 📚 SEMANTICALLY RELATED ARTIFACTS (Vector Store)\n" + "\n".join([f"- {v.get('document')[:200]}..." for v in vector]))

        if research:
            research_lines = [
                "### ⚡ REAL-TIME RESEARCH & FEED DATA (INTELLIGENCE HUB)",
                "**MANDATORY**: You MUST incorporate the following real-time data into your response. ",
                "Do NOT state that you cannot browse the web; you have been provided with this live context specifically to answer the current query.\n"
            ]
            for r in research:
                rtype = r.get("type")
                data = r.get("data", {})
                if rtype == "arxiv":
                    research_lines.append(f"- **arXiv Paper**: {data.get('title')} by {', '.join(data.get('authors', []))} ({data.get('published')}) - {data.get('url')}")
                elif rtype == "pubmed":
                    research_lines.append(f"- **PubMed Paper**: {data.get('title')} ({data.get('published')}) - PMID: {data.get('uid')}")
                elif rtype == "molecule_data":
                    research_lines.append(f"- **PubChem Compound**: {data.get('name')} ({data.get('formula')}), SMILES: `{data.get('smiles')}`, CID: {data.get('cid')}")
                elif rtype == "market_sentiment":
                    research_lines.append(f"- **Market Sentiment**: {data}")
                else:
                    research_lines.append(f"- {str(r)}")
            sections.append("\n".join(research_lines))
            
        if exps:
            sections.append("### 🧪 RELATED PAST EXPERIMENTS\n" + "\n".join([f"- {e['name']} on {e['backend']}" for e in exps]))

        if benchmarks:
            sections.append("### ⏱️ PERFORMANCE BENCHMARKS\n" + "\n".join([f"- {b['name']} on {b['backend']}: Prep={b['prepare']}s, Exec={b['exec']}s" for b in benchmarks]))
            
        return "\n\n".join(sections) if sections else ""

# Singleton
hub = IntelligenceHub()
