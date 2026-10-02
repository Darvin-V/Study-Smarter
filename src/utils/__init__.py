"""
Study Smarter - Utilities Package
"""
from src.utils.exceptions import (
    StudySmarterBaseException,
    ConfigurationError,
    DatabaseConnectionError,
    DatabaseQueryError,
    PDFProcessingError,
    AIServiceError,
    QuizNotFoundError,
)

__all__ = [
    "StudySmarterBaseException",
    "ConfigurationError",
    "DatabaseConnectionError",
    "DatabaseQueryError",
    "PDFProcessingError",
    "AIServiceError",
    "QuizNotFoundError",
]
