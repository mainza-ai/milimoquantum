"""Milimo Quantum — Experiment Versioning & Run Registry.

Git-like versioning for quantum experiments. Every circuit execution is
logged with full reproducibility metadata: circuit snapshot, backend,
shots, transpile options, error mitigation settings, and results.
"""
from __future__ import annotations

import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REGISTRY_DIR = Path.home() / ".milimoquantum" / "experiments"


def _ensure_dir() -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)


def _experiment_dir(project: str) -> Path:
    d = REGISTRY_DIR / project
    d.mkdir(parents=True, exist_ok=True)
    return d


def log_run(
    project: str = "default",
    circuit_name: str = "",
    circuit_code: str = "",
    backend: str = "aer_simulator",
    shots: int = 1024,
    mitigation: str | None = None,
    transpile_options: dict | None = None,
    results: dict | None = None,
    tags: list[str] | None = None,
    notes: str = "",
    parent_run_id: str | None = None,
) -> dict:
    """Log a quantum circuit execution to the run registry.

    Returns the run metadata with a unique run_id.
    """
    from app.db.local_cache import get_local_session
    from app.db.models import Experiment
    from app.experiments.sync_engine import broadcast_p2p
    import asyncio

    now = datetime.utcnow()
    hash_input = f"{circuit_code}{now.isoformat()}{shots}".encode()
    run_id = hashlib.sha256(hash_input).hexdigest()[:12]

    # Save to local SQLite explicitly
    session = get_local_session()
    try:
        exp = Experiment(
            id=run_id,
            project=project,
            name=circuit_name,
            circuit_code=circuit_code,
            backend=backend,
            shots=shots,
            results=results or {},
            tags=tags or [],
            parameters={
                "mitigation": mitigation,
                "transpile_options": transpile_options or {},
                "notes": notes,
                "version": 1,
                "parent_run_id": parent_run_id,
                "comments": [],
                "shared_with": []
            },
            created_at=now,
            is_synced=False,
        )
        session.add(exp)
        session.commit()
        logger.info(f"Logged run {run_id} for project '{project}' (Local Cache)")

        return {
            "run_id": run_id,
            "project": project,
            "circuit_name": circuit_name,
            "circuit_code": circuit_code,
            "backend": backend,
            "shots": shots,
            "mitigation": mitigation,
            "transpile_options": transpile_options or {},
            "results": results or {},
            "tags": tags or [],
            "notes": notes,
            "timestamp": now.isoformat(),
            "version": 1,
            "parent_run_id": parent_run_id,
            "comments": [],
            "shared_with": []
        }
        
        # Fire-and-forget broadcast via event loop if available
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcast_p2p(run_data))
        except RuntimeError:
            pass # No running loop (e.g. CLI script)
            
        return run_data
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to log run {run_id}: {e}")
        return {}
    finally:
        session.close()


def get_run(project: str, run_id: str) -> dict | None:
    """Retrieve a specific run by ID."""
    from app.db import get_session
    from app.db.models import Experiment

    session = get_session()
    try:
        exp = session.query(Experiment).filter_by(project=project, id=run_id).first()
        if not exp:
            return None
        return {
            "run_id": exp.id,
            "project": exp.project,
            "circuit_name": exp.name or "",
            "circuit_code": exp.circuit_code or "",
            "backend": exp.backend,
            "shots": exp.shots,
            "mitigation": exp.parameters.get("mitigation"),
            "transpile_options": exp.parameters.get("transpile_options", {}),
            "results": exp.results,
            "tags": exp.tags,
            "notes": exp.parameters.get("notes", ""),
            "timestamp": exp.created_at.isoformat(),
            "version": exp.parameters.get("version", 1),
            "parent_run_id": exp.parameters.get("parent_run_id"),
            "comments": exp.parameters.get("comments", []),
            "shared_with": exp.parameters.get("shared_with", [])
        }
    finally:
        session.close()


def list_runs(project: str = "default", limit: int = 50) -> list[dict]:
    """List recent runs for a project (most recent first)."""
    from app.db import get_session
    from app.db.models import Experiment

    session = get_session()
    try:
        exps = session.query(Experiment).filter_by(project=project).order_by(Experiment.created_at.desc()).limit(limit).all()
        return [
            {
                "run_id": e.id,
                "circuit_name": e.name or "",
                "backend": e.backend,
                "shots": e.shots,
                "timestamp": e.created_at.isoformat(),
                "tags": e.tags,
            }
            for e in exps
        ]
    finally:
        session.close()


def list_projects() -> list[dict]:
    """List all experiment projects."""
    from app.db import get_session
    from app.db.models import Experiment
    from sqlalchemy import func

    session = get_session()
    try:
        # SELECT project, count(id), max(created_at) FROM experiments GROUP BY project
        projects_data = session.query(
            Experiment.project,
            func.count(Experiment.id).label("run_count"),
            func.max(Experiment.created_at).label("last_modified")
        ).group_by(Experiment.project).all()

        return [
            {
                "name": p.project,
                "run_count": p.run_count,
                "last_modified": p.last_modified.isoformat() if p.last_modified else "",
            }
            for p in projects_data
        ]
    finally:
        session.close()


def compare_runs(project: str, run_id_a: str, run_id_b: str) -> dict:
    """Compare two runs — show differences in parameters and results."""
    run_a = get_run(project, run_id_a)
    run_b = get_run(project, run_id_b)

    if not run_a or not run_b:
        return {"error": "One or both runs not found"}

    diff: dict[str, Any] = {}
    for key in ("backend", "shots", "mitigation"):
        if run_a.get(key) != run_b.get(key):
            diff[key] = {"a": run_a.get(key), "b": run_b.get(key)}

    counts_a = run_a.get("results", {}).get("counts", {})
    counts_b = run_b.get("results", {}).get("counts", {})
    all_keys = set(list(counts_a.keys()) + list(counts_b.keys()))
    result_diff = {}
    for k in sorted(all_keys):
        va = counts_a.get(k, 0)
        vb = counts_b.get(k, 0)
        if va != vb:
            result_diff[k] = {"a": va, "b": vb, "delta": vb - va}

    return {
        "run_a": run_id_a,
        "run_b": run_id_b,
        "param_diff": diff,
        "result_diff": result_diff,
    }


def tag_run(project: str, run_id: str, tags: list[str]) -> dict:
    """Add tags to a run for organization."""
    from app.db import get_session
    from app.db.models import Experiment

    session = get_session()
    try:
        exp = session.query(Experiment).filter_by(project=project, id=run_id).first()
        if not exp:
            return {"error": "Run not found"}

        existing = set(exp.tags or [])
        existing.update(tags)
        exp.tags = sorted(existing)
        session.commit()
        return {"run_id": run_id, "tags": exp.tags}
    except Exception as e:
        session.rollback()
        return {"error": str(e)}
    finally:
        session.close()


def add_comment(project: str, run_id: str, author: str, text: str) -> dict:
    """Add a collaboration comment to a run."""
    from app.db import get_session
    from app.db.models import Experiment

    session = get_session()
    try:
        exp = session.query(Experiment).filter_by(project=project, id=run_id).first()
        if not exp:
            return {"error": "Run not found"}

        params = exp.parameters or {}
        comments = params.get("comments", [])
        
        # We need to explicitly copy lists/dicts for SQLAlchemy JSON fields to detect changes
        new_comments = list(comments)
        new_comments.append({
            "author": author,
            "text": text,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        new_params = dict(params)
        new_params["comments"] = new_comments
        exp.parameters = new_params
        
        session.commit()
        return {"run_id": run_id, "comments": exp.parameters["comments"]}
    except Exception as e:
        session.rollback()
        return {"error": str(e)}
    finally:
        session.close()


def share_run(project: str, run_id: str, user_id: str) -> dict:
    """Add a user to the shared_with list for a run."""
    from app.db import get_session
    from app.db.models import Experiment

    session = get_session()
    try:
        exp = session.query(Experiment).filter_by(project=project, id=run_id).first()
        if not exp:
            return {"error": "Run not found"}

        params = exp.parameters or {}
        shared_with = params.get("shared_with", [])
        
        if user_id not in shared_with:
            new_shared = list(shared_with)
            new_shared.append(user_id)
            
            new_params = dict(params)
            new_params["shared_with"] = new_shared
            exp.parameters = new_params
            
            session.commit()
            
        return {"run_id": run_id, "shared_with": exp.parameters["shared_with"]}
    except Exception as e:
        session.rollback()
        return {"error": str(e)}
    finally:
        session.close()


def get_lineage(project: str, run_id: str) -> dict:
    """Reconstruct the ancestral tree for a specific run."""
    from app.db import get_session
    from app.db.models import Experiment

    session = get_session()
    try:
        # Start from the requested run and walk upwards to find all ancestors
        all_runs = session.query(Experiment).filter_by(project=project).all()
        
        run_map = {r.id: r for r in all_runs}
        if run_id not in run_map:
            return {"error": "Run not found"}
            
        nodes = []
        edges = []
        
        current_id = run_id
        visited = set()
        
        # Traverse upwards to the root
        while current_id and current_id in run_map and current_id not in visited:
            visited.add(current_id)
            exp = run_map[current_id]
            
            nodes.append({
                "id": exp.id,
                "label": exp.name or "Untitled Run",
                "backend": exp.backend,
                "timestamp": exp.created_at.isoformat()
            })
            
            parent_id = exp.parameters.get("parent_run_id")
            if parent_id:
                edges.append({"source": parent_id, "target": current_id})
            
            current_id = parent_id
            
        # Reverse to show chronological order (root first)
        nodes.reverse()
        edges.reverse()
        
        return {
            "root_run_id": nodes[0]["id"] if nodes else None,
            "target_run_id": run_id,
            "graph": {
                "nodes": nodes,
                "edges": edges
            }
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()

