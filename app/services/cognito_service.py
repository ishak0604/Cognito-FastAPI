"""AWS Cognito service for authentication and user management."""

import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
from jwt import PyJWKClient

from app.core.config import settings, get_cognito_jwks
from app.database.models.user import User
from app.database.session import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CognitoService:
    """AWS Cognito service for authentication"""

    def __init__(self):
        self.user_pool_id = settings.COGNITO_USER_POOL_ID
        self.client_id = settings.COGNITO_CLIENT_ID
        self.client_secret = settings.COGNITO_CLIENT_SECRET
        self.region = settings.COGNITO_REGION
        self.domain = settings.COGNITO_DOMAIN
        self.jwks_url = get_cognito_jwks()

        # Initialize JWKS client for token verification
        self.jwks_client = PyJWKClient(self.jwks_url)

    def verify_cognito_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token from Cognito and return decoded payload."""
        try:
            # Get the signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Decode and verify the token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
            )

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None

    def get_user_info_from_cognito(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Cognito ID token."""
        payload = self.verify_cognito_token(token)
        if not payload:
            return None

        return {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "email_verified": payload.get("email_verified", False),
            "given_name": payload.get("given_name"),
            "family_name": payload.get("family_name"),
            "preferred_username": payload.get("preferred_username"),
            "cognito_username": payload.get("cognito:username")
        }

    def get_cognito_login_url(self, redirect_uri: str = "http://localhost:8000/api/v1/auth/callback") -> str:
        """Return Cognito login page URL."""
        return (
            f"{self.domain}/oauth2/authorize?"
            f"client_id={self.client_id}&"
            f"response_type=code&"
            f"scope=openid+email+profile&"
            f"redirect_uri={redirect_uri}"
        )

    def exchange_code_for_tokens(self, code: str, redirect_uri: str = "http://localhost:8000/api/v1/auth/callback") -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access, ID, and refresh tokens."""
        try:
            token_url = f"{self.domain}/oauth2/token"

            data = {
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": redirect_uri
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }

            response = requests.post(token_url, data=data, headers=headers)
            response.raise_for_status()

            tokens = response.json()

            # Decode ID token to get user info
            id_token_payload = self.verify_cognito_token(tokens["id_token"])
            if not id_token_payload:
                return None

            return {
                "access_token": tokens["access_token"],
                "id_token": tokens["id_token"],
                "refresh_token": tokens.get("refresh_token"),
                "token_type": tokens["token_type"],
                "expires_in": tokens["expires_in"],
                "user_info": {
                    "sub": id_token_payload.get("sub"),
                    "email": id_token_payload.get("email"),
                    "email_verified": id_token_payload.get("email_verified", False),
                    "given_name": id_token_payload.get("given_name"),
                    "family_name": id_token_payload.get("family_name"),
                    "preferred_username": id_token_payload.get("preferred_username"),
                    "cognito_username": id_token_payload.get("cognito:username")
                }
            }

        except requests.RequestException as e:
            logger.error(f"Token exchange failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {e}")
            return None

    def refresh_cognito_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token."""
        try:
            token_url = f"{self.domain}/oauth2/token"

            data = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }

            response = requests.post(token_url, data=data, headers=headers)
            response.raise_for_status()

            tokens = response.json()

            return {
                "access_token": tokens["access_token"],
                "id_token": tokens.get("id_token"),
                "token_type": tokens["token_type"],
                "expires_in": tokens["expires_in"]
            }

        except requests.RequestException as e:
            logger.error(f"Token refresh failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            return None

    def revoke_cognito_token(self, token: str) -> bool:
        """Revoke access token."""
        try:
            revoke_url = f"{self.domain}/oauth2/revoke"

            data = {
                "token": token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }

            response = requests.post(revoke_url, data=data, headers=headers)
            response.raise_for_status()

            logger.info("Token revoked successfully")
            return True

        except requests.RequestException as e:
            logger.error(f"Token revocation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during token revocation: {e}")
            return False

    def handle_cognito_user_sync(self, cognito_user: Dict[str, Any], db: Session) -> User:
        """Create or update local user record from Cognito user info."""
        try:
            # Check if user exists by cognito_sub
            user = db.query(User).filter(User.cognito_sub == cognito_user["sub"]).first()

            if user:
                # Update existing user
                user.email = cognito_user["email"]
                user.is_verified = cognito_user.get("email_verified", False)
                user.first_name = cognito_user.get("given_name")
                user.last_name = cognito_user.get("family_name")
                user.cognito_email_verified = cognito_user.get("email_verified", False)
                user.updated_at = datetime.utcnow()
            else:
                # Create new user
                user = User(
                    cognito_sub=cognito_user["sub"],
                    email=cognito_user["email"],
                    first_name=cognito_user.get("given_name"),
                    last_name=cognito_user.get("family_name"),
                    is_verified=cognito_user.get("email_verified", False),
                    cognito_email_verified=cognito_user.get("email_verified", False),
                    authentication_method="cognito",
                    password_hash=None,  # No password for Cognito users
                    verification_token=None,  # Already verified by Cognito
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(user)

            db.commit()
            db.refresh(user)

            logger.info(f"User synced successfully: {user.email}")
            return user

        except Exception as e:
            db.rollback()
            logger.error(f"User sync failed: {e}")
            raise


# Global instance
cognito_service = CognitoService()
