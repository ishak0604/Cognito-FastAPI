from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List


class SignupRequest(BaseModel):
    """Schema for user signup with validation."""
    email: str = Field(..., min_length=1, description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password must be at least 8 characters"
    )

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not v or v.strip() == '':
            raise ValueError('Email cannot be empty')
        if '@' not in v or '.' not in v:
            raise ValueError('Email format is invalid. Use format: user@example.com')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        if not v or v.strip() == '':
            raise ValueError('Password cannot be empty')
        
        errors = []
        
        if len(v) < 8:
            errors.append("Password must be at least 8 characters")
        if not any(char.isupper() for char in v):
            errors.append("Password must contain at least one uppercase letter (A-Z)")
        if not any(char.isdigit() for char in v):
            errors.append("Password must contain at least one number (0-9)")
        
        if errors:
            raise ValueError(" and ".join(errors))
        
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "Password123"
            }
        }


class LoginRequest(BaseModel):
    """Schema for user login."""
    email: str = Field(..., min_length=1, description="User email address")
    password: str = Field(..., min_length=1, description="User password")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not v or v.strip() == '':
            raise ValueError('Email cannot be empty')
        if '@' not in v or '.' not in v:
            raise ValueError('Email format is invalid. Use format: user@example.com')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password."""
        if not v or v.strip() == '':
            raise ValueError('Password cannot be empty')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "Password123"
            }
        }


class ConfirmSignupRequest(BaseModel):
    """Schema for confirming email signup."""
    token: str = Field(..., description="Email verification token")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "verification_token_here"
            }
        }


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    email: str = Field(..., min_length=1, description="User email address")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not v or v.strip() == '':
            raise ValueError('Email cannot be empty')
        if '@' not in v or '.' not in v:
            raise ValueError('Email format is invalid. Use format: user@example.com')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Schema for password reset."""
    token: str = Field(..., min_length=1, description="Password reset token")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password"
    )

    @field_validator('token')
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Validate token."""
        if not v or v.strip() == '':
            raise ValueError('Token cannot be empty')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        if not v or v.strip() == '':
            raise ValueError('Password cannot be empty')
        
        errors = []
        
        if len(v) < 8:
            errors.append("Password must be at least 8 characters")
        if not any(char.isupper() for char in v):
            errors.append("Password must contain at least one uppercase letter (A-Z)")
        if not any(char.isdigit() for char in v):
            errors.append("Password must contain at least one number (0-9)")
        
        if errors:
            raise ValueError(" and ".join(errors))
        
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_here",
                "password": "NewPassword123"
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str
    data: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Signup successful",
                "data": None
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    message: str
    error_code: str
    details: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Email already exists",
                "error_code": "EMAIL_EXISTS",
                "details": None
            }
        }
