from jose import jwt
from jose.utils import base64url_decode
import requests
from fastapi import HTTPException, Request, status
from app.core.config import settings

JWKS_URL = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
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

    except Exception:
        raise HTTPException(401, "Invalid or expired token")


def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Not authenticated")

    payload = verify_jwt(token)

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "claims": payload,
    }
