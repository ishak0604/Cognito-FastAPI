"""AWS Cognito authentication endpoints."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.cognito_service import cognito_service
from app.core.security import get_current_user, get_current_user_optional
from app.database.models.user import User
from app.schemas.auth_schemas import (
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    AuthStatusResponse,
    LoginUrlResponse,
    CognitoCallbackResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Cognito Auth"])


@router.get(
    "/login",
    response_model=LoginUrlResponse,
    summary="Get Cognito Login URL",
    description="Returns the Cognito hosted UI login URL for user authentication"
)
def get_login_url(redirect_uri: str = Query("http://localhost:8000/api/v1/auth/callback", description="Redirect URI after login")):
    """Get the Cognito login URL for redirecting users to AWS Cognito hosted UI."""
    try:
        login_url = cognito_service.get_cognito_login_url(redirect_uri)
        return LoginUrlResponse(
            login_url=login_url,
            message="Redirect user to this URL for authentication"
        )
    except Exception as e:
        logger.error(f"Error generating login URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate login URL"
        )


@router.get(
    "/callback",
    response_model=CognitoCallbackResponse,
    summary="Cognito OAuth Callback",
    description="Handle the callback from Cognito after user authentication"
)
def cognito_callback(
    code: str = Query(..., description="Authorization code from Cognito"),
    state: Optional[str] = Query(None, description="State parameter"),
    error: Optional[str] = Query(None, description="Error from Cognito"),
    db: Session = Depends(get_db)
):
    """Handle the OAuth callback from Cognito and exchange code for tokens."""
    if error:
        logger.warning(f"Cognito authentication error: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {error}"
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is required"
        )

    try:
        # Exchange authorization code for tokens
        token_response = cognito_service.exchange_code_for_tokens(code)

        if not token_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for tokens"
            )

        # Sync user with database
        user = cognito_service.handle_cognito_user_sync(token_response["user_info"], db)

        # Update user with token information
        user.cognito_id_token = token_response.get("id_token")
        user.cognito_refresh_token = token_response.get("refresh_token")
        user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_response["expires_in"])
        db.commit()

        logger.info(f"User {user.email} authenticated successfully via Cognito")

        return CognitoCallbackResponse(
            access_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token"),
            token_type=token_response["token_type"],
            expires_in=token_response["expires_in"],
            user={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_verified": user.is_verified
            }
        )

    except Exception as e:
        logger.error(f"Error processing Cognito callback: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process authentication callback"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Access Token",
    description="Refresh an expired access token using the refresh token"
)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    if not request.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required"
        )

    try:
        # Attempt to refresh token
        refresh_result = cognito_service.refresh_cognito_token(request.refresh_token)

        if not refresh_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # Find user by refresh token and update
        user = db.query(User).filter(User.cognito_refresh_token == request.refresh_token).first()
        if user:
            user.token_expires_at = datetime.utcnow() + timedelta(seconds=refresh_result["expires_in"])
            db.commit()

        return TokenResponse(**refresh_result)

    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        )


@router.post(
    "/logout",
    summary="Logout User",
    description="Revoke the user's access token and clear session"
)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user by revoking their tokens."""
    try:
        # Revoke token with Cognito
        if current_user.cognito_id_token:
            cognito_service.revoke_cognito_token(current_user.cognito_id_token)

        # Clear tokens from database
        current_user.cognito_id_token = None
        current_user.cognito_refresh_token = None
        current_user.token_expires_at = None
        db.commit()

        logger.info(f"User {current_user.email} logged out successfully")

        return {
            "success": True,
            "message": "Logged out successfully"
        }

    except Exception as e:
        logger.error(f"Error during logout: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="Get information about the currently authenticated user"
)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_verified=current_user.is_verified,
        authentication_method=current_user.authentication_method,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.get(
    "/auth-status",
    response_model=AuthStatusResponse,
    summary="Check Authentication Status",
    description="Check if the current request is authenticated"
)
def check_auth_status(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Check authentication status."""
    if current_user:
        return AuthStatusResponse(
            is_authenticated=True,
            user=UserResponse(
                id=current_user.id,
                email=current_user.email,
                first_name=current_user.first_name,
                last_name=current_user.last_name,
                is_verified=current_user.is_verified,
                authentication_method=current_user.authentication_method,
                created_at=current_user.created_at,
                updated_at=current_user.updated_at
            )
        )
    else:
        return AuthStatusResponse(is_authenticated=False, user=None)
