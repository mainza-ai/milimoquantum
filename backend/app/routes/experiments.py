"""Milimo Quantum — Experiment Registry & Notebook Routes."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from fastapi.responses import Response

from app.experiments import registry, notebook
from app import storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


# ── Run Registry ─────────────────────────────────────────
@router.get("/projects")
async def list_projects():
    """List all experiment projects."""
    return {"projects": registry.list_projects()}


@router.get("/runs/{project}")
async def list_runs(project: str, limit: int = 50):
    """List runs for a project."""
    return {"runs": registry.list_runs(project, limit)}


@router.get("/runs/{project}/{run_id}")
async def get_run(project: str, run_id: str):
    """Get a specific run."""
    run = registry.get_run(project, run_id)
    if not run:
        return {"error": "Run not found"}
    return run


@router.post("/log")
async def log_run(data: dict):
    """Log a new experiment run.

    Body: { project, circuit_name, circuit_code, backend, shots,
            mitigation, transpile_options, results, tags, notes }
    """
    return registry.log_run(**{k: v for k, v in data.items() if k in {
        "project", "circuit_name", "circuit_code", "backend", "shots",
        "mitigation", "transpile_options", "results", "tags", "notes",
    }})


@router.post("/compare")
async def compare_runs(data: dict):
    """Compare two runs.

    Body: { project, run_id_a, run_id_b }
    """
    return registry.compare_runs(
        data.get("project", "default"),
        data.get("run_id_a", ""),
        data.get("run_id_b", ""),
    )


@router.put("/runs/{project}/{run_id}/tag")
async def tag_run(project: str, run_id: str, data: dict):
    """Tag a run.

    Body: { tags: ["fast", "production"] }
    """
    return registry.tag_run(project, run_id, data.get("tags", []))


# ── Notebook Export ──────────────────────────────────────
@router.get("/notebook/{conversation_id}")
async def export_notebook(conversation_id: str):
    """Export a conversation as a Jupyter notebook (.ipynb)."""
    conversation = storage.load_conversation(conversation_id)
    if not conversation:
        return {"error": "Conversation not found"}

    messages = conversation.get("messages", [])
    nb = notebook.generate_notebook(
        title=f"Milimo Quantum — {conversation_id[:8]}",
        conversation_messages=messages,
    )
    nb_bytes = notebook.notebook_to_bytes(nb)

    return Response(
        content=nb_bytes,
        media_type="application/x-ipynb+json",
        headers={
            "Content-Disposition": f'attachment; filename="{conversation_id[:8]}_experiment.ipynb"',
        },
    )


@router.post("/notebook/generate")
async def generate_notebook_endpoint(data: dict):
    """Generate a notebook from explicit code cells.

    Body: { title, code_cells: [...], markdown_cells: [...] }
    """
    nb = notebook.generate_notebook(
        title=data.get("title", "Milimo Quantum Experiment"),
        code_cells=data.get("code_cells"),
        markdown_cells=data.get("markdown_cells"),
    )
    nb_bytes = notebook.notebook_to_bytes(nb)

    return Response(
        content=nb_bytes,
        media_type="application/x-ipynb+json",
        headers={
            "Content-Disposition": 'attachment; filename="experiment.ipynb"',
        },
    )
