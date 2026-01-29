"""User authentication service with improved structure."""

import logging
from datetime import timedelta
from typing import Dict, Any

from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.database.models import User
from app.core.password_hasher import hash_password, verify_password
from app.core.jwt_handler import create_access_token
from app.core.config import settings
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
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class UserAuthService(BaseService):
    """User authentication service with improved structure."""
    
    def signup_user(self, email: str, password: str) -> Dict[str, Any]:
        """Create a new user account with email verification.
        
        Args:
            email: User email
            password: User password (will be hashed)
        
        Returns:
            Dictionary with success status and message
        
        Raises:
            EmailAlreadyExists: If email already exists and is verified
        """
        try:
            self.logger.info(f"Attempting signup for email: {email}")
            
            existing_user = self._get_user_by_email(email)
            
            if existing_user:
                return self._handle_existing_user(existing_user, password)
            
            return self._create_new_user(email, password)
            
        except EmailAlreadyExists:
            self.logger.error(f"EmailAlreadyExists exception for: {email}")
            raise
        except SQLAlchemyError as e:
            self.handle_database_error("signup", email, e)
        except Exception as e:
            self.handle_unexpected_error("signup", email, e)
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return JWT access token.
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Dictionary with success status, message, and JWT token
        
        Raises:
            InvalidCredentials: If email or password is incorrect
            EmailNotVerified: If email is not verified
        """
        try:
            self.logger.info(f"Login attempt for email: {email}")
            
            user = self._get_user_by_email(email)
            if not user:
                self.logger.warning(f"Login failed: User not found - {email}")
                raise InvalidCredentials(field="email")
            
            self._verify_password(password, user.password_hash, email)
            self._check_email_verified(user)
            
            access_token = self._create_access_token(user.email)
            
            self.logger.info(f"Login successful for: {email}")
            return self._create_login_response(access_token, user)
            
        except (InvalidCredentials, EmailNotVerified):
            self.logger.error(f"Authentication exception for: {email}")
            raise
        except SQLAlchemyError as e:
            self.handle_database_error("login", email, e)
        except Exception as e:
            self.handle_unexpected_error("login", email, e)
    
    def confirm_signup(self, token: str) -> Dict[str, Any]:
        """Verify user email using verification token.
        
        Args:
            token: Email verification token
        
        Returns:
            Dictionary with success status and message
        
        Raises:
            InvalidToken: If token is invalid or expired
        """
        try:
            self.logger.info(f"Attempting email verification with token: {token[:10]}...")
            
            user = self._get_user_by_verification_token(token)
            self._validate_verification_token(user, token)
            
            user.is_verified = True
            user.verification_token = None
            self.commit_or_rollback("email verification")
            
            self.logger.info(f"Email verified successfully for: {user.email}")
            return self.create_success_response(
                "Email verified successfully",
                {"email": user.email}
            )
            
        except InvalidToken:
            self.logger.error(f"InvalidToken exception during email verification for token {token[:10]}...")
            raise
        except SQLAlchemyError as e:
            self.handle_database_error("email verification", "unknown", e)
        except Exception as e:
            self.handle_unexpected_error("email verification", "unknown", e)
    
    def forgot_password(self, email: str) -> Dict[str, Any]:
        """Generate password reset token for user.
        
        Args:
            email: User email
        
        Returns:
            Dictionary with success status and message
        
        Raises:
            InvalidCredentials: If email not found
        """
        try:
            self.logger.info(f"Password reset requested for email: {email}")
            
            user = self._get_user_by_email(email)
            if not user:
                self.logger.warning(f"Password reset failed: User not found - {email}")
                raise InvalidCredentials(field="email")
            
            reset_token = generate_reset_token()
            reset_token_expires_at = get_token_expiry(hours=1)
            
            user.reset_token = reset_token
            user.reset_token_expires_at = reset_token_expires_at
            self.commit_or_rollback("password reset request")
            
            self.logger.info(f"Password reset token generated for: {email}")
            return self.create_success_response(
                "Password reset link sent to email",
                {
                    "reset_token": reset_token,
                    "expires_in_hours": 1
                }
            )
            
        except InvalidCredentials:
            self.logger.error(f"InvalidCredentials exception for: {email}")
            raise
        except SQLAlchemyError as e:
            self.handle_database_error("password reset request", email, e)
        except Exception as e:
            self.handle_unexpected_error("password reset request", email, e)
    
    def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Reset user password using reset token.
        
        Args:
            token: Password reset token
            new_password: New password
        
        Returns:
            Dictionary with success status and message
        
        Raises:
            InvalidToken: If token is invalid or expired
        """
        try:
            self.logger.info("Password reset attempt with token")
            
            user = self._get_user_by_reset_token(token)
            self._validate_reset_token(user, token)
            
            user.password_hash = hash_password(new_password)
            user.reset_token = None
            user.reset_token_expires_at = None
            self.commit_or_rollback("password reset")
            
            self.logger.info(f"Password reset successful for: {user.email}")
            return self.create_success_response(
                "Password reset successful",
                {"email": user.email}
            )
            
        except InvalidToken:
            self.logger.error("InvalidToken exception during password reset")
            raise
        except SQLAlchemyError as e:
            self.handle_database_error("password reset", "unknown", e)
        except Exception as e:
            self.handle_unexpected_error("password reset", "unknown", e)
    
    # Private helper methods
    def _get_user_by_email(self, email: str) -> User:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def _get_user_by_verification_token(self, token: str) -> User:
        """Get user by verification token."""
        return self.db.query(User).filter(User.verification_token == token).first()
    
    def _get_user_by_reset_token(self, token: str) -> User:
        """Get user by reset token."""
        return self.db.query(User).filter(User.reset_token == token).first()
    
    def _handle_existing_user(self, user: User, password: str) -> Dict[str, Any]:
        """Handle existing user during signup."""
        if user.is_verified:
            self.logger.warning(f"Signup failed: Email already exists and verified - {user.email}")
            raise EmailAlreadyExists()
        
        # User exists but not verified - generate new token
        self.logger.info(f"User exists but not verified, generating new token for: {user.email}")
        verification_token = generate_verification_token()
        user.verification_token = verification_token
        user.password_hash = hash_password(password)
        self.commit_or_rollback("existing user token regeneration")
        
        return self.create_success_response(
            "New verification token generated. Please verify your email.",
            {
                "email": user.email,
                "verification_token": verification_token
            }
        )
    
    def _create_new_user(self, email: str, password: str) -> Dict[str, Any]:
        """Create new user account."""
        verification_token = generate_verification_token()
        
        user = User(
            email=email,
            password_hash=hash_password(password),
            verification_token=verification_token,
            is_verified=False
        )
        self.db.add(user)
        self.commit_or_rollback("user creation")
        
        self.logger.info(f"User signup successful: {email}")
        return self.create_success_response(
            "Signup successful. Please verify your email.",
            {
                "email": user.email,
                "verification_token": verification_token
            }
        )
    
    def resend_verification(self, email: str) -> Dict[str, Any]:
        """Resend verification email for user.
        
        Args:
            email: User email
        
        Returns:
            Dictionary with success status and message
        
        Raises:
            InvalidCredentials: If email not found or already verified
        """
        try:
            self.logger.info(f"Resend verification requested for email: {email}")
            
            user = self._get_user_by_email(email)
            if not user:
                self.logger.warning(f"Resend verification failed: User not found - {email}")
                raise InvalidCredentials(field="email")
            
            if user.is_verified:
                self.logger.warning(f"Resend verification failed: User already verified - {email}")
                raise InvalidCredentials(field="email", message="Email already verified")
            
            # Generate new verification token
            verification_token = generate_verification_token()
            user.verification_token = verification_token
            self.commit_or_rollback("resend verification")
            
            self.logger.info(f"Verification token resent for: {email}")
            return self.create_success_response(
                "Verification email sent. Please check your inbox.",
                {
                    "email": user.email,
                    "verification_token": verification_token
                }
            )
            
        except InvalidCredentials:
            self.logger.error(f"InvalidCredentials exception for: {email}")
            raise
        except SQLAlchemyError as e:
            self.handle_database_error("resend verification", email, e)
        except Exception as e:
            self.handle_unexpected_error("resend verification", email, e)
    
    def _verify_password(self, password: str, password_hash: str, email: str) -> None:
        """Verify user password."""
        if not verify_password(password, password_hash):
            self.logger.warning(f"Login failed: Invalid password for - {email}")
            raise InvalidCredentials(field="password")
    
    def _check_email_verified(self, user: User) -> None:
        """Check if user email is verified."""
        if not user.is_verified:
            self.logger.warning(f"Login failed: Email not verified - {user.email}")
            raise EmailNotVerified()
    
    def _create_access_token(self, email: str) -> str:
        """Create JWT access token."""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(
            data={"sub": email}, 
            expires_delta=access_token_expires
        )
    
    def _create_login_response(self, access_token: str, user: User) -> Dict[str, Any]:
        """Create login response."""
        return self.create_success_response(
            "Login successful",
            {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "email": user.email,
                    "is_verified": user.is_verified
                }
            }
        )
    
    def _validate_verification_token(self, user: User, token: str) -> None:
        """Validate verification token."""
        if not user:
            self.logger.warning(f"Email verification failed: No user found with token {token[:10]}...")
            raise InvalidToken(token_type="verification token")
        
        if user.is_verified:
            self.logger.warning(f"Email verification failed: User {user.email} already verified")
            raise InvalidToken(token_type="verification token")
    
    def _validate_reset_token(self, user: User, token: str) -> None:
        """Validate reset token."""
        if not user:
            self.logger.warning("Password reset failed: Invalid reset token")
            raise InvalidToken(token_type="reset token")
        
        if is_token_expired(user.reset_token_expires_at):
            user.reset_token = None
            user.reset_token_expires_at = None
            self.db.commit()
            self.logger.warning(f"Password reset failed: Token expired for {user.email}")
            raise InvalidToken(token_type="reset token")


# Factory function for dependency injection
def get_user_auth_service(db: Session = Depends(get_db)) -> UserAuthService:
    """Get user authentication service instance."""
    return UserAuthService(db)


# Legacy functions for backward compatibility
def signup_user(db: Session, email: str, password: str) -> Dict[str, Any]:
    """Legacy signup function."""
    service = UserAuthService(db)
    return service.signup_user(email, password)


def login_user(db: Session, email: str, password: str) -> Dict[str, Any]:
    """Legacy login function."""
    service = UserAuthService(db)
    return service.login_user(email, password)


def confirm_signup(db: Session, token: str) -> Dict[str, Any]:
    """Legacy confirm signup function."""
    service = UserAuthService(db)
    return service.confirm_signup(token)


def forgot_password(db: Session, email: str) -> Dict[str, Any]:
    """Legacy forgot password function."""
    service = UserAuthService(db)
    return service.forgot_password(email)


def reset_password(db: Session, token: str, new_password: str) -> Dict[str, Any]:
    """Legacy reset password function."""
    service = UserAuthService(db)
    return service.reset_password(token, new_password)


def resend_verification(db: Session, email: str) -> Dict[str, Any]:
    """Legacy resend verification function."""
    service = UserAuthService(db)
    return service.resend_verification(email)