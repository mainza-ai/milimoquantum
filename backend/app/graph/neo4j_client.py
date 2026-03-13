"""Milimo Quantum — Neo4j Graph Client.

Provides domain-specific Cypher queries for the quantum knowledge graph.
Gracefully degrades when Neo4j is unavailable — returns empty results
and logs a warning instead of crashing.
"""
from __future__ import annotations

import logging
import os
import datetime
from typing import Any
import json

logger = logging.getLogger(__name__)

async def extract_concepts_with_llm(text: str) -> list[str]:
    """Extract quantum concepts from text using LLM, with fallback to basic noun chunks."""
    try:
        from app.llm.ollama_client import ollama_client
        prompt = f"Extract all quantum computing concepts, algorithms, named techniques, and scientific entities from the following text. Return ONLY a JSON array of lowercase strings. Text: {text[:2000]}"
        response = await ollama_client.generate(prompt=prompt, system_prompt="You are a JSON entity extractor. Return ONLY a JSON array of strings.")
        
        start = response.find('[')
        end = response.rfind(']')
        if start != -1 and end != -1:
            concepts = json.loads(response[start:end+1])
            if isinstance(concepts, list):
                return [str(c).lower() for c in concepts]
    except Exception as e:
        logger.warning(f"LLM concept extraction failed: {e}")
        
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        return list(set(chunk.text.lower() for chunk in doc.noun_chunks if len(chunk.text) > 3))
    except Exception:
        return ["quantum", "algorithm"]


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
        self.password = os.getenv("NEO4J_PASSWORD", "milimopassword")
        
        if not self.password and NEO4J_AVAILABLE:
            logger.warning("NEO4J_PASSWORD is not set in the environment.")
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
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (c:Circuit) ON (c.type)",
            "CREATE INDEX IF NOT EXISTS FOR (a:Agent) ON (a.type)",
        ]
        for q in schema_queries:
            await self.execute_query(q)
        logger.info("Neo4j schema ensured")

    async def index_artifact(self, artifact_id: str, message_id: str, conversation_id: str, code: str, result_metadata: dict):
        """Index a generated artifact (circuit code) into the knowledge graph."""
        if not self.connected:
            return
        try:
            # TODO: add index
            await self.execute_query(
                """
                MERGE (a:Artifact {id: $art_id, code: $code})
                WITH a
                MATCH (m:Message {id: $msg_id})
                MATCH (conv:Conversation {id: $conv_id})
                MERGE (m)-[:PRODUCED]->(a)
                MERGE (a)-[:BELONGS_TO]->(conv)
                WITH a, conv
                MATCH (conv)-[:DISCUSSED]->(c:Concept)
                MERGE (a)-[:DEMONSTRATES]->(c)
                """,
                {"art_id": artifact_id, "code": code, "msg_id": message_id, "conv_id": conversation_id}
            )
        except Exception as e:
            logger.warning(f"Neo4j failed to index artifact: {e}")

    async def index_conversation(
        self,
        conversation_id: str,
        messages: list[dict],
        agent_type: str | None = None,
        user_id: str = "default",
        message_id: str = "none",
        message_timestamp: str = "",
        project_id: str | None = None
    ):
        """Index a conversation into the knowledge graph."""
        if not self.connected:
            return

        try:
            # Create project, conversation & user node
            # TODO: add index
            await self.execute_query(
                """
                MERGE (u:User {id: $user_id})
                MERGE (conv:Conversation {id: $conv_id})
                SET conv.message_count = $count,
                    conv.updated_at = datetime()
                MERGE (u)-[:PARTICIPATED_IN]->(conv)
                WITH conv
                WHERE $project_id IS NOT NULL
                MERGE (p:Project {id: $project_id})
                MERGE (p)-[:CONTAINS]->(conv)
                """,
                {"conv_id": conversation_id, "count": len(messages), "user_id": user_id, "project_id": project_id},
            )

            # Create message node for granularity
            timestamp_val = message_timestamp or str(datetime.datetime.utcnow())
            # TODO: add index
            await self.execute_query(
                """
                MATCH (conv:Conversation {id: $conv_id})
                MERGE (m:Message {id: $msg_id, timestamp: $ts, role: 'assistant'})
                MERGE (conv)-[:HAS_MESSAGE]->(m)
                """,
                {"conv_id": conversation_id, "msg_id": message_id, "ts": timestamp_val}
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
            all_text = " ".join(m.get("content", "") for m in messages).lower()
            concepts = await extract_concepts_with_llm(all_text)

            for concept_name in concepts:
                # TODO: add index
                await self.execute_query(
                    """
                    MATCH (conv:Conversation {id: $conv_id})
                    MATCH (m:Message {id: $msg_id})
                    MATCH (u:User {id: $user_id})
                    MERGE (c:Concept {name: $name})
                    MERGE (conv)-[:DISCUSSED]->(c)
                    MERGE (m)-[:SURFACED]->(c)
                    MERGE (u)-[:EXPLORED]->(c)
                    """,
                    {"name": concept_name, "conv_id": conversation_id, "msg_id": message_id, "user_id": user_id},
                )
                
            # Example query for Top 5 concepts by user:
            # MATCH (:User {id: $uid})-[:EXPLORED]->(c:Concept) RETURN c.name, count(*) AS freq ORDER BY freq DESC LIMIT 5
            # Example query for temporal concept retrieval:
            # MATCH (conv:Conversation {id: $cid})-[:HAS_MESSAGE]->(m:Message)-[:SURFACED]->(c:Concept) RETURN m.timestamp, c.name ORDER BY m.timestamp ASC
        except Exception as e:
            logger.warning(f"Neo4j conversation index failed: {e}")

    async def query_related(
        self, query: str, limit: int = 10, project_id: str | None = None
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
            WHERE $project_id IS NULL OR conv.project_id = $project_id
            OPTIONAL MATCH (conv)-[:USED_AGENT]->(a:Agent)
            RETURN c.name AS concept,
                   collect(DISTINCT conv.id)[0..5] AS conversations,
                   collect(DISTINCT a.type)[0..3] AS agents
            LIMIT $limit
            """,
            {"query": query, "limit": limit, "project_id": project_id},
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
