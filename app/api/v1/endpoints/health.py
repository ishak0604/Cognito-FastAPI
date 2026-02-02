"""Health check endpoints for production monitoring."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from fastapi import HTTPException

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "fastapi-auth"}


@router.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail={
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        })