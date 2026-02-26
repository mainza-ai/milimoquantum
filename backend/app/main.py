"""Milimo Quantum — FastAPI Application Entry Point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.llm.ollama_client import ollama_client
from app.routes import chat, quantum, projects, settings as settings_routes
from app.routes import analytics, search, collaboration
from app.routes import benchmarks, citations, audit
from app.routes import hpc, marketplace
from app.routes import graph as graph_routes
from app.routes import academy
from app.routes import feeds as feeds_routes
from app.routes import ibm as ibm_routes
from app.routes import export as export_routes
from app.routes import experiments as experiments_routes
from app.routes import database as database_routes
from app.routes import jobs as jobs_routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown."""
    logger.info("⚛  Milimo Quantum starting up...")

    # Check Ollama
    if await ollama_client.is_available():
        models = await ollama_client.list_models()
        logger.info(f"✅ Ollama connected — models: {models}")
    else:
        logger.warning("⚠️  Ollama not available — LLM features disabled")

    # Log platform info
    from app.quantum.hal import hal_config
    logger.info(f"🖥  Platform: {hal_config.os_name} {hal_config.arch}")
    logger.info(f"⚡ GPU: {hal_config.gpu_name or 'None'}")

    from app.quantum.executor import QISKIT_AVAILABLE
    if QISKIT_AVAILABLE:
        logger.info("✅ Qiskit loaded — quantum execution ready")
    else:
        logger.warning("⚠️  Qiskit not installed — quantum features disabled")

    logger.info(f"⚛  Milimo Quantum ready on http://{settings.host}:{settings.port}")
    yield

    # Shutdown
    await ollama_client.close()
    logger.info("⚛  Milimo Quantum shut down")


app = FastAPI(
    title="Milimo Quantum",
    description="The Universe of Quantum, In One Place",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat.router)
app.include_router(quantum.router)
app.include_router(projects.router)
app.include_router(settings_routes.router)
app.include_router(analytics.router)
app.include_router(search.router)
app.include_router(collaboration.router)
app.include_router(benchmarks.router)
app.include_router(citations.router)
app.include_router(audit.router)
app.include_router(hpc.router)
app.include_router(marketplace.router)
app.include_router(graph_routes.router)
app.include_router(academy.router)
app.include_router(feeds_routes.router)
app.include_router(ibm_routes.router)
app.include_router(export_routes.router)
app.include_router(experiments_routes.router)
app.include_router(database_routes.router)
app.include_router(jobs_routes.router)


@app.get("/")
async def root():
    return {
        "name": "Milimo Quantum",
        "version": "0.1.0",
        "tagline": "The Universe of Quantum, In One Place",
    }


@app.get("/api/health")
async def health():
    """Health check."""
    ollama_ok = await ollama_client.is_available()
    from app.quantum.executor import QISKIT_AVAILABLE
    from app.graph.neo4j_client import neo4j_client
    from app.graph.agent_memory import agent_memory
    return {
        "status": "healthy",
        "ollama": "connected" if ollama_ok else "disconnected",
        "qiskit": "available" if QISKIT_AVAILABLE else "unavailable",
        "graph": neo4j_client.get_status(),
        "memory": agent_memory.get_status(),
    }
