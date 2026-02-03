import requests
import time
from threading import Lock
from jose import jwt, JWTError
from fastapi import HTTPException, Request, Depends, status
from app.core.config import settings

ISSUER = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"

_jwks_cache = None
_jwks_cache_expiry = 0
_jwks_lock = Lock()
CACHE_TTL = 3600


# ---------------- JWKS FETCH ----------------
def get_jwks():
    global _jwks_cache, _jwks_cache_expiry
    with _jwks_lock:
        if _jwks_cache and time.time() < _jwks_cache_expiry:
            return _jwks_cache

        response = requests.get(JWKS_URL, timeout=5)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_cache_expiry = time.time() + CACHE_TTL
        return _jwks_cache


# ---------------- JWT VERIFY ----------------
def verify_jwt(token: str):
    try:
        jwks = get_jwks()
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")

        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(401, "Invalid token key")

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.COGNITO_CLIENT_ID,
            issuer=ISSUER,
        )

        if payload.get("token_use") not in ["id", "access"]:
            raise HTTPException(401, "Invalid token type")

        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ---------------- TOKEN EXTRACT ----------------
def get_token_from_request(request: Request):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    if request.cookies.get("id_token"):
        return request.cookies.get("id_token")

    if request.cookies.get("access_token"):
        return request.cookies.get("access_token")

    raise HTTPException(status_code=401, detail="Not authenticated")


# ---------------- CURRENT USER ----------------
def get_current_user(request: Request):
    token = get_token_from_request(request)
    payload = verify_jwt(token)

    return {
        "user_id": payload["sub"],
        "email": payload.get("email"),
        "groups": payload.get("cognito:groups", []),
        "claims": payload,
    }


# 🛡️ ---------------- RBAC ----------------
class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user=Depends(get_current_user)):
        user_groups = current_user.get("groups", [])

        if not any(role in user_groups for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission"
            )
        return current_user
