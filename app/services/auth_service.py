# app/services/auth_service.py
#
# Business logic for authentication.
# Routers call this; this module calls core.auth_manager.
#

from __future__ import annotations

from typing import Tuple, Optional, Dict, Any

from core.auth_manager import auth_manager
from core.session_manager import session_db
from core.security import is_disposable_email, validate_password_strength
from core.email_verification import (
    generate_verification_token,
    is_email_verified,
    is_disposable_email as check_disposable,
)
from core.security_logger import (
    log_disposable_email_blocked,
    log_account_locked,
)


def signup(email: str, password: str, ip: str = "unknown") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    # Block disposable emails
    is_dispo, reason = check_disposable(email)
    if is_dispo:
        log_disposable_email_blocked(email, ip)
        return None, "Disposable email addresses are not allowed."

    # Validate password strength
    is_valid, error = validate_password_strength(password)
    if not is_valid:
        return None, error

    user, error = auth_manager.sign_up(email, password)
    if error:
        return None, error

    # Generate verification token (user must verify before full access)
    generate_verification_token(email)
    session_db.ensure_user_exists(user.id, user.email)

    access_token = auth_manager.create_access_token(user.id, user.email)
    refresh_token = auth_manager.create_refresh_token(user.id, user.email)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "requires_verification": True,
    }, None


def login(email: str, password: str, ip: str = "unknown") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    from core.account_security import is_account_locked, record_login_attempt, get_lockout_remaining, clear_login_attempts

    # Check if account is locked
    if is_account_locked(email):
        log_account_locked(email, ip, f"Lockout active")
        remaining = get_lockout_remaining(email)
        return None, f"Account locked. Try again in {remaining} minutes."

    user, error = auth_manager.sign_in(email, password)
    if error:
        record_login_attempt(email, ip)
        return None, "Invalid credentials"
    if not user:
        record_login_attempt(email, ip)
        return None, "Invalid credentials"

    # Check email verification (both our system and Supabase)
    if not is_email_verified(email):
        # Also check Supabase's built-in email confirmation
        if user and not getattr(user, "email_confirmed_at", None):
            log_account_locked(email, ip, "Email not verified")
            return None, "Email verification required. Check your inbox."

    # Successful login: drop any prior failed-attempt bookkeeping.
    clear_login_attempts(email, ip)

    access_token = auth_manager.create_access_token(user.id, user.email)
    refresh_token = auth_manager.create_refresh_token(user.id, user.email)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}, None


def logout(user_id: str = None) -> Dict[str, str]:
    if user_id:
        auth_manager.revoke_all_refresh_tokens(user_id)
    return {"detail": "Logged out"}


def request_verification(email: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Request verification email resend."""
    if is_email_verified(email):
        return {"detail": "Email already verified"}, None

    generate_verification_token(email)
    return {"detail": "Verification email sent"}, None
