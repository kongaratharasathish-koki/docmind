# core/account_security.py
#
# Account lockout and session management.
#

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# In-memory login attempt tracking (use Redis in production).
# _login_attempts / _ip_attempts are bounded per identifier (see
# MAX_TRACKED_ATTEMPTS) so they cannot grow without bound.
MAX_TRACKED_ATTEMPTS = 50
# How long an attempt counts toward the lockout window. The lockout
# windows are sized to this value (1h): 5 failures -> 15 min, 10 -> 1h.
LOCKOUT_WINDOW_SECONDS = 3600
# Reset attempts after this much idle time since the last failure.
PRUNE_AFTER_SECONDS = LOCKOUT_WINDOW_SECONDS

_login_attempts: Dict[str, List[float]] = {}
_ip_attempts: Dict[str, List[float]] = {}
_device_sessions: Dict[str, Dict[str, Any]] = {}


def _prune_and_count(attempts: List[float], now: float) -> List[float]:
    """Drop entries outside the lockout window, cap to MAX_TRACKED_ATTEMPTS.

    Returns the (possibly mutated) list so callers can reuse it.
    """
    cutoff = now - LOCKOUT_WINDOW_SECONDS
    pruned = [t for t in attempts if t > cutoff]
    if len(pruned) > MAX_TRACKED_ATTEMPTS:
        pruned = pruned[-MAX_TRACKED_ATTEMPTS:]
    return pruned


def record_login_attempt(identifier: str, ip: str):
    """Record a failed login attempt for user and IP."""
    now = time.time()
    _login_attempts[identifier] = _prune_and_count(
        _login_attempts.get(identifier, []), now
    ) + [now]
    _ip_attempts[ip] = _prune_and_count(
        _ip_attempts.get(ip, []), now
    ) + [now]


def clear_login_attempts(identifier: str, ip: Optional[str] = None) -> None:
    """Clear all tracked attempts on a successful login."""
    _login_attempts.pop(identifier, None)
    if ip is not None:
        _ip_attempts.pop(ip, None)


def get_failed_attempts(identifier: str) -> int:
    """Get count of recent failed login attempts within the lockout window."""
    attempts = _login_attempts.get(identifier, [])
    return len([t for t in attempts if t > time.time() - LOCKOUT_WINDOW_SECONDS])


def get_ip_failed_attempts(ip: str) -> int:
    """Get count of recent failed login attempts from IP within the lockout window."""
    attempts = _ip_attempts.get(ip, [])
    return len([t for t in attempts if t > time.time() - LOCKOUT_WINDOW_SECONDS])


def is_account_locked(identifier: str) -> bool:
    """Check if account is locked due to failed attempts within the window."""
    attempts = get_failed_attempts(identifier)
    if attempts >= 10:
        return True  # 1h lock
    if attempts >= 5:
        return True  # 15 min lock
    return False


def get_lockout_remaining(identifier: str) -> Optional[int]:
    """Get remaining lockout time in minutes."""
    attempts = get_failed_attempts(identifier)
    if attempts >= 10:
        return LOCKOUT_WINDOW_SECONDS // 60
    if attempts >= 5:
        return 15
    return None


def create_device_session(user_id: str, token: str, ip: str, user_agent: str) -> Dict[str, Any]:
    """Create a device session record."""
    _device_sessions[token] = {
        "user_id": user_id,
        "ip": ip,
        "user_agent": user_agent,
        "created_at": datetime.utcnow().isoformat(),
        "last_active": datetime.utcnow().isoformat(),
    }
    return _device_sessions[token]


def get_user_sessions(user_id: str) -> List[Dict[str, Any]]:
    """Get all active sessions for a user."""
    return [
        {"token": token, **session}
        for token, session in _device_sessions.items()
        if session["user_id"] == user_id
    ]


def revoke_session(token: str) -> bool:
    """Revoke a specific session."""
    if token in _device_sessions:
        del _device_sessions[token]
        return True
    return False


def revoke_all_sessions(user_id: str) -> int:
    """Revoke all sessions for a user. Returns count revoked."""
    global _device_sessions
    tokens_to_remove = [
        token for token, session in _device_sessions.items()
        if session["user_id"] == user_id
    ]
    for token in tokens_to_remove:
        del _device_sessions[token]
    return len(tokens_to_remove)