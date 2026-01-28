"""Login-related endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth_schemas import LoginRequest, SuccessResponse, ErrorResponse
from app.services.user_authentication import login_user
from app.exceptions import AuthException

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=SuccessResponse, status_code=200, responses={
    200: {"model": SuccessResponse, "description": "Login successful"},
    401: {"model": ErrorResponse, "description": "Invalid credentials"},
    403: {"model": ErrorResponse, "description": "Email not verified"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = login_user(db, payload.email, payload.password)
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
