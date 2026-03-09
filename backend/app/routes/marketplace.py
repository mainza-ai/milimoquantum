"""Milimo Quantum - Public Quantum App Marketplace.

Community agents, optimizers, circuit libraries, and plugins.
"""
from __future__ import annotations

from typing import Any
from app.auth import get_current_user
from app.db import get_session
from app.db.models import MarketplacePlugin, UserPlugin
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"], dependencies=[Depends(get_current_user)])

# Community plugins spanning all quantum domains
COMMUNITY_PLUGINS = [
    {
        "id": "qml-fin-1",
        "name": "Financial QAOA Tuner",
        "author": "quant-trader",
        "description": "Optimized QAOA schedules for portfolio optimization. Includes pre-tuned mixers and phase separators for financial use cases.",
        "version": "1.0.2",
        "downloads": 1420,
        "rating": 4.8,
        "tags": ["finance", "optimization", "qaoa"],
    },
    {
        "id": "chem-vqe-fast",
        "name": "VQE Fast-Converger",
        "author": "q-chem-lab",
        "description": "Custom PySCF ansatze blocks that converge 30% faster on noisy hardware. Adaptive gradient descent with noise-aware parameter initialization.",
        "version": "0.9.1",
        "downloads": 850,
        "rating": 4.5,
        "tags": ["chemistry", "vqe", "pyscf"],
    },
    {
        "id": "qec-surface-viz",
        "name": "Surface Code Visualizer",
        "author": "ftqc-team",
        "description": "Real-time stabilizer measurements and syndrome extraction visualization for surface codes. Supports rotated and unrotated lattices.",
        "version": "2.1.0",
        "downloads": 3200,
        "rating": 4.9,
        "tags": ["qec", "visualization", "fault-tolerant"],
    },
    {
        "id": "qml-classifier",
        "name": "Quantum SVM Classifier",
        "author": "ml-quantum",
        "description": "Pre-built quantum kernel SVM pipeline with automatic feature map selection. Supports ZZFeatureMap, PauliFeatureMap, and custom ansatze.",
        "version": "1.2.0",
        "downloads": 2100,
        "rating": 4.7,
        "tags": ["qml", "classification", "svm"],
    },
    {
        "id": "bb84-toolkit",
        "name": "BB84 QKD Toolkit",
        "author": "crypto-q",
        "description": "Complete BB84 quantum key distribution simulation with eavesdropper detection, error correction (Cascade), and privacy amplification.",
        "version": "1.1.3",
        "downloads": 1850,
        "rating": 4.6,
        "tags": ["crypto", "qkd", "bb84"],
    },
    {
        "id": "dwave-sampler",
        "name": "D-Wave Auto Embedder",
        "author": "annealing-lab",
        "description": "Automatic minor embedding optimizer for D-Wave topology. Reduces chain lengths by up to 40% on Pegasus graphs.",
        "version": "0.8.5",
        "downloads": 720,
        "rating": 4.4,
        "tags": ["dwave", "annealing", "embedding"],
    },
    {
        "id": "qrng-entropy",
        "name": "QRNG Entropy Pool",
        "author": "rng-labs",
        "description": "Quantum random number generator using Hadamard measurement. Provides a CSPRNG-compatible interface for cryptographic applications.",
        "version": "2.0.1",
        "downloads": 3500,
        "rating": 4.8,
        "tags": ["crypto", "random", "qrng"],
    },
    {
        "id": "qaoa-maxcut",
        "name": "MaxCut QAOA Solver",
        "author": "opt-quantum",
        "description": "Production-ready QAOA solver for MaxCut problems. Warm-start initialization with graph partitioning heuristics.",
        "version": "1.3.0",
        "downloads": 1650,
        "rating": 4.6,
        "tags": ["optimization", "qaoa", "maxcut"],
    },
    {
        "id": "vqe-mol-sim",
        "name": "Molecular Ground State VQE",
        "author": "q-pharma",
        "description": "End-to-end pipeline for molecular ground state energy estimation. Supports H₂, LiH, BeH₂, and custom molecules via PySCF.",
        "version": "1.0.4",
        "downloads": 950,
        "rating": 4.5,
        "tags": ["chemistry", "vqe", "molecules"],
    },
    {
        "id": "quantum-walk",
        "name": "Quantum Walk Simulator",
        "author": "graph-quantum",
        "description": "Continuous and discrete quantum walks on arbitrary graphs. Includes spatial search and graph isomorphism algorithms.",
        "version": "0.7.2",
        "downloads": 480,
        "rating": 4.3,
        "tags": ["research", "walks", "graphs"],
    },
    {
        "id": "noise-model-gen",
        "name": "Noise Model Generator",
        "author": "ibm-community",
        "description": "Generate realistic noise models from IBM Quantum device calibration data. Supports thermal relaxation, depolarizing, and readout error channels.",
        "version": "1.1.0",
        "downloads": 2800,
        "rating": 4.7,
        "tags": ["noise", "simulation", "ibm"],
    },
    {
        "id": "qnet-teleport",
        "name": "Quantum Teleportation Network",
        "author": "net-quantum",
        "description": "Multi-node quantum teleportation protocol simulator with entanglement swapping and purification. Supports linear and star topologies.",
        "version": "0.6.1",
        "downloads": 620,
        "rating": 4.4,
        "tags": ["networking", "teleportation", "entanglement"],
    },
]

# State for installed plugins (persists in memory for demo)
# INSTALLED_PLUGINS: set[str] = set()


@router.get("/")
@router.get("/algorithms")
async def list_plugins(q: str = "", tag: str = "", current_user: Any = Depends(get_current_user)):
    """Browse the quantum app marketplace algorithms."""
    session = get_session()
    try:
        # Get all plugins from DB (or use the hardcoded list to seed if empty)
        db_plugins = session.query(MarketplacePlugin).all()
        if not db_plugins:
            # Seed the database with the core plugins on first run
            for p_data in COMMUNITY_PLUGINS:
                p = MarketplacePlugin(**p_data)
                session.add(p)
            session.commit()
            db_plugins = session.query(MarketplacePlugin).all()

        # Get user's installed plugins
        user_id = current_user.get("sub", "local-dev-id")
        installed_ids = {up.plugin_id for up in session.query(UserPlugin).filter_by(user_id=user_id).all()}

        results = []
        for p in db_plugins:
            p_dict = {
                "id": p.id,
                "name": p.name,
                "author": p.author,
                "description": p.description,
                "version": p.version,
                "downloads": p.downloads,
                "rating": p.rating,
                "tags": p.tags or [],
                "installed": p.id in installed_ids
            }
            
            # Simple filtering
            if q and q.lower() not in p_dict["name"].lower() and q.lower() not in p_dict["description"].lower():
                continue
            if tag and tag.lower() not in [t.lower() for t in p_dict["tags"]]:
                continue
            
            results.append(p_dict)

        return {"plugins": results}
    finally:
        session.close()


@router.post("/install/{plugin_id}")
async def install_plugin(plugin_id: str, current_user: Any = Depends(get_current_user)):
    """Install a community plugin."""
    session = get_session()
    try:
        plugin = session.query(MarketplacePlugin).filter_by(id=plugin_id).first()
        if not plugin:
            # Check hardcoded list as fallback seeded data
            plugin_data = next((p for p in COMMUNITY_PLUGINS if p["id"] == plugin_id), None)
            if not plugin_data:
                raise HTTPException(status_code=404, detail="Plugin not found")
            plugin = MarketplacePlugin(**plugin_data)
            session.add(plugin)
            session.commit()

        # Check if already installed
        user_id = current_user.get("sub", "local-dev-id")
        existing = session.query(UserPlugin).filter_by(user_id=user_id, plugin_id=plugin_id).first()
        if not existing:
            install = UserPlugin(user_id=user_id, plugin_id=plugin_id)
            session.add(install)
            plugin.downloads += 1
            session.commit()
            
        return {"message": f"Successfully installed {plugin.name}", "plugin_id": plugin_id}
    finally:
        session.close()


@router.delete("/install/{plugin_id}")
async def uninstall_plugin(plugin_id: str, current_user: Any = Depends(get_current_user)):
    """Uninstall a community plugin."""
    session = get_session()
    try:
        user_id = current_user.get("sub", "local-dev-id")
        install = session.query(UserPlugin).filter_by(user_id=user_id, plugin_id=plugin_id).first()
        if install:
            session.delete(install)
            session.commit()
        return {"message": "Plugin removed"}
    finally:
        session.close()
