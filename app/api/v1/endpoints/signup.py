"""Signup-related endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth_schemas import SignupRequest, ConfirmSignupRequest, ResendVerificationRequest, SuccessResponse, ErrorResponse
from app.services.user_auth_service import signup_user, confirm_signup, resend_verification
from app.exceptions import AuthException, format_exception_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=SuccessResponse, status_code=201, responses={
    201: {"model": SuccessResponse, "description": "User created successfully"},
    409: {"model": ErrorResponse, "description": "Email already exists"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        logger.info(f"Signup attempt for email: {payload.email}")
        result = signup_user(db, payload.email, payload.password)
        return result
    except AuthException as e:
        logger.warning(f"Signup failed: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=format_exception_response(e))
    except Exception as e:
        logger.error(f"Unexpected signup error: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR",
            "details": None
        })


@router.post("/confirm-signup", response_model=SuccessResponse, status_code=200, responses={
    200: {"model": SuccessResponse, "description": "Email verified successfully"},
    400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def confirm_email(payload: ConfirmSignupRequest, db: Session = Depends(get_db)):
    try:
        logger.info("Email confirmation attempt")
        result = confirm_signup(db, payload.token)
        return result
    except AuthException as e:
        logger.warning(f"Email confirmation failed: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=format_exception_response(e))
    except Exception as e:
        logger.error(f"Unexpected confirmation error: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR",
            "details": None
        })


@router.post("/resend-verification", response_model=SuccessResponse, status_code=200, responses={
    200: {"model": SuccessResponse, "description": "New verification token sent"},
    401: {"model": ErrorResponse, "description": "Email not found or already verified"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def resend_verification_email(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    try:
        result = resend_verification(db, payload.email)
        return result
    except AuthException as e:
        raise HTTPException(status_code=e.status_code, detail=format_exception_response(e))
    except Exception:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR",
            "details": None
        })