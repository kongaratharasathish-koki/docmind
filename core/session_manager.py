# core/session_manager.py
#
# Responsible for persisting user-scoped chat sessions and messages using SQLite.
#
# Design notes:
#   - Enforces strict data isolation using user_id on every query.
#   - Supports a multi-user schema where sessions belong to a specific user.
#   - Implements a migration path to add user_id to existing sessions.
#
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = "docmind_sessions.db"

class SessionManager:
    def __init__(self):
        self._init_db()

    def _get_connection(self):
        """Returns a sqlite3 connection with foreign key support enabled."""
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes the database schema with user-scoped tables."""
        with self._get_connection() as conn:
            # Users Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Sessions Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Messages Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)

            # Collections Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    archived_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Collection Documents Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS collection_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collection_id INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    content_hash TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Collection Metadata Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS collection_metadata (
                    collection_id INTEGER PRIMARY KEY,
                    document_count INTEGER DEFAULT 0,
                    last_indexed_at TIMESTAMP NULL,
                    vector_hash TEXT NULL,
                    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
                )
            """)

            # Migration: Add user_id to existing sessions if missing (for legacy data)
            try:
                conn.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT")
            except sqlite3.OperationalError:
                pass

            # Migration: Add collection_id to sessions (nullable for backward compatibility)
            try:
                conn.execute("ALTER TABLE sessions ADD COLUMN collection_id INTEGER NULL REFERENCES collections(id)")
            except sqlite3.OperationalError:
                pass

            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_collections_user ON collections(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_collection_docs_user ON collection_documents(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_collection ON sessions(collection_id)")

            conn.commit()

    def ensure_user_exists(self, user_id: str, email: str):
        """Ensures the user is registered in our local mapping table."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (id, email) VALUES (?, ?)",
                (user_id, email)
            )
            conn.commit()

    def create_session(self, user_id: str, name: str, collection_id: Optional[int] = None) -> int:
        """Creates a new chat session linked to the specific user, optionally tied to a collection."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO sessions (user_id, name, collection_id) VALUES (?, ?, ?)",
                (user_id, name, collection_id)
            )
            conn.commit()
            return cursor.lastrowid

    def rename_session(self, session_id: int, user_id: str, new_name: str):
        """Updates the name of a session only if it belongs to the user."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET name = ? WHERE id = ? AND user_id = ?",
                (new_name, session_id, user_id)
            )
            conn.commit()

    def delete_session(self, session_id: int, user_id: str) -> bool:
        """Deletes a session only if it belongs to the user.

        Returns True if a row was actually deleted, False otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE id = ? AND user_id = ?",
                (session_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetches only the sessions belonging to the specified user, including collection_id."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, created_at, collection_id FROM sessions WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def list_sessions_by_collection(self, user_id: str, collection_id: int) -> List[Dict[str, Any]]:
        """Fetches sessions for a specific collection belonging to the user."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, created_at FROM sessions WHERE user_id = ? AND collection_id = ? ORDER BY created_at DESC",
                (user_id, collection_id)
            )
            return [dict(row) for row in cursor.fetchall()]

    def update_session_collection(self, session_id: int, user_id: str, collection_id: Optional[int] = None):
        """Link or unlink a session to/from a collection."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET collection_id = ? WHERE id = ? AND user_id = ?",
                (collection_id, session_id, user_id)
            )
            conn.commit()

    def save_message(self, session_id: int, role: str, content: str):
        """Persists a message. The user isolation is handled by session_id."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
            conn.commit()

    def load_messages(self, session_id: int, user_id: str) -> List[Dict[str, str]]:
        """Retrieves messages for a session only if the session belongs to the user."""
        with self._get_connection() as conn:
            # Security Check: Ensure the session belongs to this user before loading messages
            session = conn.execute(
                "SELECT id FROM sessions WHERE id = ? AND user_id = ?",
                (session_id, user_id)
            ).fetchone()

            if not session:
                return [] # Or raise a security exception

            cursor = conn.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,)
            )
            return [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]

# Singleton instance
session_db = SessionManager()
