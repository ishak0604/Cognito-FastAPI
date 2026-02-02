from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth_schemas import UserResponse

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/profile", response_model=UserResponse)
def profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get the profile of the current logged-in user.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.id == current_user["user_id"]).first()

    if not user:
        # Fallback: create user locally if info is present in current_user
        email = current_user.get("email", "")
        role = current_user.get("role", "user")

        user = User(id=current_user["user_id"], email=email, role=role)
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            user = db.query(User).filter(User.id == current_user["user_id"]).first()

    return user
