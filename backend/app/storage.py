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
    """Save a conversation to disk."""
    _ensure_dir()
    filepath = STORAGE_DIR / f"{conversation_id}.json"

    # Auto-title from first user message
    if not title:
        for msg in messages:
            if msg.get("role") == "user":
                title = msg["content"][:60].strip()
                if len(msg["content"]) > 60:
                    title += "…"
                break
    if not title:
        title = "New Conversation"

    data = {
        "id": conversation_id,
        "title": title,
        "messages": messages,
        "message_count": len(messages),
        "created_at": _get_created_at(filepath),
        "updated_at": datetime.utcnow().isoformat(),
    }

    filepath.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    logger.debug(f"Saved conversation {conversation_id} ({len(messages)} messages)")


def load_conversation(conversation_id: str) -> dict | None:
    """Load a conversation from disk."""
    _ensure_dir()
    filepath = STORAGE_DIR / f"{conversation_id}.json"
    if not filepath.exists():
        return None
    try:
        return json.loads(filepath.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to load conversation {conversation_id}: {e}")
        return None


def list_conversations() -> list[dict]:
    """List all saved conversations with summary info."""
    _ensure_dir()
    convos = []
    for filepath in sorted(STORAGE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            convos.append({
                "id": data.get("id", filepath.stem),
                "title": data.get("title", "Untitled"),
                "message_count": data.get("message_count", 0),
                "updated_at": data.get("updated_at", ""),
                "created_at": data.get("created_at", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return convos


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation from disk."""
    _ensure_dir()
    filepath = STORAGE_DIR / f"{conversation_id}.json"
    if filepath.exists():
        filepath.unlink()
        logger.info(f"Deleted conversation {conversation_id}")
        return True
    return False


def _get_created_at(filepath: Path) -> str:
    """Get or preserve the created_at timestamp."""
    if filepath.exists():
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            return data.get("created_at", datetime.utcnow().isoformat())
        except (json.JSONDecodeError, OSError):
            pass
    return datetime.utcnow().isoformat()
