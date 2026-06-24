# app/routers/analytics.py

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.schemas import AnalyticsResponse
from app.deps import get_current_user
from app.services import analytics_service
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsResponse)
@limiter.limit("60/minute")
def get_analytics(request: Request, current_user: dict = Depends(get_current_user)):
    data = analytics_service.get_analytics_data(current_user["user_id"])
    return AnalyticsResponse(**data)
