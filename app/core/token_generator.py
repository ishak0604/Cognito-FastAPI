import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def generate_verification_token() -> str:
    """
    Generate a secure random token for email verification.
    
    Returns:
        A URL-safe token string
    
    Raises:
        RuntimeError: If token generation fails
    """
    try:
        logger.info("Generating verification token")
        token = secrets.token_urlsafe(32)
        logger.info("Verification token generated successfully")
        return token
    except Exception as e:
        logger.error(f"Failed to generate verification token: {str(e)}")
        raise RuntimeError("Token generation failed") from e


def generate_reset_token() -> str:
    """
    Generate a secure random token for password reset.
    
    Returns:
        A URL-safe token string
    
    Raises:
        RuntimeError: If token generation fails
    """
    try:
        logger.info("Generating reset token")
        token = secrets.token_urlsafe(32)
        logger.info("Reset token generated successfully")
        return token
    except Exception as e:
        logger.error(f"Failed to generate reset token: {str(e)}")
        raise RuntimeError("Token generation failed") from e


def get_token_expiry(hours: int = 24) -> datetime:
    """
    Get token expiry time.
    
    Args:
        hours: Number of hours until token expires (default: 24)
    
    Returns:
        datetime object representing token expiry time
    """
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def is_token_expired(expiry_time: Optional[datetime]) -> bool:
    """
    Check if token is expired.
    
    Args:
        expiry_time: datetime object representing token expiry time
    
    Returns:
        True if token is expired, False otherwise
    """
    if not expiry_time:
        return True
    current_time = datetime.now(timezone.utc)
    if expiry_time.tzinfo is None:
        expiry_time = expiry_time.replace(tzinfo=timezone.utc)
    return current_time > expiry_time
