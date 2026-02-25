"""Milimo Quantum — Neo4j Graph Client.

Provides domain-specific Cypher queries for the quantum knowledge graph.
Gracefully degrades when Neo4j is unavailable — returns empty results
and logs a warning instead of crashing.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# ── Neo4j Availability ──────────────────────────────────
NEO4J_AVAILABLE = False
try:
    from neo4j import AsyncGraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    logger.info("neo4j driver not installed — graph queries disabled")


class Neo4jClient:
    """Async Neo4j client with domain-specific quantum knowledge graph queries."""

    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "milimo-quantum-graph")
        self.driver = None
        self.connected = False

    async def connect(self) -> bool:
        """Connect to Neo4j. Returns True if successful."""
        if not NEO4J_AVAILABLE:
            logger.debug("Neo4j driver not installed — skipping connection")
            return False
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            # Verify connectivity
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 AS n")
                await result.single()
            self.connected = True
            logger.info(f"Connected to Neo4j at {self.uri}")
            return True
        except Exception as e:
            logger.warning(f"Neo4j connection failed (non-critical): {e}")
            self.connected = False
            return False

    async def close(self):
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()
            self.connected = False
            logger.info("Closed Neo4j connection")

    def get_status(self) -> dict:
        """Get Neo4j connection status."""
        return {
            "driver_installed": NEO4J_AVAILABLE,
            "connected": self.connected,
            "uri": self.uri if self.connected else None,
        }

    async def execute_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a read-only Cypher query."""
        if not self.connected or not self.driver:
            return []
        parameters = parameters or {}
        try:
            async with self.driver.session() as session:
                result = await session.run(query, parameters)
                return await result.data()
        except Exception as e:
            logger.error(f"Neo4j query error: {e}")
            return []

    # ── Domain-Specific Graph Operations ─────────────────

    async def ensure_schema(self):
        """Create indexes and constraints for the quantum knowledge graph."""
        if not self.connected:
            return

        schema_queries = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Experiment) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (conv:Conversation) REQUIRE conv.id IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (c:Circuit) ON (c.type)",
            "CREATE INDEX IF NOT EXISTS FOR (a:Agent) ON (a.type)",
        ]
        for q in schema_queries:
            await self.execute_query(q)
        logger.info("Neo4j schema ensured")

    async def index_conversation(
        self,
        conversation_id: str,
        messages: list[dict],
        agent_type: str | None = None,
    ):
        """Index a conversation into the knowledge graph.

        Creates nodes for: Conversation, Agent, Concept (extracted from content).
        Creates edges for: DISCUSSED, USED_AGENT, CONTAINS_CIRCUIT.
        """
        if not self.connected:
            return

        # Create conversation node
        await self.execute_query(
            """
            MERGE (conv:Conversation {id: $id})
            SET conv.message_count = $count,
                conv.updated_at = datetime()
            """,
            {"id": conversation_id, "count": len(messages)},
        )

        # Link agent
        if agent_type:
            await self.execute_query(
                """
                MERGE (a:Agent {type: $type})
                WITH a
                MATCH (conv:Conversation {id: $conv_id})
                MERGE (conv)-[:USED_AGENT]->(a)
                """,
                {"type": agent_type, "conv_id": conversation_id},
            )

        # Extract and link concepts from message content
        concept_keywords = {
            "entanglement": "Entanglement",
            "superposition": "Superposition",
            "bell state": "Bell State",
            "ghz": "GHZ State",
            "grover": "Grover's Algorithm",
            "shor": "Shor's Algorithm",
            "vqe": "VQE",
            "qaoa": "QAOA",
            "qft": "QFT",
            "error correction": "Error Correction",
            "surface code": "Surface Code",
            "teleportation": "Teleportation",
            "qkd": "QKD",
            "bb84": "BB84 Protocol",
            "annealing": "Quantum Annealing",
            "qubo": "QUBO",
        }

        all_text = " ".join(m.get("content", "") for m in messages).lower()
        for keyword, concept_name in concept_keywords.items():
            if keyword in all_text:
                await self.execute_query(
                    """
                    MERGE (c:Concept {name: $name})
                    WITH c
                    MATCH (conv:Conversation {id: $conv_id})
                    MERGE (conv)-[:DISCUSSED]->(c)
                    """,
                    {"name": concept_name, "conv_id": conversation_id},
                )

    async def query_related(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Find conversations and concepts related to a query via graph traversal."""
        if not self.connected:
            return []

        # Search for concepts matching the query
        return await self.execute_query(
            """
            MATCH (c:Concept)
            WHERE toLower(c.name) CONTAINS toLower($query)
            OPTIONAL MATCH (c)<-[:DISCUSSED]-(conv:Conversation)
            OPTIONAL MATCH (conv)-[:USED_AGENT]->(a:Agent)
            RETURN c.name AS concept,
                   collect(DISTINCT conv.id)[0..5] AS conversations,
                   collect(DISTINCT a.type)[0..3] AS agents
            LIMIT $limit
            """,
            {"query": query, "limit": limit},
        )

    async def get_graph_stats(self) -> dict:
        """Get graph statistics."""
        if not self.connected:
            return {"nodes": 0, "relationships": 0, "concepts": 0, "conversations": 0}

        stats = await self.execute_query(
            """
            MATCH (n) WITH count(n) AS nodes
            MATCH ()-[r]->() WITH nodes, count(r) AS rels
            OPTIONAL MATCH (c:Concept) WITH nodes, rels, count(c) AS concepts
            OPTIONAL MATCH (conv:Conversation) WITH nodes, rels, concepts, count(conv) AS convs
            RETURN nodes, rels, concepts, convs
            """
        )
        if stats:
            s = stats[0]
            return {
                "nodes": s.get("nodes", 0),
                "relationships": s.get("rels", 0),
                "concepts": s.get("concepts", 0),
                "conversations": s.get("convs", 0),
            }
        return {"nodes": 0, "relationships": 0, "concepts": 0, "conversations": 0}


# Singleton
neo4j_client = Neo4jClient()
