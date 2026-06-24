# app/routers/auth.py

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas import Token, UserSignup, EmailOnly
from app.deps import get_current_user
from app.services import auth_service
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/signup", response_model=Token)
@limiter.limit("100/hour")
def signup(request: Request, payload: UserSignup):
    ip = _get_client_ip(request)
    token_data, error = auth_service.signup(payload.email, payload.password, ip)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return token_data


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    ip = _get_client_ip(request)
    token_data, error = auth_service.login(form_data.username, form_data.password, ip)
    if error:
        raise HTTPException(status_code=401, detail=error)
    return token_data


@router.post("/logout")
def logout(request: Request, current_user: dict = Depends(get_current_user)):
    return auth_service.logout(current_user["user_id"])


@router.post("/verify-email")
@limiter.limit("100/hour")
def request_email_verification(request: Request, payload: EmailOnly):
    """Request email verification token resend."""
    result, error = auth_service.request_verification(payload.email)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return result


@router.post("/verify")
def verify_email(token: str):
    """Verify email with token."""
    from core.email_verification import verify_email_token
    success, error = verify_email_token(token)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"detail": "Email verified successfully"}


@router.get("/sessions", response_model=list[dict])
def get_auth_sessions(request: Request, current_user: dict = Depends(get_current_user)):
    """Get active device sessions for current user."""
    from core.account_security import get_user_sessions
    return get_user_sessions(current_user["user_id"])


@router.delete("/sessions/{session_token}")
def revoke_auth_session(request: Request, session_token: str, current_user: dict = Depends(get_current_user)):
    """Revoke a specific device session."""
    from core.account_security import revoke_session
    if revoke_session(session_token):
        return {"detail": "Session revoked"}
    raise HTTPException(status_code=404, detail="Session not found")


@router.delete("/sessions")
def revoke_all_auth_sessions(request: Request, current_user: dict = Depends(get_current_user)):
    """Revoke all device sessions for current user."""
    from core.account_security import revoke_all_sessions
    count = revoke_all_sessions(current_user["user_id"])
    return {"detail": f"Revoked {count} sessions"}
