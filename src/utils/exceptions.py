"""
Study Smarter - Custom Exception Handler Module
Defines application-specific exceptions for clean error handling.
"""


class StudySmarterBaseException(Exception):
    """Base exception class for all Study Smarter application errors."""
    pass


StudySmarterException = StudySmarterBaseException


class ConfigurationError(StudySmarterBaseException):
    """Raised when environment variables or settings are missing or invalid."""
    pass


class DatabaseConnectionError(StudySmarterBaseException):
    """Raised when the database connection fails or times out."""
    pass


class DatabaseQueryError(StudySmarterBaseException):
    """Raised when a database query execution fails."""
    pass


class PDFProcessingError(StudySmarterBaseException):
    """Raised when PDF extraction fails or format is invalid (for future use)."""
    pass


class AIServiceError(StudySmarterBaseException):
    """Raised when AI API request fails or returns invalid response (for future use)."""
    pass


class QuizNotFoundError(StudySmarterBaseException):
    """Raised when a requested quiz does not exist in the database."""
    pass
