# app/main.py
#
# FastAPI entry point for DocMind backend.
# Wraps existing core modules into a REST API.
#

from __future__ import annotations

import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.routers import auth, libraries, sessions, upload, chat, search, analytics
from app.middleware.rate_limiter import limiter
from app.middleware.logging_middleware import RequestLoggingMiddleware
from utils.logger import log_app, log_auth, log_error


# Cap inbound request bodies. Starlette defaults to unbounded, which lets
# any client stream gigabytes through a slow path. 100 MB is well above
# the largest allowed per-file upload (100 MB enterprise) with some headroom
# for multipart envelopes.
MAX_REQUEST_BODY_BYTES = int(os.getenv("MAX_REQUEST_BODY_BYTES", str(100 * 1024 * 1024)))


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add enterprise security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        return response


class RequestBodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with Content-Length above the configured cap.

    Streaming clients can omit Content-Length — those still pass through
    here, and per-endpoint / per-file caps in the upload router are the
    real defense. This middleware is the first line of defense for the
    rest of the API surface.
    """

    def __init__(self, app, max_bytes: int):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl is not None:
            try:
                if int(cl) > self.max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request body too large"},
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid Content-Length"},
                )
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log_app("FastAPI startup", event="startup")
    yield
    log_app("FastAPI shutdown", event="shutdown")


app = FastAPI(
    title="DocMind API",
    description="AI Document Assistant — Backend API",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting middleware - must be added before other middleware
app.state.limiter = limiter

# Rate limiting exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )


# Catch-all for unhandled exceptions. Logs the trace and returns a clean
# 500 without leaking stack frames to the client. Per-route handlers
# (HTTPException, validation errors, etc.) still take precedence.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # HTTPException is FastAPI's own signaling exception; let it pass
    # through to its normal handler. The exception handler registry does
    # this by HTTP status, but registering Exception here would otherwise
    # swallow them, so we re-raise.
    from fastapi import HTTPException as _HTTPException
    if isinstance(exc, _HTTPException):
        # Re-raise so FastAPI's HTTPException handler runs.
        raise exc

    log_error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        endpoint=request.url.path,
        method=request.method,
        status=500,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# CORS allowlist. Comma-separated env var. Browsers reject Access-Control-
# Allow-Origin: * with credentials, and the open default is a CSRF risk.
# Default = empty list (CORS disabled) so misconfiguration is safe-by-default;
# operators MUST set CORS_ALLOW_ORIGINS to enable browser access.
_cors_origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

# Middleware order: CORS → rate limiting → body size → security headers → logging
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # No CORS: any cross-origin browser request will be blocked by the
    # browser itself. This is the safe default for a backend that does
    # not yet have a known frontend origin.
    pass

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestBodySizeLimitMiddleware, max_bytes=MAX_REQUEST_BODY_BYTES)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(libraries.router)
app.include_router(sessions.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}
