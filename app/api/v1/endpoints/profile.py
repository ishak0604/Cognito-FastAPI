"""Placeholder profile endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/profile")
def get_profile():
    return {"success": True, "message": "Profile endpoint placeholder", "data": None}
