"""Token refresh endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Body
from datetime import timedelta
from app.core.jwt_handler import verify_token, create_access_token
from app.core.config import settings
from app.schemas.auth_schemas import SuccessResponse, ErrorResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/refresh-token", response_model=SuccessResponse, responses={
    200: {"model": SuccessResponse, "description": "Token refreshed successfully"},
    401: {"model": ErrorResponse, "description": "Invalid or expired token"},
    500: {"model": ErrorResponse, "description": "Internal server error"}
})
def refresh_token(token: str = Body(..., embed=True)):
    """Refresh JWT access token."""
    try:
        # Verify the provided token
        payload = verify_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail={
                "success": False,
                "message": "Invalid or expired token",
                "error_code": "INVALID_TOKEN",
                "details": None
            })
        
        # Extract email from token
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail={
                "success": False,
                "message": "Invalid token payload",
                "error_code": "INVALID_TOKEN",
                "details": None
            })
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "data": {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        }
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": "An unexpected error occurred",
            "error_code": "INTERNAL_ERROR",
            "details": None
        })
