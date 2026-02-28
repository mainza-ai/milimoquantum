"""Milimo Quantum - Public Quantum App Marketplace.

Community agents, optimizers, circuit libraries, and plugins.
"""
from __future__ import annotations

from typing import Dict, List
from app.auth import get_current_user
from fastapi import APIRouter, Depends

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
INSTALLED_PLUGINS: set[str] = set()


@router.get("/")
@router.get("/algorithms")
async def list_plugins(q: str = "", tag: str = ""):
    """Browse the quantum app marketplace algorithms."""
    results = list(COMMUNITY_PLUGINS)

    if q:
        q_lower = q.lower()
        results = [p for p in results if q_lower in p["name"].lower() or q_lower in p["description"].lower()]

    if tag:
        t_lower = tag.lower()
        results = [p for p in results if t_lower in [t.lower() for t in p["tags"]]]

    # Add installed boolean
    for r in results:
        r["installed"] = r["id"] in INSTALLED_PLUGINS

    return {"plugins": results}


@router.post("/install/{plugin_id}")
async def install_plugin(plugin_id: str):
    """Install a community plugin."""
    plugin = next((p for p in COMMUNITY_PLUGINS if p["id"] == plugin_id), None)
    if not plugin:
        return {"error": "Plugin not found", "status": 404}

    INSTALLED_PLUGINS.add(plugin_id)
    return {"message": f"Successfully installed {plugin['name']}", "plugin_id": plugin_id}


@router.delete("/install/{plugin_id}")
async def uninstall_plugin(plugin_id: str):
    """Uninstall a community plugin."""
    if plugin_id in INSTALLED_PLUGINS:
        INSTALLED_PLUGINS.remove(plugin_id)
    return {"message": "Plugin removed"}
