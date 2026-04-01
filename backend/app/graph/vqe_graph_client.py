"""
VQE-specific Neo4j client for Fixed Entity Architecture.

Implements Text2Cypher retrieval patterns for ansatz discovery.
This module provides the knowledge graph backend for VQE optimization,
enabling historical success path tracking and ansatz evolution chains.

Part of Phase 3 of the NemoClaw/AutoResearch integration.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class VQEGraphClient:
    """
    Client for VQE-specific graph operations.
    
    Implements the Fixed Entity Architecture with:
    - Molecule → Hamiltonian → AnsatzMotif relationships
    - Historical success path tracking
    - Text2Cypher retrieval
    
    Schema:
        (Molecule)-[:HAS_HAMILTONIAN]->(Hamiltonian)
        (Hamiltonian)-[:SOLVED_BY]->(AnsatzMotif)
        (AutoresearchRun)-[:DISCOVERED]->(AnsatzMotif)
        (AnsatzMotif)-[:SUCCESSOR_OF]->(AnsatzMotif)
    
    Example:
        >>> client = VQEGraphClient()
        >>> await client.connect()
        >>> await client.index_molecule("H2", electron_count=2)
        >>> results = await client.retrieve_successful_ansatzes("H2")
    """
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "milimopassword")
        self.driver = None
        self.connected = False
        
    async def connect(self) -> bool:
        """Connect to Neo4j."""
        try:
            from neo4j import AsyncGraphDatabase
            
            self.driver = AsyncGraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            
            # Verify connectivity
            async with self.driver.session() as session:
                await session.run("RETURN 1")
                
            self.connected = True
            logger.info(f"VQE GraphClient connected to {self.uri}")
            return True
            
        except ImportError:
            logger.warning("neo4j driver not installed - graph operations disabled")
            self.connected = False
            return False
        except Exception as e:
            logger.warning(f"VQE GraphClient connection failed: {e}")
            self.connected = False
            return False
            
    async def close(self):
        """Close connection."""
        if self.driver:
            await self.driver.close()
            self.connected = False
            logger.info("VQE GraphClient connection closed")
            
    async def ensure_schema(self):
        """Create indexes and constraints for VQE entities."""
        if not self.connected:
            return False
            
        schema_queries = [
            # Constraints
            "CREATE CONSTRAINT molecule_formula IF NOT EXISTS FOR (m:Molecule) REQUIRE m.formula IS UNIQUE",
            "CREATE CONSTRAINT hamiltonian_id IF NOT EXISTS FOR (h:Hamiltonian) REQUIRE h.id IS UNIQUE",
            "CREATE CONSTRAINT ansatz_motif_id IF NOT EXISTS FOR (a:AnsatzMotif) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT autoresearch_run_id IF NOT EXISTS FOR (r:AutoresearchRun) REQUIRE r.id IS UNIQUE",
            
            # Indexes
            "CREATE INDEX molecule_electrons IF NOT EXISTS FOR (m:Molecule) ON (m.electron_count)",
            "CREATE INDEX hamiltonian_qubits IF NOT EXISTS FOR (h:Hamiltonian) ON (h.num_qubits)",
            "CREATE INDEX ansatz_mw_score IF NOT EXISTS FOR (a:AnsatzMotif) ON (a.meyer_wallach_score)",
            "CREATE INDEX ansatz_depth IF NOT EXISTS FOR (a:AnsatzMotif) ON (a.depth)",
            "CREATE INDEX autoresearch_status IF NOT EXISTS FOR (r:AutoresearchRun) ON (r.status)",
            "CREATE INDEX autoresearch_timestamp IF NOT EXISTS FOR (r:AutoresearchRun) ON (r.timestamp)",
        ]
        
        for query in schema_queries:
            try:
                async with self.driver.session() as session:
                    await session.run(query)
            except Exception as e:
                logger.debug(f"Schema query warning (may already exist): {e}")
                
        logger.info("VQE schema ensured")
        return True
            
    async def index_molecule(
        self,
        formula: str,
        electron_count: int,
        pubchem_cid: Optional[int] = None,
        ground_state_energy: Optional[float] = None
    ) -> bool:
        """Index a molecule in the knowledge graph."""
        if not self.connected:
            return False
            
        query = """
        MERGE (m:Molecule {formula: $formula})
        SET m.electron_count = $electrons,
            m.pubchem_cid = $pubchem,
            m.ground_state_energy = $energy,
            m.indexed_at = datetime()
        RETURN m
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, {
                    "formula": formula,
                    "electrons": electron_count,
                    "pubchem": pubchem_cid,
                    "energy": ground_state_energy
                })
                await result.single()
            logger.debug(f"Indexed molecule: {formula}")
            return True
        except Exception as e:
            logger.error(f"Failed to index molecule: {e}")
            return False
            
    async def index_hamiltonian(
        self,
        molecule: str,
        hamiltonian_id: str,
        pauli_string: str,
        num_qubits: int,
        basis: str = "sto-3g"
    ) -> bool:
        """Index a molecular Hamiltonian."""
        if not self.connected:
            return False
            
        query = """
        MATCH (m:Molecule {formula: $molecule})
        MERGE (h:Hamiltonian {id: $h_id})
        SET h.pauli_string = $pauli,
            h.num_qubits = $qubits,
            h.basis = $basis,
            h.created_at = datetime()
        MERGE (m)-[:HAS_HAMILTONIAN]->(h)
        RETURN h
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, {
                    "molecule": molecule,
                    "h_id": hamiltonian_id,
                    "pauli": pauli_string,
                    "qubits": num_qubits,
                    "basis": basis
                })
                await result.single()
            logger.debug(f"Indexed Hamiltonian: {hamiltonian_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index Hamiltonian: {e}")
            return False
            
    async def index_ansatz_motif(
        self,
        motif_id: str,
        gate_sequence: List[str],
        depth: int,
        parameter_count: int,
        meyer_wallach_score: float,
        parent_motif_id: Optional[str] = None
    ) -> bool:
        """
        Index a discovered ansatz motif.
        
        Args:
            motif_id: Unique identifier
            gate_sequence: List of gate tokens
            depth: Circuit depth
            parameter_count: Number of parameters
            meyer_wallach_score: MW entanglement measure
            parent_motif_id: ID of parent motif (for evolution chain)
        """
        if not self.connected:
            return False
            
        query = """
        MERGE (a:AnsatzMotif {id: $id})
        SET a.gate_sequence = $gates,
            a.depth = $depth,
            a.parameter_count = $params,
            a.meyer_wallach_score = $mw,
            a.created_at = datetime()
        """
        
        params = {
            "id": motif_id,
            "gates": gate_sequence,
            "depth": depth,
            "params": parameter_count,
            "mw": meyer_wallach_score
        }
        
        if parent_motif_id:
            query += """
            WITH a
            MATCH (parent:AnsatzMotif {id: $parent_id})
            MERGE (a)-[:SUCCESSOR_OF]->(parent)
            """
            params["parent_id"] = parent_motif_id
            
        query += " RETURN a"
            
        try:
            async with self.driver.session() as session:
                result = await session.run(query, params)
                await result.single()
            logger.debug(f"Indexed ansatz motif: {motif_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index ansatz motif: {e}")
            return False
            
    async def link_successful_ansatz(
        self,
        hamiltonian_id: str,
        ansatz_id: str,
        converged: bool,
        energy: float,
        gradient_variance: float,
        iterations: int
    ) -> bool:
        """Link an ansatz to a Hamiltonian with performance metrics."""
        if not self.connected:
            return False
            
        query = """
        MATCH (h:Hamiltonian {id: $h_id})
        MATCH (a:AnsatzMotif {id: $a_id})
        MERGE (h)-[s:SOLVED_BY]->(a)
        SET s.converged = $converged,
            s.energy = $energy,
            s.gradient_variance = $grad_var,
            s.iterations = $iterations,
            s.solved_at = datetime()
        RETURN s
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, {
                    "h_id": hamiltonian_id,
                    "a_id": ansatz_id,
                    "converged": converged,
                    "energy": energy,
                    "grad_var": gradient_variance,
                    "iterations": iterations
                })
                await result.single()
            logger.debug(f"Linked ansatz {ansatz_id} to Hamiltonian {hamiltonian_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to link ansatz: {e}")
            return False
            
    async def retrieve_successful_ansatzes(
        self,
        molecule: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historically successful ansatz architectures.
        
        This implements the Text2Cypher retrieval pattern:
        "Find the best ansatz for this molecule"
        
        Returns:
            List of ansatz data with gate sequences and scores
        """
        if not self.connected:
            return []
            
        query = """
        MATCH (m:Molecule {formula: $mol})-[:HAS_HAMILTONIAN]->(h:Hamiltonian)
        MATCH (h)-[s:SOLVED_BY]->(a:AnsatzMotif)
        WHERE s.converged = true
          AND s.gradient_variance < 0.1
        RETURN a.id AS id,
               a.gate_sequence AS gates,
               a.meyer_wallach_score AS mw,
               a.depth AS depth,
               s.energy AS energy,
               s.iterations AS iterations
        ORDER BY s.energy ASC, a.meyer_wallach_score DESC
        LIMIT $limit
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, {
                    "mol": molecule,
                    "limit": limit
                })
                return await result.data()
        except Exception as e:
            logger.error(f"Failed to retrieve ansatzes: {e}")
            return []
            
    async def retrieve_ansatz_evolution_chain(
        self,
        motif_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get the full evolutionary history of an ansatz.
        
        Returns the chain of mutations that led to this motif.
        """
        if not self.connected:
            return []
            
        query = """
        MATCH path = (a:AnsatzMotif {id: $id})-[:SUCCESSOR_OF*]->(root:AnsatzMotif)
        RETURN [n IN nodes(path) | {
            id: n.id,
            gates: n.gate_sequence,
            mw: n.meyer_wallach_score,
            depth: n.depth
        }] AS evolution
        """
        
        try:
            async with self.driver.session() as session:
                result = await session.run(query, {"id": motif_id})
                data = await result.single()
                return data["evolution"] if data else []
        except Exception as e:
            logger.error(f"Failed to retrieve evolution: {e}")
            return []
            
    async def text2cypher_search(
        self,
        natural_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Text2Cypher retrieval: convert natural language to Cypher.
        
        Example queries:
        - "best ansatz for H2"
        - "circuits with high entanglement"
        - "low depth ansatzes that converged"
        
        Args:
            natural_query: Natural language query
            context: Additional context (molecule, energy range, etc.)
        """
        if not self.connected:
            return []
            
        context = context or {}
        query_lower = natural_query.lower()
        
        # Pattern matching for common queries
        if "best" in query_lower and "ansatz" in query_lower:
            molecule = context.get("molecule")
            if molecule:
                return await self.retrieve_successful_ansatzes(molecule)
            else:
                # Return best ansatzes overall
                query = """
                MATCH (h:Hamiltonian)-[s:SOLVED_BY]->(a:AnsatzMotif)
                WHERE s.converged = true
                RETURN a.id AS id, 
                       a.gate_sequence AS gates, 
                       s.energy AS energy, 
                       a.meyer_wallach_score AS mw
                ORDER BY s.energy ASC
                LIMIT 10
                """
                params = {}
                
        elif "high entanglement" in query_lower or "meyer-wallach" in query_lower:
            min_mw = context.get("min_mw", 0.5)
            query = """
            MATCH (a:AnsatzMotif)
            WHERE a.meyer_wallach_score > $min_mw
            RETURN a.id AS id, 
                   a.gate_sequence AS gates, 
                   a.meyer_wallach_score AS mw, 
                   a.depth AS depth
            ORDER BY a.meyer_wallach_score DESC
            LIMIT 10
            """
            params = {"min_mw": min_mw}
            
        elif "low depth" in query_lower or "shallow" in query_lower:
            max_depth = context.get("max_depth", 10)
            query = """
            MATCH (a:AnsatzMotif)
            WHERE a.depth < $max_depth
            RETURN a.id AS id, 
                   a.gate_sequence AS gates, 
                   a.depth AS depth, 
                   a.meyer_wallach_score AS mw
            ORDER BY a.depth ASC
            LIMIT 10
            """
            params = {"max_depth": max_depth}
            
        else:
            # Default: return recent ansatzes
            query = """
            MATCH (a:AnsatzMotif)
            RETURN a.id AS id, 
                   a.gate_sequence AS gates, 
                   a.meyer_wallach_score AS mw, 
                   a.depth AS depth
            ORDER BY a.created_at DESC
            LIMIT 10
            """
            params = {}
            
        try:
            async with self.driver.session() as session:
                result = await session.run(query, params)
                return await result.data()
        except Exception as e:
            logger.error(f"Text2Cypher search failed: {e}")
            return []
            
    async def index_autoresearch_run(
        self,
        run_id: str,
        commit_hash: str,
        val_bpb: float,
        energy: Optional[float],
        gradient_variance: Optional[float],
        status: str,
        molecule: Optional[str] = None,
        ansatz_id: Optional[str] = None
    ) -> bool:
        """Index an Autoresearch run (keep/discard/crash)."""
        if not self.connected:
            return False
            
        query = """
        MERGE (r:AutoresearchRun {id: $id})
        SET r.commit_hash = $commit,
            r.val_bpb = $bpb,
            r.energy = $energy,
            r.gradient_variance = $grad_var,
            r.status = $status,
            r.timestamp = datetime()
        """
        
        params = {
            "id": run_id,
            "commit": commit_hash,
            "bpb": val_bpb,
            "energy": energy,
            "grad_var": gradient_variance,
            "status": status,
            "mol": molecule,
            "ansatz": ansatz_id
        }
        
        if molecule:
            query += """
            WITH r
            MATCH (m:Molecule {formula: $mol})
            MERGE (r)-[:TARGETED]->(m)
            """
            
        if ansatz_id and status == "keep":
            query += """
            WITH r
            MATCH (a:AnsatzMotif {id: $ansatz})
            MERGE (r)-[:DISCOVERED]->(a)
            """
            
        query += " RETURN r"
            
        try:
            async with self.driver.session() as session:
                result = await session.run(query, params)
                await result.single()
            logger.debug(f"Indexed Autoresearch run: {run_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index Autoresearch run: {e}")
            return False
            
    async def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        if not self.connected:
            return {"connected": False}
            
        try:
            async with self.driver.session() as session:
                result = await session.run("""
                    MATCH (m:Molecule) WITH count(m) AS molecules
                    MATCH (h:Hamiltonian) WITH molecules, count(h) AS hamiltonians
                    MATCH (a:AnsatzMotif) WITH molecules, hamiltonians, count(a) AS ansatzes
                    MATCH (r:AutoresearchRun) WITH molecules, hamiltonians, ansatzes, count(r) AS runs
                    MATCH ()-[e:SOLVED_BY]->() WITH molecules, hamiltonians, ansatzes, runs, count(e) AS solved_rels
                    RETURN molecules, hamiltonians, ansatzes, runs, solved_rels
                """)
                data = await result.single()
                
                return {
                    "connected": True,
                    "molecules": data["molecules"] if data else 0,
                    "hamiltonians": data["hamiltonians"] if data else 0,
                    "ansatz_motifs": data["ansatzes"] if data else 0,
                    "autoresearch_runs": data["runs"] if data else 0,
                    "solved_relationships": data["solved_rels"] if data else 0
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"connected": True, "error": str(e)}


# Singleton instance
vqe_graph_client = VQEGraphClient()


async def test_vqe_graph_client():
    """Test the VQE graph client."""
    client = VQEGraphClient()
    
    connected = await client.connect()
    if not connected:
        print("Could not connect to Neo4j")
        return
        
    print("Connected to Neo4j")
    
    # Ensure schema
    await client.ensure_schema()
    print("Schema ensured")
    
    # Test molecule indexing
    await client.index_molecule(
        formula="H2",
        electron_count=2,
        ground_state_energy=-1.137
    )
    print("Indexed molecule: H2")
    
    # Test Hamiltonian indexing
    await client.index_hamiltonian(
        molecule="H2",
        hamiltonian_id="H2-sto-3g",
        pauli_string="IIII + IZII + ...",
        num_qubits=4
    )
    print("Indexed Hamiltonian: H2-sto-3g")
    
    # Test ansatz indexing
    await client.index_ansatz_motif(
        motif_id="ansatz-test-001",
        gate_sequence=["H", "CNOT", "RZ", "RY"],
        depth=4,
        parameter_count=2,
        meyer_wallach_score=0.85
    )
    print("Indexed ansatz: ansatz-test-001")
    
    # Test linking
    await client.link_successful_ansatz(
        hamiltonian_id="H2-sto-3g",
        ansatz_id="ansatz-test-001",
        converged=True,
        energy=-1.13,
        gradient_variance=0.05,
        iterations=50
    )
    print("Linked ansatz to Hamiltonian")
    
    # Test retrieval
    results = await client.retrieve_successful_ansatzes("H2")
    print(f"Retrieved {len(results)} successful ansatzes for H2")
    
    # Test Text2Cypher
    results = await client.text2cypher_search("best ansatz for H2")
    print(f"Text2Cypher search returned {len(results)} results")
    
    # Get stats
    stats = await client.get_stats()
    print(f"Graph stats: {stats}")
    
    await client.close()
    print("Connection closed")


if __name__ == "__main__":
    asyncio.run(test_vqe_graph_client())
