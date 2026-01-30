"""AWS Cognito authentication endpoints (hosted UI integration)."""

import logging
from typing import Optional
from fastapi import APIRouter, Query, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.services.cognito_service import cognito_service
from app.core.auth_dependencies import get_current_user
from app.database import get_db  # adjust import to match your project
# If you return DB user in callback, import your User model:
# from app.database.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Cognito Auth"])

@router.get("/login")
def get_login_url(redirect_uri: str = Query("http://localhost:8000/api/v1/auth/callback", description="Redirect URI after login")):
    """
    Return Cognito hosted UI login URL so frontend can redirect user there.
    """
    try:
        login_url = cognito_service.get_cognito_login_url(redirect_uri)
        return {"login_url": login_url}
    except Exception as e:
        logger.error("Failed to generate login URL: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate login URL")

@router.get("/callback")
def cognito_callback(
    code: str = Query(..., description="Authorization code from Cognito"),
    redirect_uri: Optional[str] = Query(None, description="Redirect URI used in login"),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth2 callback from Cognito:
    - Exchange code for tokens
    - Retrieve userinfo
    - Sync user to DB
    - Return tokens/user to caller (or redirect as needed)
    """
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization code is required")
    if not redirect_uri:
        # ensure redirect_uri matches what you used when asking for login
        redirect_uri = "http://localhost:8000/api/v1/auth/callback"

    try:
        token_response = cognito_service.exchange_code_for_tokens(code, redirect_uri)
        access_token = token_response.get("access_token")
        id_token = token_response.get("id_token")
        refresh_token = token_response.get("refresh_token")

        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token exchange failed")

        user_info = cognito_service.get_userinfo(access_token)
        # Sync/create user in DB if needed:
        user = cognito_service.handle_cognito_user_sync(user_info, db)

        # Return tokens and user info (modify as needed for your frontend)
        return {
            "access_token": access_token,
            "id_token": id_token,
            "refresh_token": refresh_token,
            "expires_in": token_response.get("expires_in"),
            "token_type": token_response.get("token_type"),
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Cognito callback failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cognito callback failed")

@router.get("/profile")
def profile(current_user = Depends(get_current_user)):
    """
    Example protected endpoint that returns claims from Cognito token.
    """
    return {"user": current_user}