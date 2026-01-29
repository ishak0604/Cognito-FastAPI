from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional


def validate_password_strength(password: str) -> str:
    """Validate password complexity requirements."""
    if not password or password.strip() == '':
        raise ValueError('Password cannot be empty')
    
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    
    # Single pass validation for better performance
    has_upper = has_digit = False
    for char in password:
        if char.isupper():
            has_upper = True
        elif char.isdigit():
            has_digit = True
        # Early exit if both conditions met
        if has_upper and has_digit:
            break
    
    if not has_upper:
        errors.append("Password must contain at least one uppercase letter (A-Z)")
    if not has_digit:
        errors.append("Password must contain at least one number (0-9)")
    
    if errors:
        raise ValueError(" and ".join(errors))
    
    return password


class SignupRequest(BaseModel):
    """Schema for user signup with validation."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "Password123"
            }
        }
    )
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        max_length=100,
        description="Password must be at least 8 characters"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or v.strip() == '':
            raise ValueError('Password cannot be empty')
        
        errors = []
        if len(v) < 8:
            errors.append("Password must be at least 8 characters")
        
        # Single pass validation
        has_upper = has_digit = False
        for char in v:
            if char.isupper():
                has_upper = True
            elif char.isdigit():
                has_digit = True
            if has_upper and has_digit:
                break
        
        if not has_upper:
            errors.append("Password must contain at least one uppercase letter (A-Z)")
        if not has_digit:
            errors.append("Password must contain at least one number (0-9)")
        
        if errors:
            raise ValueError(" and ".join(errors))
        
        return v


class LoginRequest(BaseModel):
    """Schema for user login."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "Password123"
            }
        }
    )
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")


class ConfirmSignupRequest(BaseModel):
    """Schema for confirming email signup."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "verification_token_here"
            }
        }
    )
    
    token: str = Field(..., min_length=1, description="Email verification token")


class ResendVerificationRequest(BaseModel):
    """Schema for resending verification email."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )
    
    email: EmailStr = Field(..., description="User email address")


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )
    
    email: EmailStr = Field(..., description="User email address")


class ResetPasswordRequest(BaseModel):
    """Schema for password reset."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "reset_token_here",
                "password": "NewPassword123"
            }
        }
    )
    
    token: str = Field(..., min_length=1, description="Password reset token")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_strength(v)


class SuccessResponse(BaseModel):
    """Standard success response."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Signup successful",
                "data": None
            }
        }
    )
    
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "message": "Email already exists",
                "error_code": "EMAIL_EXISTS",
                "details": None
            }
        }
    )
    
    success: bool = False
    message: str
    error_code: str
    details: Optional[dict] = None
