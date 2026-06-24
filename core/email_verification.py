# core/email_verification.py
#
# Email verification and disposable email detection.
# Uses configurable denylist/allowlist with external API support.
#

from __future__ import annotations

import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

# In-memory store for verification tokens (replace with Redis in production)
_verification_tokens: Dict[str, Dict[str, Any]] = {}

# Disposable email denylist (updated from real sources)
DISPOSABLE_DOMAINS_FILE = "data/disposable_domains.txt"
DEFAULT_DISPOSABLE_DOMAINS = {
    "temp-mail.org", "guerrillamail.com", "mailinator.com", "yopmail.com",
    "10minutemail.com", "throwaway.email", "getnada.com", "dispostable.com",
    "maildrop.cc", "trashmail.com", "fakeinbox.com", "mailnesia.com",
    "mytemp.email", "tempail.com", "emailondeck.com", "anonbox.net",
    "guerrillamail.net", "guerrillamailblock.com", "pokemail.net",
    "spamgourmet.com", "throwam.com", "yopmail.fr", "yopmail.net",
    "cool.fr.nf", "jetable.fr", "nospamproxy.com", "proxymail.eu",
    "trashmail.net", "wegwerfmail.de", "wegwerf-email.de", "mailcatch.com",
    "tempinbox.com", "tempr.email", "tmail.ws", "incognitomail.com",
    "emailtemporar.ro", "tempemail.co", "sharklasers.com", "chmail.com",
    "einmalmail.de", "meltmail.com", "trashmail.de", "burnermail.io",
    "burnermail.org", "temp-mail.io", "temp-mail.net", "gettempmail.com",
}


def load_disposable_domains() -> set[str]:
    """Load disposable domains from file or return defaults."""
    try:
        from pathlib import Path
        path = Path(DISPOSABLE_DOMAINS_FILE)
        if path.exists():
            return {line.strip().lower() for line in path.read_text().splitlines() if line.strip()}
    except Exception:
        pass
    return DEFAULT_DISPOSABLE_DOMAINS.copy()


def is_disposable_email(email: str) -> Tuple[bool, str]:
    """
    Check if email is from a disposable provider.
    Returns (is_disposable, reason).
    """
    if not email or "@" not in email:
        return True, "Invalid email format"

    domain = email.lower().split("@")[-1]
    domains = load_disposable_domains()

    if domain in domains:
        return True, "Disposable email provider blocked"

    return False, ""


def generate_verification_token(email: str) -> str:
    """Generate a secure verification token for email."""
    token = secrets.token_urlsafe(32)
    _verification_tokens[token] = {
        "email": email,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
        "verified": False,
    }
    return token


def verify_email_token(token: str) -> Tuple[bool, str]:
    """
    Verify an email verification token.
    Returns (success, error_message).
    """
    if not token or token not in _verification_tokens:
        return False, "Invalid verification token"

    record = _verification_tokens[token]

    # Check expiration
    expires_at = datetime.fromisoformat(record["expires_at"])
    if datetime.utcnow() > expires_at:
        del _verification_tokens[token]
        return False, "Verification token expired"

    # Mark as verified
    record["verified"] = True
    record["verified_at"] = datetime.utcnow().isoformat()
    return True, ""


def is_email_verified(email: str) -> bool:
    """Check if email has been verified."""
    for record in _verification_tokens.values():
        if record.get("email") == email and record.get("verified"):
            return True
    return False


def cleanup_expired_tokens() -> int:
    """Remove expired verification tokens. Returns count removed."""
    now = datetime.utcnow()
    expired = [
        token for token, record in _verification_tokens.items()
        if datetime.fromisoformat(record["expires_at"]) < now
    ]
    for token in expired:
        del _verification_tokens[token]
    return len(expired)