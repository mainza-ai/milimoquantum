"""Milimo Quantum — Conversation Export Routes."""
from __future__ import annotations

import csv
import io
import json
import logging

from app.auth import get_current_user
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app import storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/export", tags=["export"], dependencies=[Depends(get_current_user)])


@router.get("/conversations/{conversation_id}")
async def export_conversation(conversation_id: str, format: str = "json"):
    """Export a conversation as JSON or CSV.

    Query params:
        format: 'json' (default) or 'csv'
    """
    data = storage.load_conversation(conversation_id)
    if not data:
        return Response(content="Conversation not found", status_code=404)

    messages = data.get("messages", [])
    title = data.get("title", "Untitled")

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["#", "role", "content_preview", "length"])
        for i, msg in enumerate(messages, 1):
            content = msg.get("content", "")
            preview = content[:200].replace("\n", " ")
            writer.writerow([i, msg.get("role", ""), preview, len(content)])
        csv_bytes = output.getvalue().encode("utf-8")
        filename = f"milimoquantum_{conversation_id[:8]}.csv"
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        export_data = {
            "id": conversation_id,
            "title": title,
            "message_count": len(messages),
            "created_at": data.get("created_at", ""),
            "updated_at": data.get("updated_at", ""),
            "messages": [
                {
                    "role": msg.get("role", ""),
                    "content": msg.get("content", ""),
                }
                for msg in messages
            ],
        }
        json_bytes = json.dumps(export_data, indent=2, ensure_ascii=False).encode("utf-8")
        filename = f"milimoquantum_{conversation_id[:8]}.json"
        return Response(
            content=json_bytes,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
