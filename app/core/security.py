import requests
import time
from threading import Lock
from jose import jwt
from fastapi import HTTPException, Request
from app.core.config import settings

ISSUER = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"

_jwks_cache = None
_jwks_cache_expiry = 0
_jwks_lock = Lock()
CACHE_TTL = 3600


# ------------------ JWKS FETCH WITH CACHE ------------------
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


# ------------------ JWT VERIFY ------------------
def verify_jwt(token: str):
    jwks = get_jwks()
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")

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

    # 🔐 Accept BOTH ID and Access tokens
    if payload.get("token_use") not in ["id", "access"]:
        raise HTTPException(status_code=401, detail="Invalid token type")

    return payload


# ------------------ TOKEN FROM HEADER OR COOKIE ------------------
def get_token_from_request(request: Request):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    # Fallback to cookies
    id_token = request.cookies.get("id_token")
    if id_token:
        return id_token

    access_token = request.cookies.get("access_token")
    if access_token:
        return access_token

    raise HTTPException(status_code=401, detail="Not authenticated")


# ------------------ CURRENT USER ------------------
def get_current_user(request: Request):
    token = get_token_from_request(request)
    payload = verify_jwt(token)

    return {
        "user_id": payload["sub"],
        "email": payload.get("email"),
        "groups": payload.get("cognito:groups", []),
        "claims": payload,
    }
