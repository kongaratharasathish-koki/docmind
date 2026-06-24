# app/routers/search.py

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.schemas import SearchRequest, SearchResponse
from app.deps import get_current_user
from app.services import search_service
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
@limiter.limit("30/minute")
def search(request: Request, payload: SearchRequest, current_user: dict = Depends(get_current_user)):
    results = search_service.search(
        current_user["user_id"],
        payload.query,
        library_id=payload.library_id,
    )
    return SearchResponse(**results)
