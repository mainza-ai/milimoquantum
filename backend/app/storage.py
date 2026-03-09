"""Milimo Quantum — Conversation Storage.

JSON file-based persistence for conversations.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

STORAGE_DIR = Path.home() / ".milimoquantum" / "conversations"


def _ensure_dir():
    """Ensure the storage directory exists."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_conversation(conversation_id: str, messages: list[dict], title: str | None = None, is_new_append: bool = False) -> None:
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
        # 1. Update Conversation Meta
        conv = session.query(Conversation).filter_by(id=conversation_id).first()
        if not conv:
            conv = Conversation(id=conversation_id, title=title)
            session.add(conv)
        else:
            conv.title = title
            conv.updated_at = datetime.utcnow()

        # 2. Map existing messages for quick lookup
        # If it's a new append stream, only process the last 2 messages (user + assistant) to avoid destructive re-inserts and O(N) looping
        messages_to_process = messages[-2:] if is_new_append and len(messages) >= 2 else messages
        existing_messages = {m.id: m for m in conv.messages} if conv else {}

        # 3. Process messages
        for msg in messages_to_process:
            m_id = msg.get("id") or _uuid()
            role = msg["role"]
            content = msg["content"]
            agent = msg.get("agent")
            timestamp = datetime.fromisoformat(msg["timestamp"]) if msg.get("timestamp") else datetime.utcnow()

            if m_id in existing_messages:
                # Update existing message if content changed
                db_msg = existing_messages[m_id]
                if db_msg.content != content:
                    db_msg.content = content
                    db_msg.timestamp = timestamp # Useful for streaming updates
            else:
                # Insert new message
                db_msg = Message(
                    id=m_id,
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    agent=agent,
                    timestamp=timestamp,
                )
                session.add(db_msg)
            
            # 4. Sync artifacts for this message
            incoming_artifacts = msg.get("artifacts", [])
            if incoming_artifacts:
                existing_art_ids = {a.id for a in db_msg.artifacts}
                for art in incoming_artifacts:
                    a_id = art.get("id") or _uuid()
                    if a_id not in existing_art_ids:
                        db_art = Artifact(
                            id=a_id,
                            message_id=db_msg.id,
                            type=art["type"],
                            title=art.get("title"),
                            content=art.get("content"),
                            language=art.get("language"),
                            metadata_=art.get("metadata", {}),
                        )
                        session.add(db_art)

        conv.message_count = len(messages)
        session.commit()
        logger.debug(f"Saved conversation {conversation_id} (Differential sync complete)")
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
                        "metadata": dict(art.metadata_ or {}),
                    }
                    for art in msg.artifacts
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
