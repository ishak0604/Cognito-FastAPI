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


class ValidationError(AuthException):
    """Raised when validation fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details or {}
        )


def format_validation_errors(exc_errors: list) -> tuple[dict, int]:
    """
    Format Pydantic validation errors into readable, user-friendly format.

    Args:
        exc_errors: List of Pydantic validation errors

    Returns:
        tuple: (error_details_dict, status_code)
    """
    errors = {}

    for error in exc_errors:
        field = str(error["loc"][-1]) if error["loc"] else "unknown"
        error_type = error["type"]
        msg = error["msg"]

        if error_type == "missing":
            if field == "email":
                errors[field] = "Email is required"
            elif field == "password":
                errors[field] = "Password is required"
            elif field == "token":
                errors[field] = "Token is required"
            else:
                errors[field] = f"{field.replace('_', ' ').title()} is required"

        elif "at least" in msg.lower() and "character" in msg.lower():
            if field == "password":
                errors[field] = "Password must be at least 8 characters"
            elif field == "email":
                errors[field] = "Email cannot be empty"
            elif field == "token":
                errors[field] = "Token cannot be empty"
            else:
                errors[field] = msg

        elif error_type == "value_error":
            if "Email cannot be empty" in msg:
                errors[field] = "Email cannot be empty"
            elif "Password cannot be empty" in msg:
                errors[field] = "Password cannot be empty"
            elif "Token cannot be empty" in msg:
                errors[field] = "Token cannot be empty"
            elif "Email format is invalid" in msg:
                errors[field] = "Email format is invalid. Use format: user@example.com"
            elif "Password must be at least 8 characters" in msg:
                errors[field] = "Password must be at least 8 characters"
            elif "Password must contain at least one uppercase letter" in msg:
                errors[field] = "Password must contain at least one uppercase letter (A-Z)"
            elif "Password must contain at least one number" in msg:
                errors[field] = "Password must contain at least one number (0-9)"
            elif "and" in msg and "Password" in msg:
                errors[field] = msg
            else:
                errors[field] = msg

        else:
            errors[field] = msg

    return errors, 422


def format_exception_response(exception: AuthException) -> dict:
    """
    Format custom exception into HTTP response.
    """
    return {
        "success": False,
        "message": exception.message,
        "error_code": exception.error_code,
        "details": exception.details
    }
