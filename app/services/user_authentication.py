import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database.models import User
from app.core.password_hasher import hash_password, verify_password
from app.exceptions import (
    EmailAlreadyExists,
    InvalidCredentials,
    EmailNotVerified,
    InvalidToken
)
from app.core.token_generator import (
    generate_verification_token,
    generate_reset_token,
    get_token_expiry,
    is_token_expired
)

logger = logging.getLogger(__name__)


def signup_user(db: Session, email: str, password: str) -> dict:
    """
    Create a new user account with email verification.
    
    Args:
        db: Database session
        email: User email
        password: User password (will be hashed)
    
    Returns:
        Dictionary with success status and message
    
    Raises:
        EmailAlreadyExists: If email already exists
    """
    try:
        logger.info(f"Attempting signup for email: {email}")
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            logger.warning(f"Signup failed: Email already exists - {email}")
            raise EmailAlreadyExists()

        # Generate verification token
        verification_token = generate_verification_token()
        
        # Create new user
        user = User(
            email=email,
            password_hash=hash_password(password),
            verification_token=verification_token,
            is_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User signup successful: {email}")

        return {
            "success": True,
            "message": "Signup successful. Please verify your email.",
            "data": {
                "email": user.email,
                "verification_token": verification_token
            }
        }
    except EmailAlreadyExists:
        db.rollback()
        logger.error(f"EmailAlreadyExists exception for: {email}")
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during signup for {email}: {str(e)}")
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during signup for {email}: {str(e)}")
        raise


def confirm_signup(db: Session, token: str) -> dict:
    """
    Verify user email using verification token.
    
    Args:
        db: Database session
        token: Email verification token
    
    Returns:
        Dictionary with success status and message
    
    Raises:
        InvalidToken: If token is invalid or expired
    """
    try:
        logger.info("Attempting email verification with token")
        
        # Find user by verification token
        user = db.query(User).filter(User.verification_token == token).first()
        if not user:
            logger.warning("Email verification failed: Invalid token")
            raise InvalidToken(token_type="verification token")

        # Mark email as verified
        user.is_verified = True
        user.verification_token = None
        db.commit()
        db.refresh(user)
        
        logger.info(f"Email verified successfully for: {user.email}")

        return {
            "success": True,
            "message": "Email verified successfully",
            "data": {"email": user.email}
        }
    except InvalidToken:
        db.rollback()
        logger.error("InvalidToken exception during email verification")
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during email verification: {str(e)}")
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during email verification: {str(e)}")
        raise


def login_user(db: Session, email: str, password: str) -> dict:
    """
    Authenticate user and return login status.
    
    Args:
        db: Database session
        email: User email
        password: User password
    
    Returns:
        Dictionary with success status and message
    
    Raises:
        InvalidCredentials: If email or password is incorrect
        EmailNotVerified: If email is not verified
    """
    try:
        logger.info(f"Login attempt for email: {email}")
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"Login failed: User not found - {email}")
            raise InvalidCredentials(field="email")

        # Verify password
        if not verify_password(password, user.password_hash):
            logger.warning(f"Login failed: Invalid password for - {email}")
            raise InvalidCredentials(field="password")

        # Check if email is verified
        if not user.is_verified:
            logger.warning(f"Login failed: Email not verified - {email}")
            raise EmailNotVerified()
        
        logger.info(f"Login successful for: {email}")

        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "email": user.email,
                "is_verified": user.is_verified
            }
        }
    except (InvalidCredentials, EmailNotVerified):
        logger.error(f"Authentication exception for: {email}")
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error during login for {email}: {str(e)}")
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during login for {email}: {str(e)}")
        raise


def forgot_password(db: Session, email: str) -> dict:
    """
    Generate password reset token for user.
    
    Args:
        db: Database session
        email: User email
    
    Returns:
        Dictionary with success status and message
    
    Raises:
        InvalidCredentials: If email not found
    """
    try:
        logger.info(f"Password reset requested for email: {email}")
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"Password reset failed: User not found - {email}")
            raise InvalidCredentials(field="email")

        # Generate reset token (valid for 1 hour)
        reset_token = generate_reset_token()
        reset_token_expires_at = get_token_expiry(hours=1)
        
        user.reset_token = reset_token
        user.reset_token_expires_at = reset_token_expires_at
        db.commit()
        db.refresh(user)
        
        logger.info(f"Password reset token generated for: {email}")

        return {
            "success": True,
            "message": "Password reset link sent to email",
            "data": {
                "reset_token": reset_token,
                "expires_in_hours": 1
            }
        }
    except InvalidCredentials:
        db.rollback()
        logger.error(f"InvalidCredentials exception for: {email}")
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during password reset request for {email}: {str(e)}")
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during password reset request for {email}: {str(e)}")
        raise


def reset_password(db: Session, token: str, new_password: str) -> dict:
    """
    Reset user password using reset token.
    
    Args:
        db: Database session
        token: Password reset token
        new_password: New password
    
    Returns:
        Dictionary with success status and message
    
    Raises:
        InvalidToken: If token is invalid or expired
    """
    try:
        logger.info("Password reset attempt with token")
        
        # Find user by reset token
        user = db.query(User).filter(User.reset_token == token).first()
        if not user:
            logger.warning("Password reset failed: Invalid reset token")
            raise InvalidToken(token_type="reset token")

        # Check if token is expired
        if is_token_expired(user.reset_token_expires_at):
            user.reset_token = None
            user.reset_token_expires_at = None
            db.commit()
            logger.warning(f"Password reset failed: Token expired for {user.email}")
            raise InvalidToken(token_type="reset token")

        # Update password
        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires_at = None
        db.commit()
        db.refresh(user)
        
        logger.info(f"Password reset successful for: {user.email}")

        return {
            "success": True,
            "message": "Password reset successful",
            "data": {"email": user.email}
        }
    except InvalidToken:
        db.rollback()
        logger.error("InvalidToken exception during password reset")
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during password reset: {str(e)}")
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during password reset: {str(e)}")
        raise
