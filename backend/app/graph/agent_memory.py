"""Milimo Quantum — Agent Memory System.

Provides per-agent episodic memory with a local JSON fallback when
FalkorDB/Graphiti are unavailable. Stores past interactions, preferences,
and context that can be injected into agent system prompts.
"""
from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MEMORY_DIR = Path.home() / ".milimoquantum" / "agent_memory"


class AgentMemory:
    """Agent episodic memory with local JSON fallback.

    Each agent type has its own memory store. Memories are keyed by
    conversation_id and include content, metadata, and timestamps.
    When FalkorDB is available, memories are also stored in the graph
    for cross-conversation retrieval via GraphRAG.
    """

    def __init__(self):
        self.host = os.getenv("FALKORDB_HOST", "localhost")
        self.port = int(os.getenv("FALKORDB_PORT", 6379))
        self.use_graph = False  # FalkorDB connection status

        # Local memory store: agent_type → list of memory entries
        self._local: dict[str, list[dict]] = defaultdict(list)
        self._load_local()

    def _load_local(self):
        """Load persisted memories from disk."""
        if not MEMORY_DIR.exists():
            return
        for filepath in MEMORY_DIR.glob("*.json"):
            try:
                agent_type = filepath.stem
                data = json.loads(filepath.read_text(encoding="utf-8"))
                self._local[agent_type] = data
            except (json.JSONDecodeError, OSError):
                continue
        total = sum(len(v) for v in self._local.values())
        if total:
            logger.info(f"Loaded {total} agent memory entries from disk")

    def _save_agent(self, agent_type: str):
        """Save a single agent's memories to disk."""
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        filepath = MEMORY_DIR / f"{agent_type}.json"
        try:
            filepath.write_text(
                json.dumps(self._local[agent_type], indent=2, default=str),
                encoding="utf-8",
            )
        except OSError as e:
            logger.error(f"Failed to save memory for {agent_type}: {e}")

    async def connect(self) -> bool:
        """Try to connect to FalkorDB for graph-enhanced memory."""
        try:
            import falkordb  # noqa: F401
            # Would initialize FalkorDB connection here
            self.use_graph = False  # Keep off until fully wired
            logger.info("FalkorDB available but using local memory for now")
            return False
        except ImportError:
            self.use_graph = False
            logger.debug("FalkorDB not installed — using local JSON memory")
            return False

    async def add_memory(
        self,
        agent_type: str,
        conversation_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        memory_type: str = "interaction",
    ):
        """Store an episodic memory for an agent.

        Args:
            agent_type: The agent that created this memory (e.g., 'code', 'research')
            conversation_id: The conversation this memory belongs to
            content: The content to remember (summary, key fact, preference)
            metadata: Additional metadata (circuit type, qubit count, etc.)
            memory_type: Type of memory: interaction, preference, result, insight
        """
        entry = {
            "conversation_id": conversation_id,
            "content": content[:2000],  # Cap content length
            "metadata": metadata or {},
            "memory_type": memory_type,
            "timestamp": time.time(),
        }

        # Add to local store
        self._local[agent_type].append(entry)

        # Keep only last 200 entries per agent
        if len(self._local[agent_type]) > 200:
            self._local[agent_type] = self._local[agent_type][-200:]

        # Persist
        self._save_agent(agent_type)
        logger.debug(f"[{agent_type}] Stored memory: {content[:60]}...")

    async def retrieve_context(
        self,
        agent_type: str,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant context for an agent's current query.

        Uses simple keyword matching on local store.
        When FalkorDB is available, uses GraphRAG for semantic retrieval.
        """
        memories = self._local.get(agent_type, [])
        if not memories:
            return []

        # Simple keyword relevance scoring
        query_words = set(query.lower().split())
        scored = []
        for mem in memories:
            content_words = set(mem["content"].lower().split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                scored.append((overlap, mem))

        # Sort by relevance (descending), then recency
        scored.sort(key=lambda x: (x[0], x[1].get("timestamp", 0)), reverse=True)
        return [m for _, m in scored[:limit]]

    async def get_context_prompt(
        self, agent_type: str, query: str, max_chars: int = 1000
    ) -> str:
        """Build a context injection string for agent system prompts.

        Returns a short summary of relevant past interactions that
        can be appended to the agent's system prompt.
        """
        context = await self.retrieve_context(agent_type, query, limit=3)
        if not context:
            return ""

        lines = ["Relevant context from past interactions:"]
        char_count = 0
        for mem in context:
            line = f"- [{mem['memory_type']}] {mem['content'][:300]}"
            if char_count + len(line) > max_chars:
                break
            lines.append(line)
            char_count += len(line)

        return "\n".join(lines)

    def get_status(self) -> dict:
        """Get memory system status."""
        return {
            "backend": "falkordb" if self.use_graph else "local_json",
            "agents_with_memory": list(self._local.keys()),
            "total_entries": sum(len(v) for v in self._local.values()),
            "storage_dir": str(MEMORY_DIR),
        }

    def get_agent_stats(self) -> dict[str, int]:
        """Get per-agent memory counts."""
        return {k: len(v) for k, v in self._local.items() if v}


# Singleton
agent_memory = AgentMemory()
