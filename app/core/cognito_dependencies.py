from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from app.services.cognito_service import cognito_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

async def get_current_user_cognito(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current user from Cognito JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User information from Cognito
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not settings.USE_COGNITO:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Cognito authentication is not enabled"
        )
    
    token = credentials.credentials
    
    try:
        # Verify token with Cognito
        user_info = cognito_service.verify_token(token)
        
        if not user_info:
            logger.warning("Invalid token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"User authenticated: {user_info.get('email')}")
        return user_info
        
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_optional_cognito(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    Optional dependency to get current user from Cognito JWT token
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        User information from Cognito or None if not authenticated
    """
    if not settings.USE_COGNITO or not credentials:
        return None
    
    try:
        return await get_current_user_cognito(credentials)
    except HTTPException:
        return None