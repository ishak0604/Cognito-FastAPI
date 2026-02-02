from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.database import Base   # ✅ corrected import


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # Cognito sub
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
