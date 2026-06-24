# app/services/search_service.py
#
# Business logic for search.
# Routers call this; this module calls core.search_manager.

from __future__ import annotations

from typing import Dict, Any, List, Optional

from core.search_manager import global_search


def search(user_id: str, query: str, library_id: Optional[int] = None) -> Dict[str, Any]:
    return global_search(
        user_id,
        query,
        collection_id=library_id,
    )
