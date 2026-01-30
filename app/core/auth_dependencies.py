from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from app.auth import verify_cognito_jwt

bearer = HTTPBearer(auto_error=False)

def get_current_user(token = Depends(bearer)):
    """
    FastAPI dependency that returns Cognito claims for an authenticated user.
    Raises 401 for missing or invalid tokens.
    """
    if not token or not token.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    claims = verify_cognito_jwt(token.credentials)
    if not claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return claims