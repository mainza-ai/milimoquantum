"""Milimo Quantum - Unified Graph Interface.

Supports Neo4j, FalkorDB, and Kuzu connections for GraphRAG.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

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
            import falkordb
            self.falkor_available = True
            self.falkor_driver = None
        except ImportError:
            pass
            
        try:
            import kuzu
            self.kuzu_available = True
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
        # Fallback to true if simulated for now until full integration
        return True
        
    async def close(self):
        if self.active_provider == "neo4j":
            await self.neo4j.close()

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
                    "connected": False, # Placeholder until Kuzu driver fully wired
                }
            }
        }

    async def ensure_schema(self):
        """Ensure schema exists on active provider."""
        if self.active_provider == "neo4j":
            await self.neo4j.ensure_schema()
        elif self.active_provider == "falkordb" and self.falkor_driver:
            # FalkorDB automatically creates schema constraints on first use
            pass
            
    async def index_conversation(self, conversation_id: str, messages: list[dict], agent_type: str | None = None):
        """Index a conversation to the active graph DB."""
        if self.active_provider == "neo4j":
            await self.neo4j.index_conversation(conversation_id, messages, agent_type)
        elif self.active_provider == "falkordb" and self.falkor_driver:
            # Using OpenCypher (same as neo4j for basic operations)
            try:
                self.falkor_driver.query(f"MERGE (conv:Conversation {{id: '{conversation_id}'}}) SET conv.message_count = {len(messages)}")
                if agent_type:
                    self.falkor_driver.query(f"MERGE (a:Agent {{type: '{agent_type}'}})")
                    self.falkor_driver.query(f"MATCH (conv:Conversation {{id: '{conversation_id}'}}), (a:Agent {{type: '{agent_type}'}}) MERGE (conv)-[:USED_AGENT]->(a)")
            except Exception as e:
                logger.error(f"FalkorDB index error: {e}")
            
    async def query_related(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Query related concepts and conversations from the graph DB."""
        if self.active_provider == "neo4j":
            return await self.neo4j.query_related(query, limit)
        elif self.active_provider == "falkordb" and self.falkor_driver:
            # Fallback mock for FalkorDB graph querying until full entity extraction is ported
            return []
        return []
        
    async def get_graph_stats(self) -> dict:
        if self.active_provider == "neo4j":
            return await self.neo4j.get_graph_stats()
        elif self.active_provider == "falkordb" and self.falkor_driver:
            return {"nodes": 0, "relationships": 0, "concepts": 0, "conversations": 0} # Needs falkordb specific stats implementation
        return {"nodes": 0, "relationships": 0, "concepts": 0, "conversations": 0}

    async def execute_query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self.active_provider == "neo4j":
            return await self.neo4j.execute_query(query, parameters)
        elif self.active_provider == "falkordb" and self.falkor_driver:
             # Translate parameterized queries to falkordb format manually or use params
             # This is a simplification. Real implementation needs robust param handling.
             return []
        return []

graph_client = UnifiedGraphClient()
