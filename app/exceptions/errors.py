"""
Centralized exception classes and helpers.

This consolidates custom auth exceptions and Pydantic formatting helpers.
"""


class AuthException(Exception):
    """Base authentication exception."""
    def __init__(self, message: str, error_code: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class EmailAlreadyExists(AuthException):
    """Raised when email already exists in database."""
    def __init__(self):
        super().__init__(
            message="This email is already registered. Please log in or use a different email.",
            error_code="EMAIL_EXISTS",
            status_code=409
        )


class InvalidCredentials(AuthException):
    """Raised when email or password is invalid."""
    def __init__(self, field: str = None):
        details = {}
        if field == "email":
            message = "Email not found. Please check your email or sign up."
            details["field"] = "email"
        elif field == "password":
            message = "Password is incorrect. Please try again."
            details["field"] = "password"
        else:
            message = "Email or password is incorrect. Please try again."

        super().__init__(
            message=message,
            error_code="INVALID_CREDENTIALS",
            status_code=401,
            details=details
        )


class EmailNotVerified(AuthException):
    """Raised when user tries to login with unverified email."""
    def __init__(self):
        super().__init__(
            message="Email not verified. Please verify your email to login.",
            error_code="EMAIL_NOT_VERIFIED",
            status_code=403
        )


class InvalidToken(AuthException):
    """Raised when verification or reset token is invalid."""
    def __init__(self, token_type: str = "token"):
        try:
            if token_type == "verification token":
                message = "Verification link has expired or is invalid. Please request a new verification email."
            elif token_type == "reset token":
                message = "Password reset link has expired. Please request a new password reset link."
            else:
                message = f"Invalid or expired {token_type}. Please try again."

            super().__init__(
                message=message,
                error_code="INVALID_TOKEN",
                status_code=400
            )
        except Exception:
            # Fallback initialization
            self.message = f"Invalid or expired {token_type}. Please try again."
            self.error_code = "INVALID_TOKEN"
            self.status_code = 400
            self.details = {}
            Exception.__init__(self, self.message)


class ValidationError(AuthException):
    """Raised when validation fails."""
    def __init__(self, message: str, details: dict = None):
        try:
            super().__init__(
                message=message,
                error_code="VALIDATION_ERROR",
                status_code=422,
                details=details or {}
            )
        except Exception:
            # Fallback initialization if parent init fails
            self.message = message
            self.error_code = "VALIDATION_ERROR"
            self.status_code = 422
            self.details = details or {}
            Exception.__init__(self, message)


def _format_missing_field_error(field: str) -> str:
    """Format missing field error message."""
    field_messages = {
        "email": "Email is required",
        "password": "Password is required",
        "token": "Token is required"
    }
    return field_messages.get(field, f"{field.replace('_', ' ').title()} is required")


def _format_length_error(field: str, msg: str) -> str:
    """Format length validation error message."""
    if field == "password":
        return "Password must be at least 8 characters"
    elif field == "email":
        return "Email cannot be empty"
    elif field == "token":
        return "Token cannot be empty"
    return msg


def _format_value_error(field: str, msg: str) -> str:
    """Format value validation error message."""
    error_mappings = {
        "Email cannot be empty": "Email cannot be empty",
        "Password cannot be empty": "Password cannot be empty",
        "Token cannot be empty": "Token cannot be empty",
        "Email format is invalid": "Email format is invalid. Use format: user@example.com",
        "Password must be at least 8 characters": "Password must be at least 8 characters",
        "Password must contain at least one uppercase letter": "Password must contain at least one uppercase letter (A-Z)",
        "Password must contain at least one number": "Password must contain at least one number (0-9)"
    }
    
    for key, value in error_mappings.items():
        if key in msg:
            return value
    
    return msg


def format_validation_errors(exc_errors: list) -> tuple[dict, int]:
    """
    Format Pydantic validation errors into readable, user-friendly format.

    Args:
        exc_errors: List of Pydantic validation errors

    Returns:
        tuple: (error_details_dict, status_code)
    """
    if not exc_errors:
        return {}, 422
    
    errors = {}

    for error in exc_errors:
        try:
            field = str(error["loc"][-1]) if error.get("loc") else "unknown"
            error_type = error.get("type", "unknown")
            msg = error.get("msg", "Validation error")

            if error_type == "missing":
                errors[field] = _format_missing_field_error(field)
            elif "at least" in msg.lower() and "character" in msg.lower():
                errors[field] = _format_length_error(field, msg)
            elif error_type == "value_error":
                errors[field] = _format_value_error(field, msg)
            else:
                errors[field] = msg
        except (KeyError, TypeError, IndexError):
            # Handle malformed error objects gracefully
            errors["validation"] = "Invalid validation error format"

    return errors, 422


def format_exception_response(exception: AuthException) -> dict:
    """
    Format custom exception into HTTP response.
    """
    try:
        return {
            "success": False,
            "message": getattr(exception, 'message', str(exception)),
            "error_code": getattr(exception, 'error_code', 'UNKNOWN_ERROR'),
            "details": getattr(exception, 'details', {})
        }
    except Exception:
        # Fallback response if exception formatting fails
        return {
            "success": False,
            "message": "An error occurred",
            "error_code": "FORMATTING_ERROR",
            "details": {}
        }
