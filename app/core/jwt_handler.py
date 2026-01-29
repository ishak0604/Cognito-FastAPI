"""JWT token handling utilities with improved error handling."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenError(Exception):
    """Base exception for token-related errors."""
    pass


class TokenExpiredError(TokenError):
    """Raised when token has expired."""
    pass


class TokenInvalidError(TokenError):
    """Raised when token is invalid."""
    pass


def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token with proper timezone handling.
    
    Args:
        data: Payload data to encode in token
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT token string
        
    Raises:
        TokenError: If token creation fails
    """
    try:
        to_encode = data.copy()
        
        # Use timezone-aware datetime
        now = datetime.now(timezone.utc)
        
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": now,  # Issued at
            "type": "access_token"
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        
        logger.debug(f"Access token created for subject: {data.get('sub', 'unknown')}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Failed to create access token: {e}")
        raise TokenError(f"Token creation failed: {e}") from e


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token with detailed error handling.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Decoded token payload or None if invalid
        
    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Validate token type
        if payload.get("type") != "access_token":
            logger.warning("Invalid token type")
            raise TokenInvalidError("Invalid token type")
        
        logger.debug(f"Token verified for subject: {payload.get('sub', 'unknown')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise TokenExpiredError("Token has expired")
        
    except jwt.JWTClaimsError as e:
        logger.warning(f"Token claims error: {e}")
        raise TokenInvalidError(f"Invalid token claims: {e}")
        
    except jwt.JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise TokenInvalidError(f"Invalid token: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        raise TokenInvalidError(f"Token verification failed: {e}")


def decode_token_unsafe(token: str) -> Optional[Dict[str, Any]]:
    """Decode token without verification (for debugging only).
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None
    """
    try:
        return jwt.get_unverified_claims(token)
    except Exception as e:
        logger.debug(f"Failed to decode token: {e}")
        return None