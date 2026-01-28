"""Password-related endpoints: forgot and reset."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth_schemas import ForgotPasswordRequest, ResetPasswordRequest, SuccessResponse, ErrorResponse
from app.services.user_authentication import forgot_password, reset_password
from app.exceptions import AuthException

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/forgot-password", response_model=SuccessResponse, status_code=200, responses={
    200: {"model": SuccessResponse, "description": "Password reset link sent"},
    401: {"model": ErrorResponse, "description": "Email not found"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def forgot_password_endpoint(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    try:
        result = forgot_password(db, payload.email)
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


@router.post("/reset-password", response_model=SuccessResponse, status_code=200, responses={
    200: {"model": SuccessResponse, "description": "Password reset successfully"},
    400: {"model": ErrorResponse, "description": "Invalid or expired token"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def reset_password_endpoint(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        result = reset_password(db, payload.token, payload.password)
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
