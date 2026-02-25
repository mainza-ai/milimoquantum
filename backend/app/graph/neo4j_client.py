import os
import logging
from neo4j import AsyncGraphDatabase
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "milimo-quantum-graph")
        self.driver = None

    async def connect(self):
        try:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info("Connected to Neo4j successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")

    async def close(self):
        if self.driver:
            await self.driver.close()
            logger.info("Closed Neo4j connection.")

    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return the results as a list of dictionaries."""
        if not self.driver:
            await self.connect()
            
        parameters = parameters or {}
        async with self.driver.session() as session:
            try:
                result = await session.run(query, parameters)
                records = await result.data()
                return records
            except Exception as e:
                logger.error(f"Error executing Neo4j query: {e}")
                return []

# Singleton instance
neo4j_client = Neo4jClient()
