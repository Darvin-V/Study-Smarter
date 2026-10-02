"""
Study Smarter - NCERT Smart Quiz Generator & Performance Analyzer
Application Main Entry Point

Usage:
  1. Web UI Mode: run via Streamlit
     $ streamlit run main.py
  2. Health / Syntax Verification Mode: run via standard Python
     $ python main.py
"""

import sys
import os
from src.config import config
from src.logger import logger
from src.database.connection import DatabaseManager


def run_system_health_check() -> bool:
    """Performs startup diagnostics and syntax verification without displaying credentials."""
    print("=" * 60)
    print(f"  {config.APP_NAME} v{config.VERSION}")
    print(f"  {config.SUBTITLE}")
    print("=" * 60)
    status = config.get_status_summary()
    print(f"[+] Environment     : {status['environment']}")
    print(f"[+] Database Target : {status['db_target']}")
    print(f"[+] Database Config : {status['database_config']}")
    print(f"[+] Gemini Config   : {status['gemini_config']}")
    print("-" * 60)

    # Check Database Connection
    logger.info("Running initial database connectivity diagnostic...")
    db_result = DatabaseManager.test_connection()
    if db_result["success"]:
        print(f"[OK] Database Status: {db_result['message']}")
    else:
        print(f"[!] Database Warning: {db_result['message']}")
        print("    (Configure environment variables / secrets for MySQL persistence)")

    print("=" * 60)
    print("[OK] System diagnostics completed cleanly!")
    print("    To launch the interactive Web Interface, execute:")
    print("    $ streamlit run main.py")
    print("=" * 60)
    return True


if __name__ == "__main__":
    # Detect if running under Streamlit runtime
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        is_streamlit = get_script_run_ctx() is not None
    except Exception:
        is_streamlit = False

    if is_streamlit:
        logger.info("Starting Study Smarter Streamlit Web Interface...")
        from src.ui.app_ui import render_ui
        render_ui()
    else:
        # Standalone Python execution mode
        run_system_health_check()
