"""Custom exceptions for openaur.

Standardized exception hierarchy for consistent error handling.
"""

from typing import Any


class OpenAurException(Exception):
    """Base exception for openaur."""

    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, message: str | None = None, **kwargs: Any):
        self.message = message or self.detail
        self.extra = kwargs
        super().__init__(self.message)


# Client Errors (4xx)


class ValidationError(OpenAurException):
    """Input validation failed."""

    status_code = 400
    detail = "Validation error"


class NotFoundError(OpenAurException):
    """Resource not found."""

    status_code = 404
    detail = "Not found"


class AlreadyExistsError(OpenAurException):
    """Resource already exists."""

    status_code = 409
    detail = "Resource already exists"


class ConfigurationError(OpenAurException):
    """Invalid configuration."""

    status_code = 400
    detail = "Configuration error"


class AuthenticationError(OpenAurException):
    """Authentication failed."""

    status_code = 401
    detail = "Authentication failed"


class AuthorizationError(OpenAurException):
    """Authorization failed (insufficient permissions)."""

    status_code = 403
    detail = "Forbidden"


# Package Management Errors


class PackageNotFoundError(NotFoundError):
    """Package not found in repositories or AUR."""

    detail = "Package not found"


class PackageInstallError(OpenAurException):
    """Package installation failed."""

    status_code = 500
    detail = "Package installation failed"


class PackageRemoveError(OpenAurException):
    """Package removal failed."""

    status_code = 500
    detail = "Package removal failed"


# Memory Errors


class MemoryNotFoundError(NotFoundError):
    """Memory not found."""

    detail = "Memory not found"


class MemoryStorageError(OpenAurException):
    """Failed to store memory."""

    status_code = 500
    detail = "Memory storage failed"


# Session Errors


class SessionNotFoundError(NotFoundError):
    """Session not found."""

    detail = "Session not found"


class SessionExecutionError(OpenAurException):
    """Session command execution failed."""

    status_code = 500
    detail = "Session execution failed"


# AI/Model Errors


class ModelError(OpenAurException):
    """AI model error."""

    status_code = 502
    detail = "AI model error"


class RateLimitError(OpenAurException):
    """Rate limit exceeded."""

    status_code = 429
    detail = "Rate limit exceeded"


class InvalidAPIKeyError(AuthenticationError):
    """Invalid or missing API key."""

    detail = "Invalid API key"


# Service Errors


class ServiceUnavailableError(OpenAurException):
    """External service unavailable."""

    status_code = 503
    detail = "Service unavailable"


class DatabaseError(OpenAurException):
    """Database operation failed."""

    status_code = 500
    detail = "Database error"
