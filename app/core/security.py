from jose import jwt
import requests
from fastapi import HTTPException, Request, status
from app.core.config import settings

JWKS_URL = (
    f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/"
    f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)
jwks = requests.get(JWKS_URL).json()

def verify_jwt(token: str):
    try:
        headers = jwt.get_unverified_header(token)
        kid = headers["kid"]
        key = next(k for k in jwks["keys"] if k["kid"] == kid)

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.COGNITO_CLIENT_ID,
            issuer=f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}",
        )
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}"
        )

def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = auth_header.split(" ")[1]
    payload = verify_jwt(token)
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "claims": payload,
    }
