# app/services/session_service.py
#
# Business logic for sessions (conversations).
# Routers call this; this module calls core.session_manager.

from __future__ import annotations

from typing import List, Dict, Any, Optional

from core.session_manager import session_db


def list_sessions(user_id: str) -> List[Dict[str, Any]]:
    raw = session_db.list_sessions(user_id)
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "created_at": s.get("created_at"),
            "library_id": s.get("collection_id"),
        }
        for s in raw
    ]


def create_session(user_id: str, name: str, library_id: Optional[int] = None) -> Dict[str, Any]:
    sid = session_db.create_session(user_id, name, collection_id=library_id)
    return {
        "id": sid,
        "name": name,
        "library_id": library_id,
    }


def delete_session(user_id: str, session_id: int) -> bool:
    """Delete a session. Returns True only if a row was actually deleted."""
    return session_db.delete_session(session_id, user_id)


def get_messages(user_id: str, session_id: int) -> List[Dict[str, Any]]:
    raw = session_db.load_messages(session_id, user_id)
    return [
        {
            "id": m.get("id", idx),
            "role": m["role"],
            "content": m["content"],
            "timestamp": m.get("timestamp"),
        }
        for idx, m in enumerate(raw)
    ]
