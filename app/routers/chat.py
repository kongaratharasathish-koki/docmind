# app/routers/chat.py

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas import ChatRequest, ChatResponse, CitationResponse
from app.deps import get_current_user
from core.chat_engine import ask, rebuild_memory_from_messages, create_conversation_chain
from core.citations import format_citations
from core.vectorstore_manager import load_or_build_collection_vectorstore
from core.session_manager import session_db

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    session_id = payload.session_id

    # Validate question is present and within sane bounds. An empty/whitespace
    # question otherwise hits Gemini, burns tokens, and produces empty answers.
    question = (payload.question or "").strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty.",
        )
    if len(question) > 4000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question exceeds maximum length of 4000 characters.",
        )

    # Validate session ownership
    with session_db._get_connection() as conn:
        row = conn.execute(
            "SELECT collection_id FROM sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id)
        ).fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        collection_id = row["collection_id"]

    # Load or build chain
    if not collection_id:
        raise HTTPException(status_code=400, detail="Session has no assigned library. Upload documents first.")

    try:
        vs = load_or_build_collection_vectorstore(user_id, collection_id)
    except ValueError as exc:
        # Empty library or no extractable text — surface as 400, not 500.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc) or "Library has no documents to query.",
        ) from exc
    chain = create_conversation_chain(vs)

    # Restore memory
    history = session_db.load_messages(session_id, user_id)
    chain = rebuild_memory_from_messages(chain, history)

    # Run query. The LLM call can fail for many reasons (network,
    # rate-limit, auth, content filter). Treat all of them as a 503 so
    # the client gets a clear signal instead of a 500 with a stack trace.
    try:
        response = ask(chain, question)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The chat model is currently unavailable. Please try again shortly.",
        ) from exc

    answer = response.get("answer", "") if isinstance(response, dict) else ""
    source_docs = response.get("source_documents", []) if isinstance(response, dict) else []

    citations = []
    for c in format_citations(source_docs):
        citations.append(CitationResponse(**c))

    # Persist messages
    session_db.save_message(session_id, "user", question)
    session_db.save_message(session_id, "assistant", answer)

    return ChatResponse(answer=answer, citations=citations)
