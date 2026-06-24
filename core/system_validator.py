# core/system_validator.py
#
# Production Validation Layer for DocMind.
# This module operates as a STRICT READ-ONLY EXTERNAL OBSERVER.
# It validates system stability by inspecting the SQLite database and
# Streamlit session state without mutating either.

from __future__ import annotations
import time
import logging
import streamlit as st
from typing import List, Dict, Any
from core.session_manager import session_db

# Configure diagnostic logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger("DocMindValidator")

class SystemValidator:
    def __init__(self):
        self.results = []
        self.start_time = time.time()

    def _record(self, test_name: str, status: str, detail: str):
        self.results.append({
            "test": test_name,
            "status": status,
            "detail": detail
        })
        logger.info(f"[{status}] {test_name}: {detail}")

    def run_all_tests(self) -> str:
        """Executes the production validation suite in read-only observer mode."""
        logger.info("🚀 Starting DocMind Production Validation Suite (Read-Only)...")

        # 1. DB vs UI Sync Test (Verify SSOT)
        self.test_db_ui_sync()

        # 2. AI Double Trigger Detection (DB Analysis)
        self.test_ai_double_trigger_db()

        return self._generate_report()

    def test_db_ui_sync(self):
        """Verifies that st.session_state.chat_history is a faithful cache of the SQLite store."""
        test_name = "DB vs UI Sync Test"
        try:
            if not st.session_state.get("user") or not st.session_state.get("current_session_id"):
                self._record(test_name, "SKIP", "No active user/session to sync.")
                return

            user_id = st.session_state.user.id
            session_id = st.session_state.current_session_id

            ui_history = st.session_state.get("chat_history", [])
            db_history = session_db.load_messages(session_id, user_id)

            if len(ui_history) != len(db_history):
                self._record(test_name, "FAIL", f"Length mismatch: UI({len(ui_history)}) vs DB({len(db_history)})")
                return

            for i, (ui_msg, db_msg) in enumerate(zip(ui_history, db_history)):
                if ui_msg["role"] != db_msg["role"] or ui_msg["content"] != db_msg["content"]:
                    self._record(test_name, "FAIL", f"Content mismatch at index {i}")
                    return

            self._record(test_name, "PASS", "UI cache and DB are perfectly synchronized.")
        except Exception as e:
            self._record(test_name, "ERROR", str(e))

    def test_ai_double_trigger_db(self):
        """
        Detects AI double-triggers by analyzing the database for identical
        consecutive messages occurring within the same second.
        """
        test_name = "AI Double Trigger Detection"
        try:
            if not st.session_state.get("user") or not st.session_state.get("current_session_id"):
                self._record(test_name, "SKIP", "No active session for DB analysis.")
                return

            session_id = st.session_state.current_session_id

            with session_db._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
                    (session_id,)
                )
                msgs = cursor.fetchall()

            if not msgs:
                self._record(test_name, "PASS", "No messages found; no triggers to analyze.")
                return

            duplicates = 0
            for i in range(len(msgs) - 1):
                curr_content, curr_time = msgs[i]["content"], msgs[i]["timestamp"]
                next_content, next_time = msgs[i+1]["content"], msgs[i+1]["timestamp"]

                if curr_content == next_content and curr_time == next_time:
                    duplicates += 1

            if duplicates > 0:
                self._record(test_name, "FAIL", f"Detected {duplicates} identical consecutive messages in DB.")
            else:
                self._record(test_name, "PASS", "No double-trigger patterns detected in DB.")
        except Exception as e:
            self._record(test_name, "ERROR", str(e))

    def _generate_report(self) -> str:
        """Generates a formatted summary report."""
        duration = time.time() - self.start_time
        report = [
            "\n" + "="*60,
            "DOCMIND PRODUCTION VALIDATION REPORT (OBSERVER MODE)",
            "="*60,
            f"Execution Time: {duration:.2f}s",
            "-"*60
        ]

        passed = 0
        for res in self.results:
            status_icon = "✅" if res["status"] == "PASS" else "❌" if res["status"] == "FAIL" else "⚠️"
            report.append(f"{status_icon} {res['test']}: {res['status']}")
            report.append(f"    └─ {res['detail']}")
            if res["status"] == "PASS":
                passed += 1

        report.append("-"*60)
        report.append(f"FINAL SCORE: {passed}/{len(self.results)} tests passed.")
        report.append("STATUS: " + ("PRODUCTION READY" if passed == len(self.results) else "STABILITY ISSUES DETECTED"))
        report.append("="*60 + "\n")
        return "\n".join(report)
