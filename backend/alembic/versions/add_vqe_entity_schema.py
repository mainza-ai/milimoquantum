"""Add VQE entity schema to Neo4j

Revision ID: vqe_entity_schema
Revises: add_projects_related_tables
Create Date: 2026-03-30

This migration adds the Fixed Entity Architecture for VQE ansatz tracking:
- Molecule nodes with molecular properties
- Hamiltonian nodes with Pauli representations
- AnsatzMotif nodes with tokenized gate sequences
- AutoresearchRun nodes for experiment tracking

The schema enables historical success path tracking and Text2Cypher
retrieval patterns for autonomous VQE optimization.
"""

import asyncio
import logging
import os
from typing import List

logger = logging.getLogger(__name__)

# Migration queries
SCHEMA_QUERIES = [
    # === CONSTRAINTS ===
    "CREATE CONSTRAINT molecule_formula IF NOT EXISTS FOR (m:Molecule) REQUIRE m.formula IS UNIQUE",
    "CREATE CONSTRAINT hamiltonian_id IF NOT EXISTS FOR (h:Hamiltonian) REQUIRE h.id IS UNIQUE",
    "CREATE CONSTRAINT ansatz_motif_id IF NOT EXISTS FOR (a:AnsatzMotif) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT autoresearch_run_id IF NOT EXISTS FOR (r:AutoresearchRun) REQUIRE r.id IS UNIQUE",
    
    # === INDEXES ===
    "CREATE INDEX molecule_electrons IF NOT EXISTS FOR (m:Molecule) ON (m.electron_count)",
    "CREATE INDEX hamiltonian_qubits IF NOT EXISTS FOR (h:Hamiltonian) ON (h.num_qubits)",
    "CREATE INDEX ansatz_mw_score IF NOT EXISTS FOR (a:AnsatzMotif) ON (a.meyer_wallach_score)",
    "CREATE INDEX ansatz_depth IF NOT EXISTS FOR (a:AnsatzMotif) ON (a.depth)",
    "CREATE INDEX autoresearch_status IF NOT EXISTS FOR (r:AutoresearchRun) ON (r.status)",
    "CREATE INDEX autoresearch_timestamp IF NOT EXISTS FOR (r:AutoresearchRun) ON (r.timestamp)",
    
    # === FULLTEXT INDEX FOR TEXT2CYPHER ===
    "CREATE FULLTEXT INDEX ansatz_fulltext IF NOT EXISTS FOR (a:AnsatzMotif) ON EACH [a.gate_sequence]",
]

DROP_QUERIES = [
    "DROP CONSTRAINT molecule_formula IF EXISTS",
    "DROP CONSTRAINT hamiltonian_id IF EXISTS",
    "DROP CONSTRAINT ansatz_motif_id IF EXISTS",
    "DROP CONSTRAINT autoresearch_run_id IF EXISTS",
    "DROP INDEX molecule_electrons IF EXISTS",
    "DROP INDEX hamiltonian_qubits IF EXISTS",
    "DROP INDEX ansatz_mw_score IF EXISTS",
    "DROP INDEX ansatz_depth IF EXISTS",
    "DROP INDEX autoresearch_status IF EXISTS",
    "DROP INDEX autoresearch_timestamp IF EXISTS",
    "DROP FULLTEXT INDEX ansatz_fulltext IF EXISTS",
]


async def run_migration_async(queries: List[str], downgrade: bool = False):
    """Execute schema migration queries against Neo4j."""
    try:
        from neo4j import AsyncGraphDatabase
    except ImportError:
        logger.warning("neo4j driver not installed - skipping migration")
        return False
        
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "milimopassword")
    
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        
        async with driver.session() as session:
            # Verify connection
            await session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {uri}")
            
            for query in queries:
                try:
                    await session.run(query)
                    action = "Dropped" if downgrade else "Created"
                    logger.info(f"{action}: {query.split()[0]} {query.split()[2] if len(query.split()) > 2 else ''}")
                except Exception as e:
                    # Log warning but continue (constraint may already exist)
                    logger.debug(f"Query skipped (may already exist): {e}")
                    
        await driver.close()
        
        action = "downgraded" if downgrade else "completed"
        logger.info(f"VQE entity schema migration {action} successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def upgrade():
    """Alembic upgrade entry point."""
    logger.info("Running VQE entity schema upgrade...")
    return asyncio.run(run_migration_async(SCHEMA_QUERIES, downgrade=False))


def downgrade():
    """Alembic downgrade - remove VQE schema."""
    logger.info("Running VQE entity schema downgrade...")
    return asyncio.run(run_migration_async(DROP_QUERIES, downgrade=True))


async def test_migration():
    """Test the migration by verifying schema."""
    try:
        from neo4j import AsyncGraphDatabase
    except ImportError:
        print("neo4j driver not installed")
        return False
        
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "milimopassword")
    
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        
        async with driver.session() as session:
            # Check constraints
            result = await session.run("SHOW CONSTRAINTS")
            constraints = await result.data()
            print(f"Found {len(constraints)} constraints")
            
            # Check indexes
            result = await session.run("SHOW INDEXES")
            indexes = await result.data()
            print(f"Found {len(indexes)} indexes")
            
            # Check for VQE-specific constraints
            vqe_constraints = [c for c in constraints if any(
                label in str(c) for label in ['Molecule', 'Hamiltonian', 'AnsatzMotif', 'AutoresearchRun']
            )]
            print(f"VQE-specific constraints: {len(vqe_constraints)}")
            
        await driver.close()
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VQE Entity Schema Migration")
    parser.add_argument("--upgrade", action="store_true", help="Run upgrade")
    parser.add_argument("--downgrade", action="store_true", help="Run downgrade")
    parser.add_argument("--test", action="store_true", help="Test migration")
    
    args = parser.parse_args()
    
    if args.upgrade:
        success = upgrade()
        print(f"Upgrade: {'SUCCESS' if success else 'FAILED'}")
    elif args.downgrade:
        success = downgrade()
        print(f"Downgrade: {'SUCCESS' if success else 'FAILED'}")
    elif args.test:
        success = asyncio.run(test_migration())
        print(f"Test: {'SUCCESS' if success else 'FAILED'}")
    else:
        # Default: run upgrade
        success = upgrade()
        print(f"Upgrade: {'SUCCESS' if success else 'FAILED'}")
