# core/security_logger.py
#
# Security audit logging - separate from application logs.
#

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

SECURITY_LOG_FILE = "logs/security.log"

# Ensure logs directory exists
import os
os.makedirs(os.path.dirname(SECURITY_LOG_FILE) if os.path.dirname(SECURITY_LOG_FILE) else ".", exist_ok=True)

_security_logger = logging.getLogger("security")
_security_logger.setLevel(logging.WARNING)
_handler = logging.FileHandler(SECURITY_LOG_FILE)
_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
_security_logger.addHandler(_handler)


def log_suspicious_activity(
    event: str,
    user_email: Optional[str] = None,
    ip: Optional[str] = None,
    details: Optional[str] = None,
):
    """Log security-relevant events."""
    msg = f"EVENT={event}"
    if user_email:
        msg += f" USER={user_email}"
    if ip:
        msg += f" IP={ip}"
    if details:
        msg += f" DETAILS={details}"
    _security_logger.warning(msg)


def log_disposable_email_blocked(email: str, ip: str):
    log_suspicious_activity("DISPOSABLE_EMAIL_BLOCKED", email, ip)


def log_account_locked(email: str, ip: str, reason: str):
    log_suspicious_activity("ACCOUNT_LOCKED", email, ip, reason)


def log_rate_limit_exceeded(ip: str, endpoint: str):
    log_suspicious_activity("RATE_LIMIT_EXCEEDED", ip=ip, details=endpoint)


def log_token_reuse_detected(user_id: str, token_preview: str):
    log_suspicious_activity("TOKEN_REUSE_DETECTED", user_id, details=token_preview)