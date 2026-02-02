from jose import jwt
import requests
from fastapi import HTTPException, Request, Depends, status
from app.core.config import settings
from functools import lru_cache

ISSUER = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"


# 🔁 Auto-refresh JWKS (avoids restart issues)
@lru_cache()
def get_jwks():
    return requests.get(JWKS_URL).json()


def verify_jwt(token: str):
    try:
        jwks = get_jwks()
        headers = jwt.get_unverified_header(token)
        kid = headers["kid"]

        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token key")

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.COGNITO_CLIENT_ID,
            issuer=ISSUER,
        )

        # 🔐 Only allow ACCESS TOKENS
        if payload.get("token_use") != "access":
            raise HTTPException(status_code=401, detail="Use access token")

        return payload

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# 🔐 Extract token (Header OR Cookie)
def get_token_from_request(request: Request):
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth.split(" ")[1]

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    raise HTTPException(status_code=401, detail="Not authenticated")


# 👤 Current User Dependency
def get_current_user(request: Request):
    token = get_token_from_request(request)
    payload = verify_jwt(token)

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("custom:role", "user"),
        "claims": payload,
    }


# 🔐 RBAC Dependency
def require_role(role: str):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user["role"] != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return role_checker
