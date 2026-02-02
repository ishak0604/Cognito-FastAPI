from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from uuid import UUID
import re


class SignUpSchema(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def strong_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must include uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must include number")
        return v


class ConfirmSchema(BaseModel):
    email: EmailStr
    otp: str


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

    @field_validator("new_password")
    def strong_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must include uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must include number")
        return v


class UserResponse(BaseModel):
    id: UUID
    email: Optional[str]  # Allow None
    role: Optional[str]   # Allow None

    class Config:
        orm_mode = True
