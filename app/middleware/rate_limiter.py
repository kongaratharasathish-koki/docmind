# app/middleware/rate_limiter.py
#
# Rate limiting configuration using slowapi.
# Limits are applied per endpoint as defined in ROUTE_LIMITS.

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def _get_rate_limit_key(request: Request) -> str:
    """
    Rate limit key function.
    Uses IP address by default.
    For authenticated users, user_id could be used instead.
    """
    # Try to get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if user and user.get("user_id"):
        return f"user:{user['user_id']}"
    return get_remote_address(request)


limiter = Limiter(key_func=_get_rate_limit_key, storage_uri="memory://")
