from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.schemas.auth_schemas import UserResponse

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.get("/profile", response_model=UserResponse)
def profile(current_user=Depends(get_current_user)):
    """
    Get currently logged-in user's profile
    """
    return current_user
