# app/services/library_service.py
#
# Business logic for libraries (collections).
# Routers call this; this module calls core.collection_manager + core.document_storage.

from __future__ import annotations

from typing import List, Dict, Any, Optional

from core.collection_manager import (
    create_collection,
    list_collections,
    archive_collection,
    get_metadata,
    ensure_metadata_exists,
)
from core.session_manager import session_db


def create_library(user_id: str, name: str) -> Dict[str, Any]:
    cid = create_collection(user_id, name)
    ensure_metadata_exists(cid)
    return {
        "id": cid,
        "name": name,
        "document_count": 0,
    }


def list_libraries(user_id: str, include_archived: bool = False) -> List[Dict[str, Any]]:
    """
    Single-query fetch: collections LEFT JOIN collection_metadata so we
    don't N+1 into the metadata table per library.
    """
    archive_clause = "" if include_archived else "AND c.archived_at IS NULL"
    with session_db._get_connection() as conn:
        cursor = conn.execute(
            f"""
            SELECT c.id, c.name, c.archived_at, c.created_at, c.updated_at,
                   COALESCE(m.document_count, 0) AS document_count
            FROM collections c
            LEFT JOIN collection_metadata m ON m.collection_id = c.id
            WHERE c.user_id = ? {archive_clause}
            ORDER BY c.updated_at DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def delete_library(user_id: str, library_id: int) -> bool:
    """Archive a library. Returns True only if a row was actually archived."""
    return archive_collection(library_id, user_id)
