"""
Study Smarter - Production Configuration Module
Loads configuration safely from environment variables and deployment secrets.
Supports both local development (.env) and cloud production (Streamlit Cloud secrets / OS env).
Never hard-codes credentials or API keys.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Base Directory of the Project (cross-platform Path)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file if present (local development)
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


def _get_setting(key: str, default: Any = None) -> Any:
    """
    Safely retrieves a configuration setting in order of priority:
    1. Streamlit Cloud secrets (st.secrets):
       - Exact key (e.g. "DB_HOST")
       - Canonical aliases (e.g. "MYSQL_HOST", "MYSQL_DATABASE")
       - Lowercase / Uppercase keys
       - Nested tables (st.secrets["mysql"]["host"], st.secrets["gemini"]["api_key"])
    2. OS environment variables (exact, aliases, upper, lower)
    3. Fallback default
    """
    # Key aliases for consistent cross-environment configuration
    aliases = [key, key.upper(), key.lower()]
    if key == "DB_HOST":
        aliases.extend(["MYSQL_HOST", "mysql_host"])
    elif key == "DB_NAME":
        aliases.extend(["MYSQL_DATABASE", "mysql_database", "DATABASE_NAME", "database_name"])
    elif key == "DB_PORT":
        aliases.extend(["MYSQL_PORT", "mysql_port"])
    elif key == "DB_USER":
        aliases.extend(["MYSQL_USER", "mysql_user"])
    elif key == "DB_PASSWORD":
        aliases.extend(["MYSQL_PASSWORD", "mysql_password"])
    elif key in ("GEMINI_API_KEY", "AI_API_KEY"):
        aliases.extend(["GEMINI_API_KEY", "AI_API_KEY", "gemini_api_key", "ai_api_key"])

    # 1. Streamlit Cloud secrets (Highest Priority in Cloud Deployment)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            for k in aliases:
                try:
                    if k in st.secrets:
                        secret_val = st.secrets[k]
                        if secret_val is not None and str(secret_val).strip() != "":
                            return str(secret_val).strip()
                except Exception:
                    pass

            # Nested mysql/database table lookup
            if key.startswith("DB_") or "MYSQL" in key:
                suffix = key[3:].lower() if key.startswith("DB_") else key.replace("MYSQL_", "").lower()
                for section in ("mysql", "database", "connections"):
                    try:
                        if section in st.secrets:
                            sec = st.secrets[section]
                            if hasattr(sec, "get"):
                                if section == "connections" and "mysql" in sec:
                                    sec = sec["mysql"]
                                sec_val = sec.get(suffix) or sec.get(suffix.upper()) or sec.get(key)
                                if sec_val is not None and str(sec_val).strip() != "":
                                    return str(sec_val).strip()
                    except Exception:
                        pass

            # Nested ai / gemini table lookup
            if key in ("GEMINI_API_KEY", "AI_API_KEY"):
                for section in ("gemini", "ai", "google"):
                    try:
                        if section in st.secrets:
                            sec = st.secrets[section]
                            if hasattr(sec, "get"):
                                sec_val = sec.get("api_key") or sec.get("key") or sec.get("GEMINI_API_KEY")
                                if sec_val is not None and str(sec_val).strip() != "":
                                    return str(sec_val).strip()
                    except Exception:
                        pass
    except Exception:
        pass

    # 2. OS environment variables (Local .env or container environment)
    for k in aliases:
        val = os.getenv(k)
        if val is not None and str(val).strip() != "":
            return str(val).strip()

    return default


class Config:
    """Application configuration settings loader supporting local and cloud deployment."""

    # Base Directory of the Project
    BASE_DIR: Path = BASE_DIR

    # Project Information
    APP_NAME: str = "Study Smarter"
    SUBTITLE: str = "Personal Question-Bank Practice System"
    VERSION: str = "2.0.0"

    # Analytics & Performance Thresholds
    WEAK_TOPIC_THRESHOLD: float = 60.0
    STRONG_TOPIC_THRESHOLD: float = 75.0

    @property
    def APP_ENV(self) -> str:
        return _get_setting("APP_ENV", "development")

    @property
    def is_production(self) -> bool:
        """Determines if the application is running in production mode or using a remote cloud DB."""
        env = str(self.APP_ENV).strip().lower()
        if env in ("production", "prod"):
            return True
        if "aivencloud" in str(self.DB_HOST).lower():
            return True
        return False

    @property
    def APP_HOST(self) -> str:
        return _get_setting("APP_HOST", "localhost")

    @property
    def APP_PORT(self) -> int:
        return int(_get_setting("APP_PORT", "8501"))

    @property
    def LOG_LEVEL(self) -> str:
        return _get_setting("LOG_LEVEL", "INFO")

    @property
    def DB_HOST(self) -> str:
        return _get_setting("DB_HOST", "localhost")

    @property
    def DB_PORT(self) -> int:
        return int(_get_setting("DB_PORT", "15536" if "aivencloud" in str(self.DB_HOST) else "3306"))

    @property
    def DB_USER(self) -> str:
        return _get_setting("DB_USER", "avnadmin" if "aivencloud" in str(self.DB_HOST) else "root")

    @property
    def DB_PASSWORD(self) -> str:
        return _get_setting("DB_PASSWORD", "")

    @property
    def DB_NAME(self) -> str:
        return _get_setting("DB_NAME", "defaultdb")

    @property
    def DB_TIMEOUT(self) -> int:
        return int(_get_setting("DB_TIMEOUT", "10"))

    @property
    def DB_SSL_CA(self) -> Optional[str]:
        return _get_setting("DB_SSL_CA", None)

    @property
    def DB_SSL_DISABLED(self) -> bool:
        # Check DB_SSL first (standard Streamlit / cloud secret)
        db_ssl = _get_setting("DB_SSL")
        if db_ssl is not None:
            if str(db_ssl).strip().lower() in ("false", "0", "no", "disabled"):
                return True
            return False
        return str(_get_setting("DB_SSL_DISABLED", "false")).lower() in ("true", "1", "yes")

    @property
    def GEMINI_API_KEY(self) -> str:
        return _get_setting("GEMINI_API_KEY") or _get_setting("AI_API_KEY", "")

    @property
    def AI_API_KEY(self) -> str:
        return self.GEMINI_API_KEY

    @property
    def AI_MODEL_NAME(self) -> str:
        return _get_setting("AI_MODEL_NAME", "gemini-flash-lite-latest")

    @property
    def AI_MODEL_FALLBACK(self) -> str:
        return _get_setting("AI_MODEL_FALLBACK", "gemini-flash-latest")

    @property
    def GEMINI_BATCH_SIZE(self) -> int:
        return int(_get_setting("GEMINI_BATCH_SIZE", "10"))

    @property
    def SHOW_ADMIN_REVIEW(self) -> bool:
        return str(_get_setting("SHOW_ADMIN_REVIEW", "false")).strip().lower() in ("true", "1", "yes")

    def validate_database_config(self) -> bool:
        """Checks if minimum database parameters are configured."""
        return bool(self.DB_HOST and self.DB_USER and self.DB_NAME)

    def validate_gemini_config(self) -> bool:
        """Checks if Gemini API key is configured."""
        key = (self.GEMINI_API_KEY or "").strip()
        return bool(key and key != "your_gemini_api_key")

    def get_status_summary(self) -> Dict[str, str]:
        """
        Returns safe configuration status report without exposing sensitive credentials.
        """
        db_ok = self.validate_database_config()
        ai_ok = self.validate_gemini_config()
        return {
            "environment": self.APP_ENV,
            "database_config": "Available" if db_ok else "Missing",
            "gemini_config": "Available" if ai_ok else "Missing",
            "db_target": f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}",
        }


# Instantiate global config object
config = Config()
