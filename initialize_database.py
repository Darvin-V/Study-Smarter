"""
Study Smarter - Safe Database Initializer
Connects to the configured MySQL database (local or cloud) and initializes
all necessary tables, indexes, and initial records safely without dropping or deleting data.

Usage:
    python initialize_database.py
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from src.config import config
from src.database.connection import (
    get_db_connection,
    get_db_cursor,
    init_db,
    DatabaseManager,
    MYSQL_AVAILABLE,
    _sanitize_error_msg,
)


def run_initializer() -> bool:
    print("=" * 65)
    print("      STUDY SMARTER - DATABASE INITIALIZER (LOCAL & CLOUD)")
    print("=" * 65)

    if not MYSQL_AVAILABLE:
        print("[FAIL] 'mysql-connector-python' is not installed.")
        print("       Please run: pip install -r requirements.txt")
        return False

    status = config.get_status_summary()
    print(f"Target Host    : {config.DB_HOST}:{config.DB_PORT}")
    print(f"Target Database: {config.DB_NAME}")
    print(f"Configuration  : {status['database_config']}")
    print("-" * 65)

    if not config.validate_database_config():
        print("[FAIL] Minimum database configuration (DB_HOST, DB_USER, DB_NAME) missing.")
        print("       Configure .env or deployment environment variables.")
        return False

    print("[*] Testing connection to MySQL...")
    test_res = DatabaseManager.test_connection()
    if not test_res["success"]:
        print(f"[FAIL] Could not connect to MySQL server: {test_res['message']}")
        return False

    print(f"[OK] {test_res['message']}")
    print("[*] Initializing tables, indexes, and initial constraints...")

    try:
        success = init_db()
        if not success:
            print("[FAIL] Schema initialization failed. Check logs for details.")
            return False

        # Verify tables exist
        required_tables = ["users", "question_banks", "quizzes", "questions", "attempts"]
        existing_tables = []
        with get_db_cursor() as cursor:
            cursor.execute("SHOW TABLES")
            rows = cursor.fetchall()
            for r in rows:
                if isinstance(r, dict):
                    existing_tables.extend(r.values())
                else:
                    existing_tables.append(r[0])

        missing = [t for t in required_tables if t not in existing_tables]
        if missing:
            print(f"[WARN] Some tables were not detected: {missing}")
            return False

        print("-" * 65)
        print("[OK] Verified Tables in Database:")
        for t in required_tables:
            print(f"     [OK] {t}")
        print("=" * 65)
        print("[SUCCESS] Database is fully initialized and deployment-ready!")
        print("=" * 65)
        return True

    except Exception as err:
        safe_msg = _sanitize_error_msg(err)
        print(f"[FAIL] Initialization error: {safe_msg}")
        return False


if __name__ == "__main__":
    ok = run_initializer()
    sys.exit(0 if ok else 1)
