# app/routers/upload.py

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas import LibraryResponse
from app.deps import get_current_user
from core.document_storage import save_pdf, safe_filename
from core.collection_manager import (
    ensure_metadata_exists,
    increment_document_count,
    get_metadata,
    get_collection,
)
from core.security import validate_file_extension, validate_file_size
from core.session_manager import session_db
from core.vectorstore_manager import (
    load_or_build_collection_vectorstore,
    invalidate_vectorstore_cache,
)
from core.chat_engine import invalidate_chain_cache

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/{library_id}", response_model=LibraryResponse)
async def upload_to_library(
    library_id: int,
    files: list[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    # Validate library ownership AND that it's not archived.
    with session_db._get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM collections WHERE id = ? AND user_id = ? AND archived_at IS NULL",
            (library_id, user_id)
        ).fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Library not found or access denied"
            )

    # Validate every file's extension and filename *before* reading bytes.
    for uf in files:
        try:
            safe_name = safe_filename(uf.filename or "")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename: {uf.filename!r}",
            )
        ok, err = validate_file_extension(safe_name)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    # Read with a hard cap so a malicious or accidental huge upload can't OOM
    # the worker. Per-file cap mirrors MAX_FILE_SIZE_MB['basic'] (50 MB);
    # the global request body cap is enforced in middleware.
    from core.security import MAX_FILE_SIZE_MB
    per_file_max_bytes = MAX_FILE_SIZE_MB["basic"] * 1024 * 1024

    ensure_metadata_exists(library_id)
    saved = []
    for uf in files:
        # Prefer the framework-reported size when present.
        declared_size = getattr(uf, "size", None)
        if declared_size is not None and declared_size > per_file_max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {MAX_FILE_SIZE_MB['basic']}MB for your plan.",
            )

        content = await uf.read()
        if len(content) > per_file_max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {MAX_FILE_SIZE_MB['basic']}MB for your plan.",
            )

        # Re-validate size against tier after read (declared size may be wrong).
        ok, err = validate_file_size(len(content), user_tier="basic")
        if not ok:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=err)

        safe_name = safe_filename(uf.filename)
        meta = save_pdf(user_id, library_id, safe_name, content)
        with session_db._get_connection() as conn:
            conn.execute(
                "INSERT INTO collection_documents (collection_id, user_id, filename, file_path, file_size, content_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (library_id, user_id, meta["filename"], meta["file_path"], meta["file_size"], meta["content_hash"]),
            )
            conn.commit()
        increment_document_count(library_id, 1)
        saved.append(meta["filename"])

    # Vectorstore is now stale — drop any cached instance before rebuild.
    # If the build fails (e.g. every uploaded file was corrupt), the files
    # are still on disk and in the DB. Surface the failure as 422 so the
    # client knows the upload succeeded but indexing failed.
    invalidate_vectorstore_cache(user_id, library_id)
    invalidate_chain_cache()  # safe to nuke; entries are cheap to rebuild
    try:
        load_or_build_collection_vectorstore(user_id, library_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Files were uploaded but indexing failed: "
                f"{exc}. Re-upload readable documents."
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Files were uploaded but the vector index could not be built.",
        ) from exc

    # Re-fetch the library to return a valid LibraryResponse.
    library = get_collection(library_id, user_id) or {}
    meta = get_metadata(library_id) or {}
    return {
        "id": library_id,
        "name": library.get("name", ""),
        "archived_at": library.get("archived_at"),
        "created_at": library.get("created_at"),
        "updated_at": library.get("updated_at"),
        "document_count": meta.get("document_count", 0),
    }
