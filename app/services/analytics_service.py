# app/services/analytics_service.py
#
# Business logic for analytics.
# Routers call this; this module calls core.analytics_manager.

from __future__ import annotations

from typing import Dict, Any, Optional

from core.analytics_manager import get_analytics


def get_analytics_data(user_id: str) -> Dict[str, Any]:
    return get_analytics(user_id)
