# core/auth_manager.py
#
# Responsible for handling user authentication and identity via Supabase.
#
# Design notes:
#   - Wraps the Supabase client to provide a simple interface for signup, login, and logout.
#   - Manages the authentication state using the Supabase GoTrue client.
#   - Refresh token rotation prevents token reuse attacks.
#

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from supabase import create_client, Client
from jose import JWTError, jwt
import config


# In-memory refresh token store (use Redis in production)
_refresh_tokens: Dict[str, Dict[str, Any]] = {}


class AuthManager:
    def __init__(self):
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        return self._client

    def create_access_token(self, user_id: str, email: str) -> str:
        """Create a short-lived access token (15 minutes)."""
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=15),
        }
        return jwt.encode(to_encode, config.GEMINI_API_KEY, algorithm="HS256")

    def create_refresh_token(self, user_id: str, email: str) -> str:
        """Create a long-lived refresh token (30 days) with rotation tracking."""
        token = secrets.token_urlsafe(64)
        _refresh_tokens[token] = {
            "user_id": user_id,
            "email": email,
            "created_at": datetime.utcnow().isoformat(),
            "used": False,
        }
        return token

    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify refresh token and mark as used for rotation."""
        record = _refresh_tokens.get(token)
        if not record:
            return None

        # Check if already used (token reuse attack)
        if record.get("used"):
            from core.security_logger import log_token_reuse_detected
            log_token_reuse_detected(record["user_id"], token[:8] + "...")
            return None

        # Mark as used for rotation
        record["used"] = True
        return {"user_id": record["user_id"], "email": record["email"]}

    def revoke_all_refresh_tokens(self, user_id: str) -> int:
        """Revoke all refresh tokens for a user. Returns count revoked."""
        global _refresh_tokens
        tokens_to_remove = [
            t for t, r in _refresh_tokens.items()
            if r["user_id"] == user_id
        ]
        for t in tokens_to_remove:
            del _refresh_tokens[t]
        return len(tokens_to_remove)

    def create_token(self, user_id: str, email: str, expires_delta: timedelta = timedelta(hours=12)) -> str:
        """Deprecated: Kept for backward compatibility. Use create_access_token."""
        return self.create_access_token(user_id, email)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token. Returns payload or None.

        Deprecated: prefer `decode_token` which surfaces the specific
        failure mode (expired vs invalid). Kept for backward compat.
        """
        try:
            return self.decode_token(token)
        except JWTError:
            return None

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token. Raises jose.JWTError on failure.

        Use this when the caller needs to distinguish ExpiredSignatureError
        from generic invalid tokens.
        """
        payload = jwt.decode(token, config.GEMINI_API_KEY, algorithms=["HS256"])
        return payload

    def sign_up(self, email: str, password: str) -> tuple[Optional[Dict], Optional[str]]:
        """Create a new user account."""
        try:
            response = self.client.auth.sign_up({"email": email, "password": password})
            return response.user, None
        except Exception as e:
            return None, str(e)

    def sign_in(self, email: str, password: str) -> tuple[Optional[Dict], Optional[str]]:
        """Authenticate a user with email and password."""
        try:
            response = self.client.auth.sign_in_with_password({"email": email, "password": password})
            return response.user, None
        except Exception as e:
            return None, str(e)

    def sign_out(self):
        """Log out the current user."""
        self.client.auth.sign_out()


# Singleton instance
auth_manager = AuthManager()
