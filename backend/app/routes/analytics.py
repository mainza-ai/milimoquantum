"""Milimo Quantum — Analytics Dashboard Routes.

Aggregate statistics for experiments, conversations, agent usage,
and circuit complexity via PostgreSQL.
"""
from __future__ import annotations

import logging
from collections import Counter

from app.auth import get_current_user
from fastapi import APIRouter, Depends
from sqlalchemy import func, desc

from app.db import get_session
from app.db.models import Conversation, Message, Artifact, Project

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"], dependencies=[Depends(get_current_user)])


@router.get("/summary")
async def analytics_summary():
    """Overall platform usage statistics."""
    session = get_session()
    try:
        conv_count = session.query(Conversation).count()
        message_count = session.query(Message).count()
        circuit_count = session.query(Artifact).filter(
            Artifact.type.in_(["circuit", "code", "results"])
        ).count()
        project_count = session.query(Project).count()

        agent_counter = Counter()
        agents = session.query(Message.agent).filter(Message.agent.isnot(None)).all()
        for (agent,) in agents:
            agent_counter[agent] += 1

        top_agent = agent_counter.most_common(1)[0][0] if agent_counter else None

        return {
            "conversations": conv_count,
            "messages": message_count,
            "projects": project_count,
            "circuits_generated": circuit_count,
            "agents_used": dict(agent_counter.most_common()),
            "top_agent": top_agent,
        }
    except Exception as e:
        logger.error(f"Analytics summary error: {e}")
        return {
            "conversations": 0, "messages": 0, "projects": 0,
            "circuits_generated": 0, "agents_used": {}, "top_agent": None
        }
    finally:
        session.close()


@router.get("/agents")
async def agent_usage():
    """Per-agent usage breakdown."""
    session = get_session()
    try:
        agents_data = session.query(Message.agent, func.sum(func.length(Message.content)).label("total_chars"))\
            .filter(Message.agent.isnot(None))\
            .group_by(Message.agent).all()
        
        agent_counter = Counter()
        messages = session.query(Message.agent).filter(Message.agent.isnot(None)).all()
        for (a,) in messages:
            agent_counter[a] += 1

        total_msgs = sum(agent_counter.values()) or 1
        agent_msgs = {agent: chars or 0 for agent, chars in agents_data}

        agents = []
        for agent, count in agent_counter.most_common():
            agents.append({
                "agent": agent,
                "messages": count,
                "percentage": round(float(count) / float(total_msgs) * 100.0, 1),
                "total_chars": agent_msgs.get(agent, 0),
            })
        return {"agents": agents, "total_messages": sum(agent_counter.values())}
    except Exception as e:
        logger.error(f"Agent usage error: {e}")
        return {"agents": [], "total_messages": 0}
    finally:
        session.close()


@router.get("/circuits")
async def circuit_stats():
    """Circuit metadata collected from conversation artifacts."""
    session = get_session()
    try:
        artifacts = session.query(Artifact).filter(Artifact.metadata_.isnot(None)).all()
        qubit_counts = []
        depth_counts = []
        circuit_types = Counter()

        for art in artifacts:
            if art.type:
                circuit_types[art.type] += 1
            meta = art.metadata_ or {}
            if meta.get("num_qubits"):
                try:
                    qubit_counts.append(int(meta["num_qubits"]))
                except ValueError:
                    pass
            if meta.get("depth"):
                try:
                    depth_counts.append(int(meta["depth"]))
                except ValueError:
                    pass

        # Using int rounded values or 0 fallback
        qubit_avg = int(sum(qubit_counts) / len(qubit_counts)) if qubit_counts else 0
        depth_avg = int(sum(depth_counts) / len(depth_counts)) if depth_counts else 0

        return {
            "total_circuits": len(qubit_counts),
            "qubit_distribution": {
                "min": min(qubit_counts) if qubit_counts else 0,
                "max": max(qubit_counts) if qubit_counts else 0,
                "avg": qubit_avg,
            },
            "depth_distribution": {
                "min": min(depth_counts) if depth_counts else 0,
                "max": max(depth_counts) if depth_counts else 0,
                "avg": depth_avg,
            },
            "artifact_types": dict(circuit_types.most_common()),
        }
    except Exception as e:
        logger.error(f"Circuit stats error: {e}")
        return {
            "total_circuits": 0,
            "qubit_distribution": {"min": 0, "max": 0, "avg": 0},
            "depth_distribution": {"min": 0, "max": 0, "avg": 0},
            "artifact_types": {}
        }
    finally:
        session.close()


@router.get("/activity")
async def recent_activity(limit: int = 20):
    """Recent conversation activity, newest first."""
    session = get_session()
    try:
        convs = session.query(Conversation).order_by(desc(Conversation.updated_at)).limit(limit).all()
        activities = []
        for c in convs:
            # Find the last agent message
            last_agent = session.query(Message.agent)\
                .filter(Message.conversation_id == c.id, Message.agent.isnot(None))\
                .order_by(desc(Message.timestamp)).first()
            
            activities.append({
                "id": c.id,
                "title": c.title,
                "messages": c.message_count,
                "last_agent": last_agent[0] if last_agent else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else "",
                "created_at": c.created_at.isoformat() if c.created_at else "",
            })
        return {"activities": activities}
    except Exception as e:
        logger.error(f"Recent activity error: {e}")
        return {"activities": []}
    finally:
        session.close()
