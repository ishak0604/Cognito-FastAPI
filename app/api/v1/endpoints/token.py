"""Placeholder token-related endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/refresh-token")
def refresh_token():
    return {"success": True, "message": "Refresh token endpoint placeholder", "data": None}
