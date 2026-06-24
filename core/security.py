# core/security.py
#
# Security utilities for authentication and file validation.
#

from __future__ import annotations

import re
from typing import Tuple, Optional

# Disposable email domains blacklist
DISPOSABLE_EMAIL_DOMAINS = {
    "temp-mail.org",
    "guerrillamail.com",
    "mailinator.com",
    "yopmail.com",
    "10minutemail.com",
    "throwaway.email",
    "getnada.com",
    "dispostable.com",
    "maildrop.cc",
    "trashmail.com",
    "fakeinbox.com",
    "mailnesia.com",
    "mytemp.email",
    "tempail.com",
    "emailondeck.com",
    "anonbox.net",
    "guerrillamail.net",
    "guerrillamail.org",
    "guerrillamailblock.com",
    "pokemail.net",
    "spamgourmet.com",
    "throwam.com",
    "yopmail.fr",
    "yopmail.net",
    "cool.fr.nf",
    "jetable.fr",
    "nospamproxy.com",
    "proxymail.eu",
    "trashmail.net",
    "wegwerfmail.de",
    "wegwerf-email.de",
}


def is_disposable_email(email: str) -> bool:
    """Check if email is from a disposable email provider."""
    if not email:
        return True
    domain = email.lower().split("@")[-1] if "@" in email else ""
    return domain in DISPOSABLE_EMAIL_DOMAINS


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password meets security requirements.
    Returns (is_valid, error_message).
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."

    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]', password):
        return False, "Password must contain at least one special character."

    return True, None


# Allowed file types for upload
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_FILE_SIZE_MB = {
    "student": 10,
    "basic": 50,
    "pro": 50,
    "enterprise": 100,
}


def validate_file_extension(filename: str) -> Tuple[bool, Optional[str]]:
    """Validate file extension is allowed."""
    if not filename:
        return False, "No filename provided."

    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type not allowed. Permitted types: {', '.join(ALLOWED_EXTENSIONS)}"

    return True, None


def validate_file_size(size_bytes: int, user_tier: str = "basic") -> Tuple[bool, Optional[str]]:
    """Validate file size against user tier limit."""
    max_mb = MAX_FILE_SIZE_MB.get(user_tier, 50)
    max_bytes = max_mb * 1024 * 1024

    if size_bytes > max_bytes:
        return False, f"File exceeds maximum size of {max_mb}MB for your plan."

    return True, None