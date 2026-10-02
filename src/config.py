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
    1. OS environment variable
    2. Streamlit Cloud secrets (st.secrets) if running under Streamlit
    3. Fallback default
    """
    val = os.getenv(key)
    if val is not None and str(val).strip() != "":
        return str(val).strip()

    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            secret_val = st.secrets[key]
            if secret_val is not None and str(secret_val).strip() != "":
                return str(secret_val).strip()
    except Exception:
        pass

    return default


class Config:
    """Application configuration settings loader supporting local and cloud deployment."""

    # Base Directory of the Project
    BASE_DIR: Path = BASE_DIR

    # Project Information
    APP_NAME: str = "Study Smarter"
    SUBTITLE: str = "Personal Question-Bank Practice System"
    VERSION: str = "2.0.0"

    # Environment & Server
    APP_ENV: str = _get_setting("APP_ENV", "development")
    APP_HOST: str = _get_setting("APP_HOST", "localhost")
    APP_PORT: int = int(_get_setting("APP_PORT", "8501"))
    LOG_LEVEL: str = _get_setting("LOG_LEVEL", "INFO")

    # Analytics & Performance Thresholds
    WEAK_TOPIC_THRESHOLD: float = 60.0
    STRONG_TOPIC_THRESHOLD: float = 75.0

    # Database Configuration (Cloud & Local MySQL)
    DB_HOST: str = _get_setting("DB_HOST", "localhost")
    DB_PORT: int = int(_get_setting("DB_PORT", "3306"))
    DB_USER: str = _get_setting("DB_USER", "root")
    DB_PASSWORD: str = _get_setting("DB_PASSWORD", "")
    DB_NAME: str = _get_setting("DB_NAME", "study_smarter_db")
    DB_TIMEOUT: int = int(_get_setting("DB_TIMEOUT", "10"))
    DB_SSL_CA: Optional[str] = _get_setting("DB_SSL_CA", None)
    DB_SSL_DISABLED: bool = str(_get_setting("DB_SSL_DISABLED", "false")).lower() in ("true", "1", "yes")

    # AI Service Configuration (Gemini API)
    GEMINI_API_KEY: str = _get_setting("GEMINI_API_KEY") or _get_setting("AI_API_KEY", "")
    AI_API_KEY: str = GEMINI_API_KEY
    AI_MODEL_NAME: str = _get_setting("AI_MODEL_NAME", "gemini-flash-lite-latest")
    AI_MODEL_FALLBACK: str = _get_setting("AI_MODEL_FALLBACK", "gemini-flash-latest")
    GEMINI_BATCH_SIZE: int = int(_get_setting("GEMINI_BATCH_SIZE", "10"))

    # Admin & Review Controls
    SHOW_ADMIN_REVIEW: bool = str(_get_setting("SHOW_ADMIN_REVIEW", "false")).strip().lower() in ("true", "1", "yes")

    @classmethod
    def validate_database_config(cls) -> bool:
        """Checks if minimum database parameters are configured."""
        return bool(cls.DB_HOST and cls.DB_USER and cls.DB_NAME)

    @classmethod
    def validate_gemini_config(cls) -> bool:
        """Checks if Gemini API key is configured."""
        key = (cls.GEMINI_API_KEY or "").strip()
        return bool(key and key != "your_gemini_api_key")

    @classmethod
    def get_status_summary(cls) -> Dict[str, str]:
        """
        Returns safe configuration status report without exposing sensitive credentials.
        """
        db_ok = cls.validate_database_config()
        ai_ok = cls.validate_gemini_config()
        return {
            "environment": cls.APP_ENV,
            "database_config": "Available" if db_ok else "Missing",
            "gemini_config": "Available" if ai_ok else "Missing",
            "db_target": f"{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}",
        }


# Instantiate global config object
config = Config()
