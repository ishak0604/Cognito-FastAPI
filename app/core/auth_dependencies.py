"""Authentication dependencies for protected routes."""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.database.models.user import User
from app.core.jwt_handler import verify_token, TokenExpiredError, TokenInvalidError

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthError:
    """Standard authentication error responses."""
    
    INVALID_TOKEN = {
        "success": False,
        "message": "Could not validate credentials",
        "error_code": "INVALID_TOKEN",
        "details": None
    }
    
    TOKEN_EXPIRED = {
        "success": False,
        "message": "Token has expired",
        "error_code": "TOKEN_EXPIRED",
        "details": None
    }
    
    EMAIL_NOT_VERIFIED = {
        "success": False,
        "message": "Email not verified",
        "error_code": "EMAIL_NOT_VERIFIED",
        "details": None
    }
    
    USER_NOT_FOUND = {
        "success": False,
        "message": "User not found",
        "error_code": "USER_NOT_FOUND",
        "details": None
    }


def extract_user_email(credentials: HTTPAuthorizationCredentials) -> str:
    """Extract and validate user email from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User email from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = verify_token(credentials.credentials)
        email = payload.get("sub")
        
        if not email:
            logger.warning("Token missing subject (email)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=AuthError.INVALID_TOKEN,
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return email
        
    except TokenExpiredError:
        logger.warning("Expired token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AuthError.TOKEN_EXPIRED,
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    except TokenInvalidError:
        logger.warning("Invalid token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AuthError.INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_user_by_email(db: Session, email: str) -> User:
    """Get user from database by email.
    
    Args:
        db: Database session
        email: User email
        
    Returns:
        User object
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        logger.warning(f"User not found for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AuthError.USER_NOT_FOUND,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


def validate_user_verified(user: User) -> None:
    """Validate that user email is verified.
    
    Args:
        user: User object
        
    Raises:
        HTTPException: If email not verified
    """
    if not user.is_verified:
        logger.warning(f"Unverified user attempted access: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=AuthError.EMAIL_NOT_VERIFIED
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        Authenticated user object
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Extract email from token
        email = extract_user_email(credentials)
        
        # Get user from database
        user = get_user_by_email(db, email)
        
        # Validate user is verified
        validate_user_verified(user)
        
        logger.debug(f"User authenticated successfully: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AuthError.INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if token provided, otherwise return None.
    
    Args:
        credentials: Optional HTTP authorization credentials
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None