"""Milimo Quantum — Unified Intelligence Hub.

Centralized service to fuse context from Relational (PostgreSQL), 
Graph (Memory), and Research Feeds into a single retrieved context.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from app.db import get_session
from app.db.models import Conversation, Experiment
from app.graph.agent_memory import agent_memory
from app.agents.arxiv import search_arxiv
from app.agents.finance import get_market_sentiment
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
        limit: int = 5
    ) -> Dict[str, Any]:
        """Retrieve fused context for a query."""
        logger.info(f"Hub: Orchestrating context for query='{query}' (agent={agent_type})")
        
        # 1. Episodic Graph Memory (GraphRAG)
        graph_memories = await agent_memory.retrieve_context(agent_type, query, limit=limit)
        
        # 2. Research Context (ArXiv/Finance)
        research = []
        if any(kw in query.lower() for kw in ["paper", "research", "arxiv", "latest", "study"]):
            arxiv_results = await search_arxiv(query)
            research.extend(arxiv_results[:2])
            
        if any(kw in query.lower() for kw in ["market", "stock", "sentiment", "finance", "price"]):
            market = await get_market_sentiment("QUANTUM") # Default to quantum sector
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
                compound = await anyio.to_thread.run_sync(search_compound, potential_compound)
                if compound:
                    research.append({"type": "molecule_data", "data": compound})

        # 3. Relational Context (Past Experiments/Conversations)
        past_exps = []
        with get_session() as session:
            # Simple keyword search on experiments for now
            q_term = f"%{query}%"
            exps = session.query(Experiment).filter(
                (Experiment.name.ilike(q_term)) | 
                (Experiment.backend.ilike(q_term))
            ).limit(2).all()
            past_exps = [
                {
                    "id": e.id,
                    "name": e.name,
                    "backend": e.backend,
                    "results": e.results,
                    "timestamp": e.created_at.isoformat()
                }
                for e in exps
            ]

        return {
            "graph_memory": graph_memories,
            "research": research,
            "past_experiments": past_exps,
            "query": query,
            "fused_prompt_segment": self._build_prompt_segment(graph_memories, research, past_exps)
        }

    def _build_prompt_segment(self, graph, research, exps) -> str:
        """Construct the prompt injection string."""
        sections = []
        
        if graph:
            sections.append("### Relevant Past Interactions\n" + "\n".join([f"- {m['content']}" for m in graph]))
        
        if research:
            research_lines = ["### Latest Research & Market Context"]
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
            sections.append("### Related Past Experiments\n" + "\n".join([f"- {e['name']} on {e['backend']}" for e in exps]))
            
        return "\n\n".join(sections) if sections else ""

# Singleton
hub = IntelligenceHub()
