"""Milimo Quantum — FastAPI Application Entry Point."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (supports both direct and Docker execution)
_env_path = Path(__file__).resolve().parents[2] / ".env"
if _env_path.exists():
    load_dotenv(_env_path, override=False)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from starlette.middleware.base import BaseHTTPMiddleware

from app.limiter import limiter
from app.config import settings
from app.db.events import setup_listeners
from app.llm.ollama_client import ollama_client
from app.llm.mlx_client import mlx_client
from app.quantum.hal import hal_config
from app.quantum.executor import QISKIT_AVAILABLE
from app.routes import chat, quantum, projects, settings as settings_routes
from app.routes import analytics, search, collaboration
from app.routes import benchmarks, citations, audit
from app.routes import hpc, marketplace
from app.routes import graph as graph_routes
from app.routes import academy
from app.routes import feeds as feeds_routes
from app.routes import database as database_routes
from app.routes import experiments as experiments_routes
from app.routes import export as export_routes
from app.routes import ibm as ibm_routes
from app.routes import jobs as jobs_routes
from app.routes import qrng as qrng_routes
from app.routes import sync as sync_routes
from app.routes import workflows as workflows_routes
from app.routes import cache as cache_routes
from app.auth import router as auth_router

# Load Extensions
from app.extensions.mqdd.extension import setup_extension as setup_mqdd
from app.extensions.autoresearch.extension import setup_extension as setup_autoresearch
setup_mqdd()
setup_autoresearch()

# Initialize Event Fabric
setup_listeners()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown."""
    logger.info("⚛  Milimo Quantum starting up...")
    
    # Initialize SQL Database schemas inside Docker
    from app.db import init_db
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Start LLM based on HAL
        logger.warning("Qiskit not installed — quantum execution disabled")
    if hal_config.llm_backend == "mlx":
        # Start MLX on Apple Silicon
        if mlx_client.load_model():
            logger.info("✅ MLX LLM model loaded directly into unified memory.")
        else:
            logger.warning("⚠️  Failed to load MLX. Falling back to Ollama or Cloud.")
            
    # Always keep Ollama client alive for fallback
    if await ollama_client.is_available():
        models = await ollama_client.list_models()
        logger.info(f"✅ Ollama running with {len(models)} local models")
    else:
        logger.warning("⚠️  Ollama not responding — local AI features may fail if MLX/Cloud not configured.")

    # Check CUDA-Q execution environment
    from app.quantum.cudaq_executor import cudaq_executor
    if cudaq_executor.is_available:
        logger.info(f"✅ NVIDIA CUDA-Q ready on target: {cudaq_executor.target}")
    else:
        logger.info("ℹ️  CUDA-Q not available. Falling back to Aer Simulator.")

    # Log platform info
    logger.info(f"🖥  Platform: {hal_config.os_name} {hal_config.arch}")
    logger.info(f"⚡ GPU: {hal_config.gpu_name or 'None'}")
    
    if QISKIT_AVAILABLE:
        logger.info("✅ Qiskit loaded — quantum execution ready")
    else:
        logger.warning("⚠️  Qiskit not installed — quantum features disabled")

    # Graph init
    from app.graph.client import graph_client
    if await graph_client.connect():
        await graph_client.ensure_schema()
        logger.info("✅ Graph database connected — knowledge graph ready")
    else:
        logger.info("ℹ️  Graph database not available — graph features disabled (non-critical)")

    from app.experiments.sync_engine import sync_loop
    import asyncio
    sync_task = asyncio.create_task(sync_loop())
    logger.info("✅ Offline sync engine started in background")

    logger.info(f"⚛  Milimo Quantum ready on http://{settings.host}:{settings.port}")
    yield

    # Shutdown
    sync_task.cancel()
    # graph_client and ollama_client shutdown
    try:
        from app.graph.client import graph_client
        await graph_client.close()
    except Exception:
        pass
    await ollama_client.close()
    logger.info("⚛  Milimo Quantum shut down")


app = FastAPI(
    title="Milimo Quantum",
    description="The Universe of Quantum, In One Place",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            # Require custom header to prevent simple form-based cross-site requests
            if request.headers.get("X-Requested-With") != "XMLHttpRequest":
                return JSONResponse(
                    status_code=403, 
                    content={"detail": "CSRF verification failed: Missing X-Requested-With header"}
                )
        return await call_next(request)

app.add_middleware(CSRFMiddleware)

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
app.include_router(sync_routes.router)
app.include_router(qrng_routes.router)
app.include_router(workflows_routes.router)
app.include_router(cache_routes.router)
app.include_router(auth_router)

from app.extensions.mqdd.extension import mqdd_router
from app.extensions.autoresearch.extension import autoresearch_router
app.include_router(mqdd_router)
app.include_router(autoresearch_router)


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
    
    # Redis check
    redis_ok = False
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, db=0, socket_timeout=2)
        r.ping()
        redis_ok = True
    except Exception:
        pass
    
    # Celery broker check
    celery_broker_ok = redis_ok  # Celery uses Redis as broker
    
    # Cloud providers
    from app.llm.cloud_provider import get_available_providers
    configured_providers = [p["id"] for p in get_available_providers() if p["configured"]]
    
    return {
        "status": "healthy",
        "ollama": "connected" if ollama_ok else "disconnected",
        "qiskit": "available" if QISKIT_AVAILABLE else "unavailable",
        "graph": neo4j_client.get_status(),
        "memory": agent_memory.get_status(),
        "redis": "connected" if redis_ok else "disconnected",
        "celery_broker": "connected" if celery_broker_ok else "disconnected",
        "cloud_providers": configured_providers,
    }
