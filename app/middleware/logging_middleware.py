# app/middleware/logging_middleware.py
#
# Request/response logging middleware.
# Writes structured access logs with latency measurement.

from __future__ import annotations

import time
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import log_access, log_error


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with:
      - timestamp
      - user_id (from request.state if authenticated)
      - endpoint
      - method
      - status
      - latency_ms
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
            latency_ms = int((time.perf_counter() - start) * 1000)

            user_id = getattr(getattr(request, "state", None), "user", None) or {}
            log_access(
                "request",
                user_id=user_id.get("user_id"),
                endpoint=request.url.path,
                method=request.method,
                status=response.status_code,
                latency_ms=latency_ms,
            )
            return response
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            user_id = getattr(getattr(request, "state", None), "user", None) or {}
            log_error(
                str(exc),
                user_id=user_id.get("user_id"),
                endpoint=request.url.path,
                method=request.method,
                status=500,
                latency_ms=latency_ms,
            )
            raise
