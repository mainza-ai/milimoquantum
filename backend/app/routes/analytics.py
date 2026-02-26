"""Milimo Quantum — Analytics Dashboard Routes.

Aggregate statistics for experiments, conversations, agent usage,
and circuit complexity.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from collections import Counter
from typing import Counter as TypingCounter

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

STORAGE_DIR = Path.home() / ".milimoquantum"
CONVERSATIONS_DIR = STORAGE_DIR / "conversations"
PROJECTS_DIR = STORAGE_DIR / "projects"


# ── Summary Stats ──────────────────────────────────────
@router.get("/summary")
async def analytics_summary():
    """Overall platform usage statistics."""
    # Try database first (PostgreSQL)
    try:
        from app.db import get_session
        from app.db.models import Conversation, Message, Artifact
        session = get_session()
        try:
            conv_count = session.query(Conversation).count()
            message_count = session.query(Message).count()
            circuit_count = session.query(Artifact).filter(
                Artifact.type.in_(["circuit", "code", "results"])
            ).count()

            # Agent usage from messages
            agent_counter: TypingCounter[str] = Counter()
            agents = session.query(Message.agent).filter(Message.agent.isnot(None)).all()
            for (agent,) in agents:
                agent_counter[agent] += 1

            # Project count
            project_count = 0
            if PROJECTS_DIR.exists():
                project_count = len(list(PROJECTS_DIR.glob("*.json")))

            return {
                "conversations": conv_count,
                "messages": message_count,
                "projects": project_count,
                "circuits_generated": circuit_count,
                "agents_used": dict(agent_counter.most_common()),
                "top_agent": agent_counter.most_common(1)[0][0] if agent_counter else None,
            }
        finally:
            session.close()
    except Exception as e:
        logger.debug(f"DB analytics fallback: {e}")

    # Fallback: JSON files
    conv_count = 0
    message_count = 0
    agent_counter: TypingCounter[str] = Counter()
    circuit_count = 0

    if CONVERSATIONS_DIR.exists():
        for filepath in CONVERSATIONS_DIR.glob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                conv_count += 1
                messages = data.get("messages", [])
                message_count += len(messages)

                for msg in messages:
                    agent = msg.get("agent")
                    if agent:
                        agent_counter[agent] += 1
                    artifacts = msg.get("artifacts", [])
                    for art in artifacts:
                        if art.get("type") in ("circuit", "code"):
                            circuit_count += 1
            except (json.JSONDecodeError, OSError):
                continue

    project_count = 0
    if PROJECTS_DIR.exists():
        project_count = len(list(PROJECTS_DIR.glob("*.json")))

    return {
        "conversations": conv_count,
        "messages": message_count,
        "projects": project_count,
        "circuits_generated": circuit_count,
        "agents_used": dict(agent_counter.most_common()),
        "top_agent": agent_counter.most_common(1)[0][0] if agent_counter else None,
    }


# ── Agent Usage Breakdown ──────────────────────────────
@router.get("/agents")
async def agent_usage():
    """Per-agent usage breakdown."""
    agent_counter: TypingCounter[str] = Counter()
    agent_msgs: dict[str, int] = {}

    if CONVERSATIONS_DIR.exists():
        for filepath in CONVERSATIONS_DIR.glob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                for msg in data.get("messages", []):
                    agent = msg.get("agent")
                    if agent:
                        agent_counter[agent] += 1
                        if agent not in agent_msgs:
                            agent_msgs[agent] = 0
                        content = msg.get("content", "")
                        agent_msgs[agent] += len(content)
            except (json.JSONDecodeError, OSError):
                continue

    agents = []
    total = sum(agent_counter.values()) or 1
    for agent, count in agent_counter.most_common():
        agents.append({
            "agent": agent,
            "messages": count,
            "percentage": round(float(count) / float(total) * 100.0, 1),
            "total_chars": agent_msgs.get(agent, 0),
        })

    return {"agents": agents, "total_messages": sum(agent_counter.values())}


# ── Circuit Complexity Distribution ────────────────────
@router.get("/circuits")
async def circuit_stats():
    """Circuit metadata collected from conversation artifacts."""
    qubit_counts: list[int] = []
    depth_counts: list[int] = []
    circuit_types: TypingCounter[str] = Counter()

    if CONVERSATIONS_DIR.exists():
        for filepath in CONVERSATIONS_DIR.glob("*.json"):
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                for msg in data.get("messages", []):
                    for art in msg.get("artifacts", []):
                        meta = art.get("metadata", {})
                        if meta.get("num_qubits"):
                            qubit_counts.append(int(meta["num_qubits"]))
                        if meta.get("depth"):
                            depth_counts.append(int(meta["depth"]))
                        if art.get("type"):
                            circuit_types[art["type"]] += 1
            except (json.JSONDecodeError, OSError, ValueError):
                continue

    return {
        "total_circuits": len(qubit_counts),
        "qubit_distribution": {
            "min": min(qubit_counts) if qubit_counts else 0,
            "max": max(qubit_counts) if qubit_counts else 0,
            "avg": round(float(sum(qubit_counts)) / len(qubit_counts), 1) if qubit_counts else 0,
        },
        "depth_distribution": {
            "min": min(depth_counts) if depth_counts else 0,
            "max": max(depth_counts) if depth_counts else 0,
            "avg": round(float(sum(depth_counts)) / len(depth_counts), 1) if depth_counts else 0,
        },
        "artifact_types": dict(circuit_types.most_common()),
    }


# ── Recent Activity Timeline ──────────────────────────
@router.get("/activity")
async def recent_activity(limit: int = 20):
    """Recent conversation activity, newest first."""
    activities = []

    if CONVERSATIONS_DIR.exists():
        files = list(CONVERSATIONS_DIR.glob("*.json"))
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        files = files[:limit]

        for filepath in files:
            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                msg_count = len(data.get("messages", []))
                last_agent = None
                for msg in reversed(data.get("messages", [])):
                    if msg.get("agent"):
                        last_agent = msg["agent"]
                        break

                activities.append({
                    "id": data.get("id", filepath.stem),
                    "title": data.get("title", "Untitled"),
                    "messages": msg_count,
                    "last_agent": last_agent,
                    "updated_at": data.get("updated_at", ""),
                    "created_at": data.get("created_at", ""),
                })
            except (json.JSONDecodeError, OSError):
                continue

    return {"activities": activities}
