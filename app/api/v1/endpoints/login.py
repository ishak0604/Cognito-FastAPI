"""Login-related endpoints with improved structure."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth_schemas import LoginRequest, SuccessResponse, ErrorResponse
from app.services.user_auth_service import get_user_auth_service, UserAuthService
from app.exceptions import AuthException

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login", 
    response_model=SuccessResponse, 
    status_code=200,
    summary="User Login",
    description="Authenticate user with email and password",
    responses={
        200: {"model": SuccessResponse, "description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Email not verified"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
def login(
    payload: LoginRequest, 
    auth_service: UserAuthService = Depends(get_user_auth_service)
) -> SuccessResponse:
    """Authenticate user and return access token.
    
    Args:
        payload: Login request with email and password
        auth_service: User authentication service
        
    Returns:
        Success response with access token
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        result = auth_service.login_user(payload.email, payload.password)
        return SuccessResponse(**result)
        
    except AuthException as e:
        raise HTTPException(
            status_code=e.status_code, 
            detail={
                "success": False,
                "message": e.message,
                "error_code": e.error_code,
                "details": e.details
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR",
                "details": None
            }
        )
