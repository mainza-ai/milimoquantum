"""Milimo Quantum — Conversation Storage.

JSON file-based persistence for conversations.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STORAGE_DIR = Path.home() / ".milimoquantum" / "conversations"


def _ensure_dir():
    """Ensure the storage directory exists."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_conversation(conversation_id: str, messages: list[dict], title: str | None = None) -> None:
    """Save a conversation to the database."""
    from app.db import get_session
    from app.db.models import Conversation, Message, Artifact

    if not title:
        for msg in messages:
            if msg.get("role") == "user":
                title = msg["content"][:60].strip()
                if len(msg["content"]) > 60:
                    title += "…"
                break
    if not title:
        title = "New Conversation"

    session = get_session()
    try:
        # Check if conversation exists
        conv = session.query(Conversation).filter_by(id=conversation_id).first()
        if not conv:
            conv = Conversation(id=conversation_id, title=title)
            session.add(conv)
        else:
            conv.title = title
            conv.message_count = len(messages)
            conv.updated_at = datetime.utcnow()
            # Delete existing messages to rewrite
            session.query(Message).filter_by(conversation_id=conversation_id).delete()

        # Add messages
        for msg in messages:
            db_msg = Message(
                id=msg.get("id") or _uuid(),
                conversation_id=conversation_id,
                role=msg["role"],
                content=msg["content"],
                agent=msg.get("agent"),
                timestamp=datetime.fromisoformat(msg["timestamp"]) if msg.get("timestamp") else datetime.utcnow(),
            )
            session.add(db_msg)
            
            # Add artifacts if any
            artifacts = msg.get("artifacts", [])
            for art in artifacts:
                db_art = Artifact(
                    id=art.get("id") or _uuid(),
                    message_id=db_msg.id,
                    type=art["type"],
                    title=art.get("title"),
                    content=art.get("content"),
                    language=art.get("language"),
                )
                session.add(db_art)

        conv.message_count = len(messages)
        session.commit()
        logger.debug(f"Saved conversation {conversation_id} ({len(messages)} messages)")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save conversation {conversation_id}: {e}")
    finally:
        session.close()


def load_conversation(conversation_id: str) -> dict | None:
    """Load a conversation from the database."""
    from app.db import get_session
    from app.db.models import Conversation

    session = get_session()
    try:
        conv = session.query(Conversation).filter_by(id=conversation_id).first()
        if not conv:
            return None

        messages = []
        for msg in sorted(conv.messages, key=lambda m: m.timestamp):
            msg_dict = {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "agent": msg.agent,
                "timestamp": msg.timestamp.isoformat(),
            }
            if msg.artifacts:
                msg_dict["artifacts"] = [
                    {
                        "id": art.id,
                        "type": art.type,
                        "title": art.title,
                        "content": art.content,
                        "language": art.language,
                    }
                    for art in art.artifacts
                ]
            messages.append(msg_dict)

        return {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
            "message_count": conv.message_count,
            "messages": messages,
        }
    except Exception as e:
        logger.error(f"Failed to load conversation {conversation_id}: {e}")
        return None
    finally:
        session.close()


def list_conversations() -> list[dict]:
    """List all saved conversations with summary info."""
    from app.db import get_session
    from app.db.models import Conversation

    session = get_session()
    try:
        convos = session.query(Conversation).order_by(Conversation.updated_at.desc()).all()
        return [
            {
                "id": c.id,
                "title": c.title,
                "message_count": c.message_count,
                "updated_at": c.updated_at.isoformat(),
                "created_at": c.created_at.isoformat(),
            }
            for c in convos
        ]
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        return []
    finally:
        session.close()


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation from the database."""
    from app.db import get_session
    from app.db.models import Conversation

    session = get_session()
    try:
        conv = session.query(Conversation).filter_by(id=conversation_id).first()
        if conv:
            session.delete(conv)
            session.commit()
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete conversation {conversation_id}: {e}")
        return False
    finally:
        session.close()

def _uuid() -> str:
    import uuid
    return str(uuid.uuid4())
