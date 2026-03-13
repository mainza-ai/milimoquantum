"""Milimo Quantum - Unified Graph Interface.

Supports Neo4j, FalkorDB, and Kuzu connections for GraphRAG.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

class UnifiedGraphClient:
    """Unified interface for quantum knowledge graph operations across multiple DBs."""
    
    def __init__(self):
        self.active_provider = os.getenv("GRAPH_PROVIDER", "neo4j")
        self.falkor_available = False
        self.kuzu_available = False
        
        # We start by initializing Neo4j using the existing client
        self.neo4j = neo4j_client
        
        # Check module availability
        try:
            import importlib.util
            if importlib.util.find_spec("falkordb"):
                self.falkor_available = True
            self.falkor_driver = None
        except ImportError:
            pass
            
        try:
            import importlib.util
            if importlib.util.find_spec("kuzu"):
                self.kuzu_available = True
            self.kuzu_db = None
            self.kuzu_conn = None
        except ImportError:
            pass
            
    async def connect(self) -> bool:
        """Connect to the configured active graph database provider."""
        if self.active_provider == "neo4j":
            return await self.neo4j.connect()
        elif self.active_provider == "falkordb" and self.falkor_available:
            try:
                import falkordb
                self.falkor_driver = falkordb.FalkorDB().select_graph("milimo_quantum")
                logger.info("Connected to FalkorDB graph 'milimo_quantum'")
                return True
            except Exception as e:
                logger.warning(f"FalkorDB connection failed: {e}")
                return False
        elif self.active_provider == "kuzu" and self.kuzu_available:
            try:
                import kuzu
                os.makedirs("data/kuzu", exist_ok=True)
                self.kuzu_db = kuzu.Database("data/kuzu")
                self.kuzu_conn = kuzu.Connection(self.kuzu_db)
                logger.info("Connected to Kuzu Embedded Graph at data/kuzu")
                return True
            except Exception as e:
                logger.warning(f"Kuzu connection failed: {e}")
                return False
        
        # Fallback to simulated connection if no valid provider
        return True
        
    async def close(self):
        """Close connections."""
        if self.active_provider == "neo4j":
            await self.neo4j.close()
        elif self.active_provider == "falkordb" and self.falkor_driver:
            # FalkorDB connection closed automatically when python drops object or via redis pool
            self.falkor_driver = None
        elif self.active_provider == "kuzu" and self.kuzu_conn:
            self.kuzu_conn.close()
            self.kuzu_conn = None
            self.kuzu_db = None

    def get_status(self) -> dict:
        """Get the connection status across all supported graph DBs."""
        neo4j_status = self.neo4j.get_status()
        
        return {
            "active_provider": self.active_provider,
            "connected": True if (self.active_provider == "neo4j" and neo4j_status.get("connected", False)) or (self.active_provider == "falkordb" and self.falkor_driver) else False,
            "providers": {
                "neo4j": {
                    "installed": neo4j_status.get("driver_installed", False),
                    "connected": neo4j_status.get("connected", False),
                },
                "falkordb": {
                    "installed": self.falkor_available,
                    "connected": bool(self.falkor_driver),
                },
                "kuzu": {
                    "installed": self.kuzu_available,
                    "connected": bool(self.kuzu_conn),
                }
            }
        }

    async def ensure_schema(self):
        """Ensure schema exists on active provider."""
        if self.active_provider == "neo4j":
            await self.neo4j.ensure_schema()
        elif self.active_provider == "falkordb" and self.falkor_driver:
            # FalkorDB creates schema automatically on merge, but we can set constraints
            try:
                self.falkor_driver.query("CREATE INDEX ON :Concept(name)")
                self.falkor_driver.query("CREATE INDEX ON :Conversation(id)")
                self.falkor_driver.query("CREATE INDEX ON :Agent(type)")
            except Exception:
                pass
        elif self.active_provider == "kuzu" and self.kuzu_conn:
            try:
                # Kuzu requires explicit table creation
                self.kuzu_conn.execute("CREATE NODE TABLE IF NOT EXISTS Conversation (id STRING, message_count INT64, PRIMARY KEY (id))")
                self.kuzu_conn.execute("CREATE NODE TABLE IF NOT EXISTS Agent (type STRING, PRIMARY KEY (type))")
                self.kuzu_conn.execute("CREATE NODE TABLE IF NOT EXISTS Concept (name STRING, PRIMARY KEY (name))")
                self.kuzu_conn.execute("CREATE REL TABLE IF NOT EXISTS USED_AGENT (FROM Conversation TO Agent)")
                self.kuzu_conn.execute("CREATE REL TABLE IF NOT EXISTS DISCUSSED (FROM Conversation TO Concept)")
            except Exception as e:
                logger.error(f"Kuzu schema error: {e}")
            
    async def index_conversation(self, conversation_id: str, messages: list[dict], agent_type: str | None = None, project_id: str | None = None):
        """Index a conversation to the active graph DB."""
        if self.active_provider == "neo4j":
            await self.neo4j.index_conversation(conversation_id, messages, agent_type, project_id=project_id)
        elif self.active_provider == "falkordb" and self.falkor_driver:
            try:
                params = {"id": conversation_id, "count": len(messages)}
                self.falkor_driver.query("MERGE (conv:Conversation {id: $id}) SET conv.message_count = $count", params)
                if agent_type:
                    self.falkor_driver.query("MERGE (a:Agent {type: $type})", {"type": agent_type})
                    self.falkor_driver.query("MATCH (conv:Conversation {id: $id}), (a:Agent {type: $type}) MERGE (conv)-[:USED_AGENT]->(a)", {"id": conversation_id, "type": agent_type})
                
                # Extract simple concepts
                all_text = " ".join(m.get("content", "") for m in messages).lower()
                for keyword, concept_name in {"entanglement": "Entanglement", "vqe": "VQE", "qaoa": "QAOA"}.items():
                    if keyword in all_text:
                        self.falkor_driver.query("MERGE (c:Concept {name: $name})", {"name": concept_name})
                        self.falkor_driver.query("MATCH (conv:Conversation {id: $id}), (c:Concept {name: $name}) MERGE (conv)-[:DISCUSSED]->(c)", {"id": conversation_id, "name": concept_name})
            except Exception as e:
                logger.error(f"FalkorDB index error: {e}")
        elif self.active_provider == "kuzu" and self.kuzu_conn:
            try:
                 # Kuzu MERGE syntax
                 self.kuzu_conn.execute("MERGE (conv:Conversation {id: $id}) ON CREATE SET conv.message_count = $count ON MATCH SET conv.message_count = $count", {"id": conversation_id, "count": len(messages)})
                 if agent_type:
                     self.kuzu_conn.execute("MERGE (a:Agent {type: $type})", {"type": agent_type})
                     self.kuzu_conn.execute("MATCH (conv:Conversation {id: $id}), (a:Agent {type: $type}) MERGE (conv)-[:USED_AGENT]->(a)", {"id": conversation_id, "type": agent_type})
            except Exception as e:
                 logger.error(f"Kuzu index error: {e}")
            
    async def index_artifact(self, artifact_id: str, message_id: str, conversation_id: str, code: str, result_metadata: dict):
        """Index a generated artifact into the active graph DB."""
        if self.active_provider == "neo4j":
            await self.neo4j.index_artifact(artifact_id, message_id, conversation_id, code, result_metadata)
        elif self.active_provider == "falkordb" and self.falkor_driver:
            pass # Skipping falkordb implementation for now as requested fix targets neo_4j
        elif self.active_provider == "kuzu" and self.kuzu_conn:
            pass # Skipping kuzu implementation for now
            
    async def query_related(self, query: str, limit: int = 10, project_id: str | None = None) -> list[dict[str, Any]]:
        """Query related concepts and conversations from the graph DB."""
        if self.active_provider == "neo4j":
            return await self.neo4j.query_related(query, limit, project_id=project_id)
        elif self.active_provider == "falkordb" and self.falkor_driver:
            try:
                res = self.falkor_driver.query(
                    "MATCH (c:Concept) WHERE toLower(c.name) CONTAINS toLower($q) "
                    "OPTIONAL MATCH (c)<-[:DISCUSSED]-(conv:Conversation) "
                    "RETURN c.name AS concept, collect(conv.id) AS conversations LIMIT $limit",
                    {"q": query, "limit": limit}
                )
                return [{"concept": row[0], "conversations": row[1]} for row in res.result_set]
            except Exception as e:
                logger.error(f"FalkorDB query related error: {e}")
                return []
        elif self.active_provider == "kuzu" and self.kuzu_conn:
            try:
                res = self.kuzu_conn.execute(
                    "MATCH (c:Concept) WHERE lower(c.name) CONTAINS lower($q) "
                    "RETURN c.name AS concept LIMIT $limit",
                    {"q": query, "limit": limit}
                )
                results = []
                while res.has_next():
                    row = res.get_next()
                    results.append({"concept": row[0]})
                return results
            except Exception as e:
                logger.error(f"Kuzu query related error: {e}")
                return []
        return []
        
    async def get_graph_stats(self) -> dict:
        if self.active_provider == "neo4j":
            return await self.neo4j.get_graph_stats()
        elif self.active_provider == "falkordb" and self.falkor_driver:
            try:
                res = self.falkor_driver.query("MATCH (n) RETURN count(n) AS nodes")
                nodes = res.result_set[0][0] if res.result_set else 0
                res2 = self.falkor_driver.query("MATCH ()-[r]->() RETURN count(r) AS rels")
                rels = res2.result_set[0][0] if res2.result_set else 0
                return {"nodes": nodes, "relationships": rels, "concepts": 0, "conversations": 0}
            except Exception:
                return {"nodes": 0, "relationships": 0, "concepts": 0, "conversations": 0}
        
        return {"nodes": 0, "relationships": 0, "concepts": 0, "conversations": 0}

    async def execute_query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self.active_provider == "neo4j":
            return await self.neo4j.execute_query(query, parameters)
        elif self.active_provider == "falkordb" and self.falkor_driver:
             try:
                 params = parameters or {}
                 res = self.falkor_driver.query(query, params)
                 return [{"result": row} for row in res.result_set] if res.result_set else []
             except Exception as e:
                 logger.error(f"FalkorDB query error: {e}")
                 return []
        elif self.active_provider == "kuzu" and self.kuzu_conn:
             try:
                 params = parameters or {}
                 res = self.kuzu_conn.execute(query, params)
                 
                 results = []
                 while res.has_next():
                     results.append({"result": res.get_next()})
                 return results
             except Exception as e:
                 logger.error(f"Kuzu query error: {e}")
                 return []
        return []

graph_client = UnifiedGraphClient()
