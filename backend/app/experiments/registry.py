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
) -> dict:
    """Log a quantum circuit execution to the run registry.

    Returns the run metadata with a unique run_id.
    """
    _ensure_dir()

    # Generate run ID from hash of circuit + timestamp
    now = datetime.utcnow()
    hash_input = f"{circuit_code}{now.isoformat()}{shots}".encode()
    run_id = hashlib.sha256(hash_input).hexdigest()[:12]

    run_entry = {
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
    }

    # Save to project directory
    exp_dir = _experiment_dir(project)
    filepath = exp_dir / f"{run_id}.json"
    filepath.write_text(json.dumps(run_entry, indent=2, default=str))

    # Also append to run log index
    log_file = exp_dir / "_run_log.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps({
            "run_id": run_id,
            "circuit_name": circuit_name,
            "backend": backend,
            "shots": shots,
            "timestamp": now.isoformat(),
        }) + "\n")

    logger.info(f"Logged run {run_id} for project '{project}'")
    return run_entry


def get_run(project: str, run_id: str) -> dict | None:
    """Retrieve a specific run by ID."""
    filepath = _experiment_dir(project) / f"{run_id}.json"
    if not filepath.exists():
        return None
    return json.loads(filepath.read_text())


def list_runs(project: str = "default", limit: int = 50) -> list[dict]:
    """List recent runs for a project (most recent first)."""
    exp_dir = _experiment_dir(project)
    runs = []
    for filepath in sorted(exp_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if filepath.name.startswith("_"):
            continue
        try:
            data = json.loads(filepath.read_text())
            runs.append({
                "run_id": data["run_id"],
                "circuit_name": data.get("circuit_name", ""),
                "backend": data.get("backend", ""),
                "shots": data.get("shots", 0),
                "timestamp": data.get("timestamp", ""),
                "tags": data.get("tags", []),
            })
        except (json.JSONDecodeError, KeyError):
            continue
        if len(runs) >= limit:
            break
    return runs


def list_projects() -> list[dict]:
    """List all experiment projects."""
    _ensure_dir()
    projects = []
    for d in sorted(REGISTRY_DIR.iterdir()):
        if d.is_dir():
            run_count = len(list(d.glob("*.json"))) - len(list(d.glob("_*.json")))
            projects.append({
                "name": d.name,
                "run_count": run_count,
                "last_modified": datetime.fromtimestamp(d.stat().st_mtime).isoformat(),
            })
    return projects


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
    filepath = _experiment_dir(project) / f"{run_id}.json"
    if not filepath.exists():
        return {"error": "Run not found"}

    data = json.loads(filepath.read_text())
    existing = set(data.get("tags", []))
    existing.update(tags)
    data["tags"] = sorted(existing)
    filepath.write_text(json.dumps(data, indent=2, default=str))
    return {"run_id": run_id, "tags": data["tags"]}
