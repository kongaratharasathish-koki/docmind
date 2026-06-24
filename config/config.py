# config/config.py
#
# Centralized configuration and environment validation for DocMind.
# Implements a "fail-fast" strategy to ensure the system does not
# start with missing critical credentials.

from __future__ import annotations
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Initialize logging for the config loader
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ConfigLoader")

# Load .env from project root (DocMind folder or any parent)
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if not ENV_PATH.exists():
    # Fallback: search parent directories for .env
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if candidate.exists():
            ENV_PATH = candidate
            break
load_dotenv(dotenv_path=ENV_PATH, override=False)

class ConfigError(Exception):
    """Custom exception for missing or invalid configuration."""
    pass

def get_env_or_fail(key: str, default: Any = None, required: bool = True) -> Any:
    """Retrieves an environment variable or raises a ConfigError if missing."""
    val = os.getenv(key, default)
    if required and (val is None or val == ""):
        raise ConfigError(f"Missing critical environment variable: {key}")
    return val

try:
    # ── Gemini ────────────────────────────────────────────────────────────────────
    GEMINI_API_KEY = get_env_or_fail("GEMINI_API_KEY")
    GEMINI_MODEL = get_env_or_fail("GEMINI_MODEL", default="gemini-1.5-flash", required=False)
    EMBEDDING_MODEL = get_env_or_fail("EMBEDDING_MODEL", default="models/embedding-001", required=False)

    # ── Supabase ────────────────────────────────────────────────────────────────────
    SUPABASE_URL = get_env_or_fail("SUPABASE_URL")
    SUPABASE_KEY = get_env_or_fail("SUPABASE_KEY")

    # ── System ────────────────────────────────────────────────────────────────────
    DB_PATH = get_env_or_fail("DB_PATH", default="docmind_sessions.db", required=False)
    LOG_LEVEL = get_env_or_fail("LOG_LEVEL", default="INFO", required=False)

    # ── Document Processing (Tuned Constants) ──────────────────────────────────────
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    TOP_K_DOCS = 5

    # ── UI Copy ───────────────────────────────────────────────────────────────────
    APP_TITLE = "DocMind"
    APP_TAGLINE = "Ask anything across your documents."
    UPLOAD_LABEL = "Upload PDFs"
    PROCESS_BUTTON = "Build Knowledge Base"
    SUMMARIZE_BUTTON = "Summarize Documents"
    COMPARE_BUTTON = "Compare Documents"
    CHAT_PLACEHOLDER = "Ask a question about your documents…"

    logger.info("✅ Configuration loaded and validated successfully.")

except ConfigError as e:
    logger.error(f"❌ Configuration failed: {e}")
    # In a production deployment, we want the app to crash immediately
    # so the orchestrator (Docker/K8s) can report the failure.
    raise SystemExit(f"CRITICAL CONFIGURATION ERROR: {e}")
