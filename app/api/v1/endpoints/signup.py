"""Signup-related endpoints with Cognito integration."""

import logging
from fastapi import APIRouter, HTTPException

from app.schemas.auth_schemas import SignupRequest, ConfirmSignupRequest, ResendVerificationRequest, SuccessResponse, ErrorResponse
from app.services.cognito_service import cognito_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=SuccessResponse, status_code=201, responses={
    201: {"model": SuccessResponse, "description": "User created successfully in Cognito"},
    409: {"model": ErrorResponse, "description": "Email already exists"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def signup(payload: SignupRequest):
    """Create a new user in AWS Cognito User Pool."""
    try:
        logger.info(f"Cognito signup attempt for email: {payload.email}")

        result = cognito_service.signup_user(
            email=payload.email,
            password=payload.password,
            first_name=payload.first_name,
            last_name=payload.last_name
        )

        if result['success']:
            return SuccessResponse(
                success=True,
                message=result['message'],
                data={
                    "email": payload.email,
                    "user_id": result.get('user_id')
                }
            )
        else:
            # Handle Cognito-specific errors
            status_code = 400
            if result.get('error_code') == 'EMAIL_EXISTS':
                status_code = 409

            raise HTTPException(
                status_code=status_code,
                detail={
                    "success": False,
                    "message": result['message'],
                    "error_code": result.get('error_code', 'SIGNUP_FAILED'),
                    "details": None
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected signup error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR",
                "details": None
            }
        )


@router.post("/confirm-signup", response_model=SuccessResponse, status_code=200, responses={
    200: {"model": SuccessResponse, "description": "Email verified successfully"},
    400: {"model": ErrorResponse, "description": "Invalid or expired confirmation code"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def confirm_email(payload: ConfirmSignupRequest):
    """Confirm user email with verification code from Cognito."""
    try:
        logger.info(f"Email confirmation attempt for: {payload.email}")

        result = cognito_service.confirm_signup(payload.email, payload.confirmation_code)

        if result['success']:
            return SuccessResponse(
                success=True,
                message=result['message'],
                data={"email": payload.email}
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": result['message'],
                    "error_code": result.get('error_code', 'CONFIRMATION_FAILED'),
                    "details": None
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected confirmation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR",
                "details": None
            }
        )


@router.post("/resend-verification", response_model=SuccessResponse, status_code=200, responses={
    200: {"model": SuccessResponse, "description": "New verification code sent"},
    401: {"model": ErrorResponse, "description": "Email not found"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def resend_verification_email(payload: ResendVerificationRequest):
    """Resend email verification code via Cognito."""
    try:
        logger.info(f"Resend verification code for: {payload.email}")

        result = cognito_service.resend_confirmation_code(payload.email)

        if result['success']:
            return SuccessResponse(
                success=True,
                message=result['message'],
                data={"email": payload.email}
            )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "message": result['message'],
                    "error_code": "RESEND_FAILED",
                    "details": None
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected resend verification error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR",
                "details": None
            }
        )
