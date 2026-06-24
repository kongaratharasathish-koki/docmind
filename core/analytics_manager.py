# core/analytics_manager.py
#
# Provides dashboard statistics for the user's workspace.
# All queries are user-scoped for security.

from __future__ import annotations

from typing import Dict, Any, Optional

from core.session_manager import session_db


def get_analytics(user_id: str) -> Dict[str, Any]:
    """
    Compute workspace analytics for the given user.
    Returns counts and metadata for dashboard display.

    Consolidated into a single SQLite roundtrip per metric (4 queries
    total instead of 5) — minor, but eliminates one query path.
    """
    analytics = {
        "total_documents": 0,
        "total_libraries": 0,
        "total_sessions": 0,
        "total_messages": 0,
        "top_collection": None,
        "last_active": None,
    }

    with session_db._get_connection() as conn:
        # One roundtrip for the four scalar counts via UNION ALL.
        row = conn.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM collections
                 WHERE user_id = :uid AND archived_at IS NULL) AS total_libraries,
              (SELECT COUNT(*) FROM sessions
                 WHERE user_id = :uid) AS total_sessions,
              (SELECT COUNT(*) FROM messages m
                 JOIN sessions s ON m.session_id = s.id
                 WHERE s.user_id = :uid) AS total_messages,
              (SELECT COUNT(*) FROM collection_documents
                 WHERE user_id = :uid) AS total_documents,
              (SELECT MAX(uploaded_at) FROM collection_documents
                 WHERE user_id = :uid) AS last_active
            """,
            {"uid": user_id},
        ).fetchone()

        if row:
            analytics["total_libraries"] = row["total_libraries"] or 0
            analytics["total_sessions"] = row["total_sessions"] or 0
            analytics["total_messages"] = row["total_messages"] or 0
            analytics["total_documents"] = row["total_documents"] or 0
            analytics["last_active"] = row["last_active"]

        # Top collection — still a separate query because LIMIT 1 + ORDER BY.
        row = conn.execute(
            """SELECT c.id, c.name, COUNT(cd.id) as doc_count
               FROM collections c
               LEFT JOIN collection_documents cd ON c.id = cd.collection_id
               WHERE c.user_id = ? AND c.archived_at IS NULL
               GROUP BY c.id
               ORDER BY doc_count DESC
               LIMIT 1""",
            (user_id,)
        ).fetchone()
        if row and row["doc_count"] > 0:
            analytics["top_collection"] = {
                "id": row["id"],
                "name": row["name"],
                "document_count": row["doc_count"],
            }

    return analytics
