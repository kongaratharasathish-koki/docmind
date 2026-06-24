# core/document_storage.py
#
# Handles filesystem operations for persistent PDF storage.
# Documents are organized by user and collection:
#   documents/{user_id}/{collection_id}/{filename}
#
# Design notes:
#   - Content hashes prevent duplicate uploads within a collection.
#   - Paths are relative to the project root.
#   - No cloud storage — local filesystem only.

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

import config


def get_collection_path(user_id: str, collection_id: int) -> Path:
    """Return the filesystem path for a collection's document folder."""
    base = Path("documents") / user_id / str(collection_id)
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_vectorstore_path(user_id: str, collection_id: int) -> Path:
    """Return the filesystem path for a collection's FAISS index."""
    base = Path("vectorstores") / user_id / str(collection_id)
    base.mkdir(parents=True, exist_ok=True)
    return base


def safe_filename(filename: str) -> str:
    """
    Strip any path components from a user-supplied filename.
    Reject names that, after sanitization, are empty or that try to escape
    the destination directory (e.g. '..', absolute paths, NUL bytes).

    Raises ValueError for unsafe filenames. Returns the basename.
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("Invalid filename")

    # Reject NUL bytes outright — they truncate paths on POSIX and are
    # a common smuggling trick.
    if "\x00" in filename:
        raise ValueError("Invalid filename")

    # Strip Windows + POSIX drive / UNC prefixes by taking only the
    # basename. Path(...).name collapses any leading "..", "/", "\\".
    base = Path(filename).name
    if not base or base in {".", ".."}:
        raise ValueError("Invalid filename")

    # Disallow characters that are illegal on Windows filesystems;
    # they're never legitimate in a user-uploaded document name.
    if re.search(r'[<>:"/\\|?*\x01-\x1f]', base):
        raise ValueError("Invalid filename")

    # Disallow reserved Windows device names.
    stem = base.split(".", 1)[0].upper()
    if stem in {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }:
        raise ValueError("Invalid filename")

    return base


def compute_content_hash(content: bytes) -> str:
    """Compute MD5 hash of file content for deduplication and cache invalidation."""
    return hashlib.md5(content).hexdigest()


def save_pdf(
    user_id: str,
    collection_id: int,
    filename: str,
    file_bytes: bytes,
) -> Dict[str, Any]:
    """
    Save a PDF to the collection's document folder.
    Returns metadata dict with filename, file_path, file_size, content_hash.
    """
    safe_name = safe_filename(filename)
    collection_path = get_collection_path(user_id, collection_id)
    file_path = collection_path / safe_name
    file_size = len(file_bytes)
    content_hash = compute_content_hash(file_bytes)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    rel_path = str(file_path)

    return {
        "filename": safe_name,
        "file_path": rel_path,
        "file_size": file_size,
        "content_hash": content_hash,
    }


def file_exists(user_id: str, collection_id: int, filename: str) -> bool:
    """Check if a file already exists in a collection folder."""
    return get_collection_path(user_id, collection_id).joinpath(filename).exists()


def delete_file(user_id: str, collection_id: int, filename: str) -> bool:
    """Delete a file from a collection folder. Returns True if deleted."""
    path = get_collection_path(user_id, collection_id) / filename
    if path.exists():
        path.unlink()
        return True
    return False


def list_collection_files(user_id: str, collection_id: int) -> list:
    """List filenames stored in a collection folder."""
    path = get_collection_path(user_id, collection_id)
    if not path.exists():
        return []
    return [f.name for f in path.iterdir() if f.is_file()]
