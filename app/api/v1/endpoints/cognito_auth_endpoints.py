"""Cognito authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth_schemas import (
    SignupRequest,
    SignupResponse,
    ConfirmSignupRequest,
    ConfirmSignupResponse,
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SuccessResponse,
    ErrorResponse
)
from app.services.cognito_service import cognito_service
from app.core.cognito_dependencies import get_current_user_cognito
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Signup",
    description="Create a new user account with Cognito",
    responses={
        201: {"model": SignupResponse, "description": "Signup successful"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def signup(payload: SignupRequest) -> SignupResponse:
    """Create a new user account with Cognito."""
    try:
        result = cognito_service.sign_up(payload.email, payload.password)
        if result['success']:
            return SignupResponse(**result)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": result['message'],
                    "error_code": "SIGNUP_FAILED"
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post(
    "/confirm-signup",
    response_model=ConfirmSignupResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm Signup",
    description="Confirm user signup with verification code",
    responses={
        200: {"model": ConfirmSignupResponse, "description": "Confirmation successful"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def confirm_signup(payload: ConfirmSignupRequest) -> ConfirmSignupResponse:
    """Confirm user signup with verification code."""
    try:
        result = cognito_service.confirm_sign_up(payload.email, payload.otp)
        if result['success']:
            return ConfirmSignupResponse(**result)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": result['message'],
                    "error_code": "CONFIRMATION_FAILED"
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post(
    "/resend-confirmation",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend Confirmation Code",
    description="Resend verification code for signup confirmation",
    responses={
        200: {"model": SuccessResponse, "description": "Code sent successfully"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def resend_confirmation(email: str) -> SuccessResponse:
    """Resend confirmation code."""
    try:
        result = cognito_service.resend_confirmation_code(email)
        if result['success']:
            return SuccessResponse(**result)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": result['message'],
                    "error_code": "RESEND_FAILED"
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate user with email and password",
    responses={
        200: {"model": LoginResponse, "description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def login(payload: LoginRequest) -> LoginResponse:
    """Authenticate user with Cognito."""
    try:
        result = cognito_service.admin_initiate_auth(payload.email, payload.password)
        if result['success']:
            return LoginResponse(**result)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": result['message'],
                    "error_code": "LOGIN_FAILED"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Forgot Password",
    description="Initiate password reset process",
    responses={
        200: {"model": ForgotPasswordResponse, "description": "Reset code sent"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def forgot_password(payload: ForgotPasswordRequest) -> ForgotPasswordResponse:
    """Initiate forgot password flow."""
    try:
        result = cognito_service.forgot_password(payload.email)
        if result['success']:
            return ForgotPasswordResponse(**result)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": result['message'],
                    "error_code": "FORGOT_PASSWORD_FAILED"
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset Password",
    description="Reset user password with verification code",
    responses={
        200: {"model": ResetPasswordResponse, "description": "Password reset successful"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def reset_password(payload: ResetPasswordRequest) -> ResetPasswordResponse:
    """Reset user password with verification code."""
    try:
        result = cognito_service.confirm_forgot_password(payload.email, payload.otp, payload.new_password)
        if result['success']:
            return ResetPasswordResponse(**result)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": result['message'],
                    "error_code": "RESET_PASSWORD_FAILED"
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.post(
    "/refresh-token",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Token",
    description="Refresh access token using refresh token",
    responses={
        200: {"model": SuccessResponse, "description": "Token refreshed"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def refresh_token(refresh_token: str) -> SuccessResponse:
    """Refresh access token using refresh token."""
    try:
        result = cognito_service.refresh_token(refresh_token)
        if result['success']:
            return SuccessResponse(
                success=True,
                message="Token refreshed successfully",
                data={
                    "access_token": result['access_token'],
                    "expires_in": result['expires_in']
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": result['message'],
                    "error_code": "TOKEN_REFRESH_FAILED"
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )


@router.get(
    "/me",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User",
    description="Get current authenticated user information",
    responses={
        200: {"model": SuccessResponse, "description": "User information retrieved"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def get_current_user(current_user: Dict[str, Any] = Depends(get_current_user_cognito)) -> SuccessResponse:
    """Get current authenticated user information."""
    try:
        return SuccessResponse(
            success=True,
            message="User information retrieved successfully",
            data=current_user
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )
