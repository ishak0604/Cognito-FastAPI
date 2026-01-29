"""Database session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Optimized engine for production
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,  # Increased for better connection reuse
    pool_size=10,       # Increased for better concurrency
    max_overflow=20,    # Increased overflow
    echo=False,
    connect_args={"connect_timeout": 10}  # Connection timeout
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Better for production
)


def get_db():
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
