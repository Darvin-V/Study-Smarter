"""
Study Smarter - Centralized Logging Module
Configures file and console logging for the application.
"""

import logging
import sys
from pathlib import Path
from src.config import config

# Define logs directory path
LOGS_DIR = Path(config.BASE_DIR) / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOGS_DIR / "app.log"

# Map string log level to logging constant
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def setup_logger(name: str = "study_smarter") -> logging.Logger:
    """
    Creates and returns a configured logger instance.
    Logs to both standard output (console) and logs/app.log file.
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if logger is already configured
    if logger.hasHandlers():
        return logger

    log_level = LOG_LEVEL_MAP.get(config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Formatter for log messages
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Primary application logger
logger = setup_logger("study_smarter")
