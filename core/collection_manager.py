# core/collection_manager.py
#
# Responsible for managing document collections — the top-level organizational
# unit in DocMind. Collections own documents; sessions belong to collections.
#
# Design notes:
#   - All operations are user-scoped.
#   - Archiving is soft (archived_at timestamp); permanent deletion is deferred.
#   - Document persistence is handled separately in the filesystem layer.

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.session_manager import session_db


def create_collection(user_id: str, name: str) -> int:
    """Create a new collection and return its ID."""
    with session_db._get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO collections (user_id, name) VALUES (?, ?)",
            (user_id, name)
        )
        conn.commit()
        return cursor.lastrowid


def list_collections(user_id: str, include_archived: bool = False) -> List[Dict[str, Any]]:
    """Fetch collections for a user, optionally excluding archived ones."""
    with session_db._get_connection() as conn:
        if include_archived:
            cursor = conn.execute(
                "SELECT id, name, archived_at, created_at, updated_at FROM collections WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            )
        else:
            cursor = conn.execute(
                "SELECT id, name, archived_at, created_at, updated_at FROM collections WHERE user_id = ? AND archived_at IS NULL ORDER BY updated_at DESC",
                (user_id,)
            )
        return [dict(row) for row in cursor.fetchall()]


def get_collection(collection_id: int, user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single collection by ID, ensuring it belongs to the user."""
    with session_db._get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, archived_at, created_at, updated_at FROM collections WHERE id = ? AND user_id = ?",
            (collection_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def rename_collection(collection_id: int, user_id: str, new_name: str) -> bool:
    """Rename a collection if it belongs to the user. Returns True on success."""
    with session_db._get_connection() as conn:
        cursor = conn.execute(
            "UPDATE collections SET name = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (new_name, datetime.now().isoformat(), collection_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def archive_collection(collection_id: int, user_id: str) -> bool:
    """Archive a collection (soft delete). Returns True on success."""
    with session_db._get_connection() as conn:
        cursor = conn.execute(
            "UPDATE collections SET archived_at = ?, updated_at = ? WHERE id = ? AND user_id = ? AND archived_at IS NULL",
            (datetime.now().isoformat(), datetime.now().isoformat(), collection_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def unarchive_collection(collection_id: int, user_id: str) -> bool:
    """Restore an archived collection. Returns True on success."""
    with session_db._get_connection() as conn:
        cursor = conn.execute(
            "UPDATE collections SET archived_at = NULL, updated_at = ? WHERE id = ? AND user_id = ? AND archived_at IS NOT NULL",
            (datetime.now().isoformat(), collection_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def increment_document_count(collection_id: int, count: int = 1):
    """Increment the document count in collection_metadata."""
    with session_db._get_connection() as conn:
        conn.execute(
            "UPDATE collection_metadata SET document_count = document_count + ? WHERE collection_id = ?",
            (count, collection_id)
        )
        conn.commit()


def set_last_indexed_at(collection_id: int, timestamp: str = None):
    """Update the last indexed timestamp in collection_metadata."""
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    with session_db._get_connection() as conn:
        conn.execute(
            "UPDATE collection_metadata SET last_indexed_at = ? WHERE collection_id = ?",
            (timestamp, collection_id)
        )
        conn.commit()


def get_metadata(collection_id: int) -> Optional[Dict[str, Any]]:
    """Fetch collection metadata."""
    with session_db._get_connection() as conn:
        row = conn.execute(
            "SELECT collection_id, document_count, last_indexed_at, vector_hash FROM collection_metadata WHERE collection_id = ?",
            (collection_id,)
        ).fetchone()
        return dict(row) if row else None


def ensure_metadata_exists(collection_id: int):
    """Create metadata row if it doesn't exist (idempotent)."""
    with session_db._get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO collection_metadata (collection_id) VALUES (?)",
            (collection_id,)
        )
        conn.commit()
