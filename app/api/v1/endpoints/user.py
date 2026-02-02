from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/profile")
def profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()

    if not user:
        user = User(
            id=current_user["user_id"],
            email=current_user["email"],
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
