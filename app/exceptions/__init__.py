"""Exceptions package for authentication operations."""

from app.exceptions.errors import (
    AuthException,
    EmailAlreadyExists,
    InvalidCredentials,
    EmailNotVerified,
    InvalidToken,
    ValidationError,
    format_validation_errors,
    format_exception_response
)

__all__ = [
    "AuthException",
    "EmailAlreadyExists",
    "InvalidCredentials",
    "EmailNotVerified",
    "InvalidToken",
    "ValidationError",
    "format_validation_errors",
    "format_exception_response"
]
