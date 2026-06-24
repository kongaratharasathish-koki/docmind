# utils/logger.py
#
# Structured, rotating file loggers for DocMind.
# Four channels: app, auth, access, errors.
# No sensitive data (no tokens, passwords, PDFs, prompts, embeddings).

from __future__ import annotations

import json
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields if present
        for key in ("user_id", "email", "endpoint", "method", "status", "latency_ms", "action", "result", "error", "trace_id"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        return json.dumps(log_entry, ensure_ascii=False)


def _make_handler(filename: str) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        LOG_DIR / filename,
        maxBytes=5 * 1024 * 1024,   # 5 MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(JsonFormatter())
    return handler


# ---------------------------------------------------------------------------
# Logger factories
# ---------------------------------------------------------------------------
def get_app_logger() -> logging.Logger:
    logger = logging.getLogger("docmind.app")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(_make_handler("app.log"))
    return logger


def get_auth_logger() -> logging.Logger:
    logger = logging.getLogger("docmind.auth")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(_make_handler("auth.log"))
    return logger


def get_access_logger() -> logging.Logger:
    logger = logging.getLogger("docmind.access")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(_make_handler("access.log"))
    return logger


def get_error_logger() -> logging.Logger:
    logger = logging.getLogger("docmind.errors")
    logger.setLevel(logging.ERROR)
    if not logger.handlers:
        logger.addHandler(_make_handler("errors.log"))
    return logger


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------
def log_app(msg: str, **kwargs: Any) -> None:
    get_app_logger().info(msg, extra=kwargs)


def log_auth(msg: str, **kwargs: Any) -> None:
    get_auth_logger().info(msg, extra=kwargs)


def log_access(msg: str, **kwargs: Any) -> None:
    get_access_logger().info(msg, extra=kwargs)


# Default logger instance for backward compatibility
logger = get_app_logger()


def log_error(msg: str, **kwargs: Any) -> None:
    get_error_logger().error(msg, extra=kwargs)
