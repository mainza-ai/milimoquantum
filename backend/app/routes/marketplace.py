"""Milimo Quantum - Public Quantum App Marketplace.

Mock API for downloading community agents and plugins.
"""
from __future__ import annotations

import uuid
from typing import Dict, List
from fastapi import APIRouter

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

# Mock database of community plugins
COMMUNITY_PLUGINS = [
    {
        "id": "qml-fin-1",
        "name": "Financial QAOA Tuner",
        "author": "quant-trader",
        "description": "Optimized QAOA schedules for portfolio optimization.",
        "version": "1.0.2",
        "downloads": 1420,
        "rating": 4.8,
        "tags": ["finance", "optimization", "qaoa"]
    },
    {
        "id": "chem-vqe-fast",
        "name": "VQE Fast-Converger",
        "author": "q-chem-lab",
        "description": "Custom PySCF ansatze blocks that converge 30% faster on noisy hardware.",
        "version": "0.9.1",
        "downloads": 850,
        "rating": 4.5,
        "tags": ["chemistry", "vqe", "pyscf"]
    },
    {
        "id": "qec-surface-viz",
        "name": "Surface Code Visualizer plugin",
        "author": "ftqc-team",
        "description": "Visualizes stabilizer measurements in real-time.",
        "version": "2.1.0",
        "downloads": 3200,
        "rating": 4.9,
        "tags": ["qec", "visualization", "fault-tolerant"]
    }
]

# State for installed plugins (persists in memory for demo)
INSTALLED_PLUGINS = set()


@router.get("/")
async def list_plugins(q: str = "", tag: str = ""):
    """Browse the quantum app marketplace."""
    results = COMMUNITY_PLUGINS
    
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
