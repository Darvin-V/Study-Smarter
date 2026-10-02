"""
Study Smarter - Database Connection Manager
Provides robust connection handling, schema initialization, and cursor management for MySQL.
Fully supports both local MySQL and remote/cloud MySQL databases (AWS RDS, PlanetScale, Aiven, etc.).
Uses environment variables loaded safely via Config.
"""

import os
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any, Generator
from src.config import config
from src.logger import logger
from src.utils.exceptions import DatabaseConnectionError, DatabaseQueryError

# Import mysql.connector safely
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    mysql = None  # type: ignore
    MySQLError = Exception
    MYSQL_AVAILABLE = False


# Connection pool cache and failure cooldown tracker
_DB_POOL = None
_LAST_FAIL_TIME: float = 0.0
_FAIL_COOLDOWN_SECONDS: float = 8.0
_LAST_FAIL_MESSAGE: str = ""


def _sanitize_error_msg(err: Any) -> str:
    """Removes sensitive credentials from database error messages before logging or surfacing."""
    msg = str(err)
    if config.DB_PASSWORD and config.DB_PASSWORD in msg:
        msg = msg.replace(config.DB_PASSWORD, "******")
    return msg


def get_db_connection(use_database: bool = True, force_retry: bool = False):
    """
    Establishes and returns a MySQL database connection using credentials from Config.
    Supports local MySQL and remote cloud databases.
    Uses connection pooling and ping/reconnect for cloud resilience.
    Implements a failure cooldown to prevent multi-second UI freezing during network partitions.
    """
    global _DB_POOL, _LAST_FAIL_TIME, _LAST_FAIL_MESSAGE

    if not MYSQL_AVAILABLE:
        raise DatabaseConnectionError(
            "MySQL connector module ('mysql-connector-python') is not installed. "
            "Please run: pip install mysql-connector-python"
        )

    # Check failure cooldown to avoid repeated connection timeout hangs
    if not force_retry and (time.time() - _LAST_FAIL_TIME) < _FAIL_COOLDOWN_SECONDS:
        raise DatabaseConnectionError(
            _LAST_FAIL_MESSAGE or f"MySQL server at {config.DB_HOST}:{config.DB_PORT} is currently unreachable."
        )

    conn_args: Dict[str, Any] = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
        "charset": "utf8mb4",
        "connect_timeout": config.DB_TIMEOUT,
    }
    if use_database and config.DB_NAME:
        conn_args["database"] = config.DB_NAME

    # SSL configuration for cloud providers
    if config.DB_SSL_CA and os.path.exists(config.DB_SSL_CA):
        conn_args["ssl_ca"] = config.DB_SSL_CA
        conn_args["ssl_verify_cert"] = True
    elif config.DB_SSL_DISABLED:
        conn_args["ssl_disabled"] = True

    try:
        # Try using connection pool if connecting to database
        if use_database and config.DB_NAME:
            if _DB_POOL is None:
                try:
                    from mysql.connector.pooling import MySQLConnectionPool
                    pool_args = dict(conn_args)
                    pool_args["pool_name"] = "studysmarter_pool"
                    pool_args["pool_size"] = 5
                    _DB_POOL = MySQLConnectionPool(**pool_args)
                except Exception as pool_err:
                    logger.debug(f"Connection pooling bypassed: {_sanitize_error_msg(pool_err)}")
                    _DB_POOL = False

            if _DB_POOL:
                conn = _DB_POOL.get_connection()
                try:
                    conn.ping(reconnect=True, attempts=2, delay=1)
                except Exception:
                    pass
                _LAST_FAIL_TIME = 0.0
                return conn

        # Direct connection fallback
        connection = mysql.connector.connect(**conn_args)
        if connection.is_connected():
            _LAST_FAIL_TIME = 0.0
            return connection

    except MySQLError as err:
        _LAST_FAIL_TIME = time.time()
        safe_msg = _sanitize_error_msg(err)
        _LAST_FAIL_MESSAGE = f"Failed to connect to MySQL database at {config.DB_HOST}:{config.DB_PORT}. ({safe_msg})"
        logger.error(f"MySQL Connection Error: {safe_msg}")
        raise DatabaseConnectionError(_LAST_FAIL_MESSAGE) from err
    except Exception as err:
        _LAST_FAIL_TIME = time.time()
        safe_msg = _sanitize_error_msg(err)
        _LAST_FAIL_MESSAGE = f"Database Error: {safe_msg}"
        logger.error(f"Database error: {safe_msg}")
        raise DatabaseConnectionError(_LAST_FAIL_MESSAGE) from err


@contextmanager
def get_db_cursor(dictionary: bool = True) -> Generator[Any, None, None]:
    """
    Context manager that yields a database cursor.
    Automatically commits transactions on success and rolls back on exception.
    Ensures cursor and connection are cleanly closed.
    """
    connection = get_db_connection(use_database=True)
    cursor = connection.cursor(dictionary=dictionary)
    try:
        yield cursor
        connection.commit()
    except Exception as err:
        try:
            connection.rollback()
        except Exception:
            pass
        safe_msg = _sanitize_error_msg(err)
        logger.error(f"Database transaction error: {safe_msg}")
        raise DatabaseQueryError(f"Query execution failed: {safe_msg}") from err
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass


def init_db() -> bool:
    """
    Initializes database tables and indexes safely using schema.sql.
    Supports cloud databases where database name is pre-created,
    as well as local development where database creation is allowed.
    """
    if not MYSQL_AVAILABLE:
        logger.warning("Cannot initialize DB: mysql-connector-python is not installed.")
        return False

    schema_file = config.BASE_DIR / "schema.sql"
    if not schema_file.exists():
        schema_file = config.BASE_DIR / "src" / "database" / "schema.sql"
    if not schema_file.exists():
        logger.error(f"Schema file not found at {schema_file}")
        return False

    try:
        # Step 1: Ensure database exists (for local MySQL if allowed)
        try:
            conn_server = get_db_connection(use_database=False, force_retry=True)
            cur = conn_server.cursor()
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` DEFAULT CHARACTER SET utf8mb4;")
            conn_server.commit()
            cur.close()
            conn_server.close()
        except Exception as db_create_err:
            # On restricted cloud databases, user may not have CREATE DATABASE privilege.
            # That is normal if the cloud provider already provisioned the database.
            logger.debug(f"Notice during database check: {_sanitize_error_msg(db_create_err)}")

        # Step 2: Read and execute schema statements against target database
        with open(schema_file, "r", encoding="utf-8") as f:
            sql_script = f.read()

        conn = get_db_connection(use_database=True, force_retry=True)
        cursor = conn.cursor()

        # Split and execute individual statements
        statements = [stmt.strip() for stmt in sql_script.split(";") if stmt.strip()]
        for stmt in statements:
            # Strip comment lines
            lines = [l for l in stmt.splitlines() if not l.strip().startswith("--") and not l.strip().startswith("/*")]
            clean_stmt = "\n".join(lines).strip()
            if clean_stmt:
                cursor.execute(clean_stmt)

        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Database '{config.DB_NAME}' schema initialized successfully.")
        return True

    except Exception as err:
        safe_msg = _sanitize_error_msg(err)
        logger.error(f"Failed to initialize database schema: {safe_msg}")
        raise DatabaseQueryError(f"Database schema initialization failed: {safe_msg}") from err


class DatabaseManager:
    """Helper class for managing database operations and health diagnostics."""

    @staticmethod
    def test_connection() -> Dict[str, Any]:
        """
        Tests the connection to MySQL and returns status report without credentials.
        """
        if not MYSQL_AVAILABLE:
            return {
                "success": False,
                "message": "Driver missing: 'mysql-connector-python' not installed.",
            }

        try:
            conn = get_db_connection(use_database=True, force_retry=True)
            if conn and conn.is_connected():
                db_info = conn.get_server_info()
                conn.close()
                return {
                    "success": True,
                    "message": f"Connected to MySQL Server v{db_info} (Database: '{config.DB_NAME}')",
                }
        except DatabaseConnectionError as db_err:
            return {"success": False, "message": str(db_err)}
        except Exception as err:
            return {"success": False, "message": f"Connection check failed: {_sanitize_error_msg(err)}"}

        return {"success": False, "message": "Unknown error during DB connection test."}

    @staticmethod
    def initialize_schema() -> bool:
        """Runs database schema setup."""
        return init_db()
