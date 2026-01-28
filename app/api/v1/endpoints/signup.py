"""Signup-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth_schemas import SignupRequest, ConfirmSignupRequest, SuccessResponse, ErrorResponse
from app.services.user_authentication import signup_user, confirm_signup
from app.exceptions import AuthException, format_exception_response

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=SuccessResponse, status_code=201, responses={
    201: {"model": SuccessResponse, "description": "User created successfully"},
    409: {"model": ErrorResponse, "description": "Email already exists"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        result = signup_user(db, payload.email, payload.password)
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


@router.post("/confirm-signup", response_model=SuccessResponse, status_code=200, responses={
    200: {"model": SuccessResponse, "description": "Email verified successfully"},
    400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def confirm_email(payload: ConfirmSignupRequest, db: Session = Depends(get_db)):
    try:
        result = confirm_signup(db, payload.token)
        return result
    except AuthException as e:
        raise HTTPException(status_code=e.status_code, detail={
            "success": False,
            "message": e.message,
            "error_code": e.error_code,
            "details": e.details
        })
    except Exception:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR",
            "details": None
        })
