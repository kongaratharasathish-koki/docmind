# app/routers/sessions.py

from __future__ import annotations

import time
import secrets

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import SessionCreate, SessionResponse, MessageResponse
from app.deps import get_current_user
from app.services import session_service
from core.session_manager import session_db

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionResponse])
def get_sessions(current_user: dict = Depends(get_current_user)):
    return session_service.list_sessions(current_user["user_id"])


@router.post("", response_model=SessionResponse)
def create_session(payload: SessionCreate, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]

    # Ownership check: if library_id is provided, it must belong to this user
    # AND not be archived. Otherwise a user could create a session tied to
    # someone else's library and chat against their documents.
    if payload.library_id is not None:
        with session_db._get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM collections WHERE id = ? AND user_id = ? AND archived_at IS NULL",
                (payload.library_id, user_id),
            ).fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Library not found or access denied",
            )

    # Race-free default name: never read-modify-write. A 6-char random
    # suffix keeps it unique across concurrent calls.
    if payload.name:
        name = payload.name
    else:
        name = f"Conversation {int(time.time())}-{secrets.token_hex(3)}"

    return session_service.create_session(user_id, name, library_id=payload.library_id)


@router.delete("/{session_id}")
def delete_session(session_id: int, current_user: dict = Depends(get_current_user)):
    deleted = session_service.delete_session(current_user["user_id"], session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied",
        )
    return {"detail": "Session deleted"}


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
def get_messages(session_id: int, current_user: dict = Depends(get_current_user)):
    return session_service.get_messages(current_user["user_id"], session_id)
