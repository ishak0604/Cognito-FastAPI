from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.auth_schemas import UserResponse

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/profile", response_model=UserResponse)
def profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()

    if not user:
        user = User(
            id=current_user["user_id"],
            email=current_user["email"],
            role=current_user["role"],  # ← from JWT
        )
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            user = db.query(User).filter(User.id == current_user["user_id"]).first()

    return user
