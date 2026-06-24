# core/search_manager.py
#
# Provides global search across collections, sessions, messages, and documents.
# Uses SQL LIKE for keyword matching; no external dependencies.

from __future__ import annotations

import sqlite3
from typing import List, Dict, Any

from core.session_manager import session_db


def global_search(user_id: str, query: str, collection_id: int = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search across collections, sessions, messages, and documents.
    Returns grouped results by category.
    """
    if not query or not query.strip():
        return {"collections": [], "sessions": [], "messages": [], "documents": []}

    # Escape SQLite LIKE wildcards so user-supplied '%' or '_' are matched
    # literally instead of acting as wildcards.
    raw = query.strip()
    escaped = raw.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    term = f"%{escaped}%"
    results = {"collections": [], "sessions": [], "messages": [], "documents": []}

    with session_db._get_connection() as conn:
        # Collections
        if collection_id:
            cursor = conn.execute(
                "SELECT id, name, created_at FROM collections WHERE user_id = ? AND id = ? AND name LIKE ? ESCAPE '\\'",
                (user_id, collection_id, term)
            )
        else:
            cursor = conn.execute(
                "SELECT id, name, created_at FROM collections WHERE user_id = ? AND name LIKE ? ESCAPE '\\'",
                (user_id, term)
            )
        results["collections"] = [dict(row) for row in cursor.fetchall()]

        # Sessions
        if collection_id:
            cursor = conn.execute(
                "SELECT id, name, created_at, collection_id FROM sessions WHERE user_id = ? AND collection_id = ? AND name LIKE ? ESCAPE '\\'",
                (user_id, collection_id, term)
            )
        else:
            cursor = conn.execute(
                "SELECT id, name, created_at, collection_id FROM sessions WHERE user_id = ? AND name LIKE ? ESCAPE '\\'",
                (user_id, term)
            )
        results["sessions"] = [dict(row) for row in cursor.fetchall()]

        # Messages
        if collection_id:
            cursor = conn.execute(
                """SELECT m.id, m.session_id, m.role, m.content, m.timestamp, s.name as session_name
                   FROM messages m
                   JOIN sessions s ON m.session_id = s.id
                   WHERE s.user_id = ? AND s.collection_id = ? AND m.content LIKE ? ESCAPE '\\'""",
                (user_id, collection_id, term)
            )
        else:
            cursor = conn.execute(
                """SELECT m.id, m.session_id, m.role, m.content, m.timestamp, s.name as session_name
                   FROM messages m
                   JOIN sessions s ON m.session_id = s.id
                   WHERE s.user_id = ? AND m.content LIKE ? ESCAPE '\\'""",
                (user_id, term)
            )
        results["messages"] = [dict(row) for row in cursor.fetchall()]

        # Documents (collection_documents)
        if collection_id:
            cursor = conn.execute(
                "SELECT id, filename, uploaded_at FROM collection_documents WHERE user_id = ? AND collection_id = ? AND filename LIKE ? ESCAPE '\\'",
                (user_id, collection_id, term)
            )
        else:
            cursor = conn.execute(
                "SELECT id, filename, uploaded_at FROM collection_documents WHERE user_id = ? AND filename LIKE ? ESCAPE '\\'",
                (user_id, term)
            )
        results["documents"] = [dict(row) for row in cursor.fetchall()]

    return results
