import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


def generate_verification_token() -> str:
    """
    Generate a secure random token for email verification.
    
    Returns:
        A URL-safe token string
    """
    try:
        token = secrets.token_urlsafe(32)
        logger.debug("Verification token generated successfully")
        return token
    except Exception as e:
        logger.error(f"Error generating verification token: {str(e)}")
        raise


def generate_reset_token() -> str:
    """
    Generate a secure random token for password reset.
    
    Returns:
        A URL-safe token string
    """
    try:
        token = secrets.token_urlsafe(32)
        logger.debug("Reset token generated successfully")
        return token
    except Exception as e:
        logger.error(f"Error generating reset token: {str(e)}")
        raise


def get_token_expiry(hours: int = 24) -> datetime:
    """
    Get token expiry time.
    
    Args:
        hours: Number of hours until token expires (default: 24)
    
    Returns:
        datetime object representing token expiry time
    """
    return datetime.utcnow() + timedelta(hours=hours)


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
    return datetime.utcnow() > expiry_time
