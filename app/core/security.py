"""Security utilities for Cognito token handling."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.cognito_service import cognito_service
from app.database.models.user import User
from app.database.session import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme for Cognito tokens
cognito_security = HTTPBearer()


def decode_cognito_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate Cognito JWT token."""
    return cognito_service.verify_cognito_token(token)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(cognito_security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from Cognito token."""
    token = credentials.credentials

    # Verify token with Cognito
    token_payload = decode_cognito_token(token)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user identifier from token
    cognito_sub = token_payload.get("sub")
    if not cognito_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find user in database
    user = db.query(User).filter(User.cognito_sub == cognito_sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is expired
    if user.token_expires_at and user.token_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def refresh_expired_token(user: User, db: Session) -> Optional[Dict[str, Any]]:
    """Refresh expired Cognito token for user."""
    if not user.cognito_refresh_token:
        logger.warning(f"No refresh token available for user {user.id}")
        return None

    try:
        # Attempt to refresh token
        refresh_result = cognito_service.refresh_cognito_token(user.cognito_refresh_token)
        if not refresh_result:
            logger.error(f"Token refresh failed for user {user.id}")
            return None

        # Update user with new tokens
        user.cognito_id_token = refresh_result.get("id_token")
        user.token_expires_at = datetime.utcnow() + timedelta(seconds=refresh_result["expires_in"])
        db.commit()

        logger.info(f"Token refreshed successfully for user {user.id}")
        return refresh_result

    except Exception as e:
        logger.error(f"Error refreshing token for user {user.id}: {e}")
        db.rollback()
        return None


def handle_token_errors(func):
    """Decorator to handle common token errors gracefully."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in token handling: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service temporarily unavailable",
            )
    return wrapper


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None
