"""User profile endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from app.core.auth_dependencies import get_current_user
from app.database.models.user import User
from app.schemas.auth_schemas import SuccessResponse, ErrorResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/profile", response_model=SuccessResponse, responses={
    200: {"model": SuccessResponse, "description": "Profile retrieved successfully"},
    401: {"model": ErrorResponse, "description": "Unauthorized - Invalid token"},
    403: {"model": ErrorResponse, "description": "Forbidden - Email not verified"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def get_profile(current_user: User = Depends(get_current_user)):
    """Get authenticated user profile."""
    try:
        return {
            "success": True,
            "message": "Profile retrieved successfully",
            "data": {
                "email": current_user.email,
                "is_verified": current_user.is_verified,
                "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
                "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
            }
        }
    except Exception:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR",
            "details": None
        })
