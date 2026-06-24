# utils/startup_check.py
#
# Pre-run system validation hook for DocMind.
# Verifies that the environment is ready before the Streamlit app starts.

import os
from pathlib import Path
from utils.logger import logger

def verify_system_health() -> bool:
    """
    Performs a series of health checks on the system environment.
    Returns True if all checks pass, False otherwise.
    """
    logger.info("🔍 Running pre-flight system health checks...")

    checks = {
        "Logs Directory": lambda: Path("logs").exists(),
        "Config File": lambda: Path("config/config.py").exists(),
        "Env File": lambda: Path(".env").exists() or os.getenv("SaaS_ENV") == "production",
    }

    all_passed = True
    for check_name, check_fn in checks.items():
        try:
            if check_fn():
                logger.info(f"  ✅ {check_name}: OK")
            else:
                logger.warning(f"  ⚠️ {check_name}: Missing or invalid")
                all_passed = False
        except Exception as e:
            logger.error(f"  ❌ {check_name}: Error during check - {e}")
            all_passed = False

    if all_passed:
        logger.info("🚀 System health check passed. Ready for deployment.")
    else:
        logger.error("🚨 System health check failed. Please check your environment.")

    return all_passed
