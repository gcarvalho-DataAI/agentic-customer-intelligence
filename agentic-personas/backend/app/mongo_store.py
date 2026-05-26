from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pymongo import MongoClient

from .config import settings


def _collection():
    client = MongoClient(settings.mongo_uri)
    db = client[settings.mongo_db]
    return db[settings.mongo_collection]


def create_conversation(title: str | None = None) -> dict[str, Any]:
    now = datetime.now(UTC)
    conversation_id = str(uuid4())
    doc = {
        "conversation_id": conversation_id,
        "title": title or "New conversation",
        "messages": [],
        "created_at": now,
        "updated_at": now,
    }
    _collection().insert_one(doc)
    return {
        "conversation_id": conversation_id,
        "title": doc["title"],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "message_count": 0,
    }


def list_conversations(limit: int = 50) -> list[dict[str, Any]]:
    rows = _collection().find({}, {"_id": 0}).sort("updated_at", -1).limit(limit)
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "conversation_id": row["conversation_id"],
                "title": row.get("title", "New conversation"),
                "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
                "message_count": len(row.get("messages", [])),
            }
        )
    return out


def get_conversation(conversation_id: str) -> dict[str, Any] | None:
    row = _collection().find_one({"conversation_id": conversation_id}, {"_id": 0})
    if not row:
        return None
    return {
        "conversation_id": row["conversation_id"],
        "title": row.get("title", "New conversation"),
        "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
        "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
        "messages": row.get("messages", []),
    }


def append_message(conversation_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> bool:
    now = datetime.now(UTC).isoformat()
    message_id = str(uuid4())
    update = {
        "$push": {
            "messages": {
                "message_id": message_id,
                "timestamp": now,
                "role": role,
                "content": content,
                "metadata": metadata or {},
            }
        },
        "$set": {"updated_at": datetime.now(UTC)},
    }
    result = _collection().update_one({"conversation_id": conversation_id}, update)
    return result.matched_count > 0


def delete_conversation(conversation_id: str) -> bool:
    result = _collection().delete_one({"conversation_id": conversation_id})
    return result.deleted_count > 0


def update_conversation_title(conversation_id: str, title: str) -> bool:
    result = _collection().update_one(
        {"conversation_id": conversation_id},
        {"$set": {"title": title, "updated_at": datetime.now(UTC)}},
    )
    return result.matched_count > 0


def clear_conversation_messages(conversation_id: str) -> bool:
    result = _collection().update_one(
        {"conversation_id": conversation_id},
        {"$set": {"messages": [], "updated_at": datetime.now(UTC)}},
    )
    return result.matched_count > 0


def get_recent_messages(conversation_id: str, limit: int) -> list[dict[str, Any]]:
    row = _collection().find_one({"conversation_id": conversation_id}, {"_id": 0, "messages": 1})
    if not row:
        return []
    messages = row.get("messages", [])
    if limit <= 0:
        return []
    return messages[-limit:]


def start_partial_assistant_message(
    conversation_id: str,
    cluster_id: int,
    segment_name: str,
    retrieved_docs: list[dict[str, Any]],
) -> str:
    now = datetime.now(UTC).isoformat()
    message_id = str(uuid4())
    update = {
        "$push": {
            "messages": {
                "message_id": message_id,
                "timestamp": now,
                "role": "assistant",
                "content": "",
                "metadata": {
                    "cluster_id": cluster_id,
                    "segment_name": segment_name,
                    "retrieved_docs": retrieved_docs,
                    "partial": True,
                },
            }
        },
        "$set": {"updated_at": datetime.now(UTC)},
    }
    _collection().update_one({"conversation_id": conversation_id}, update)
    return message_id


def update_partial_assistant_message(
    conversation_id: str,
    message_id: str,
    content: str,
) -> bool:
    result = _collection().update_one(
        {"conversation_id": conversation_id, "messages.message_id": message_id},
        {
            "$set": {
                "messages.$.content": content,
                "messages.$.timestamp": datetime.now(UTC).isoformat(),
                "updated_at": datetime.now(UTC),
            }
        },
    )
    return result.matched_count > 0


def finalize_partial_assistant_message(
    conversation_id: str,
    message_id: str,
    content: str,
    partial: bool,
) -> bool:
    result = _collection().update_one(
        {"conversation_id": conversation_id, "messages.message_id": message_id},
        {
            "$set": {
                "messages.$.content": content,
                "messages.$.timestamp": datetime.now(UTC).isoformat(),
                "messages.$.metadata.partial": partial,
                "updated_at": datetime.now(UTC),
            }
        },
    )
    return result.matched_count > 0
