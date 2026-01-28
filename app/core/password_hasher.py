import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using Argon2 algorithm."""
    try:
        hashed = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        raise

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hashed password."""
    try:
        is_valid = pwd_context.verify(password, hashed)
        if is_valid:
            logger.debug("Password verification successful")
        else:
            logger.warning("Password verification failed")
        return is_valid
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        raise
