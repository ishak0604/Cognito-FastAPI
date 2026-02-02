import requests
from jose import jwt
from fastapi import HTTPException, Request, Depends, status
from functools import lru_cache
from app.core.config import settings
import time
from threading import Lock

# -------------------- Cognito Config --------------------
ISSUER = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
JWKS_URL = f"{ISSUER}/.well-known/jwks.json"

# -------------------- JWKS Caching --------------------
_jwks_cache = None
_jwks_cache_expiry = 0
_jwks_lock = Lock()
CACHE_TTL = 3600  # 1 hour cache

def get_jwks():
    """
    Fetch JWKS from Cognito and cache for CACHE_TTL seconds.
    Thread-safe and auto-refresh.
    """
    global _jwks_cache, _jwks_cache_expiry

    with _jwks_lock:
        if _jwks_cache and time.time() < _jwks_cache_expiry:
            return _jwks_cache

        try:
            response = requests.get(JWKS_URL, timeout=5)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_cache_expiry = time.time() + CACHE_TTL
            return _jwks_cache
        except requests.RequestException:
            if _jwks_cache:
                # fallback to cached keys if request fails
                return _jwks_cache
            raise HTTPException(status_code=503, detail="Unable to fetch JWKS from Cognito")

# -------------------- JWT Verification --------------------
def verify_jwt(token: str):
    """
    Verify Cognito JWT: signature, expiry, audience, issuer, and token_use.
    Only access tokens are accepted.
    """
    try:
        jwks = get_jwks()
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token key")

        # Decode JWT
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.COGNITO_CLIENT_ID,
            issuer=ISSUER,
        )

        # Only allow ACCESS tokens
        if payload.get("token_use") != "access":
            raise HTTPException(status_code=401, detail="Use access token")

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTClaimsError:
        raise HTTPException(status_code=401, detail="Invalid token claims")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or malformed token")


# -------------------- Token Extraction --------------------
def get_token_from_request(request: Request):
    """
    Extract JWT from Authorization header or cookie.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    raise HTTPException(status_code=401, detail="Not authenticated")


# -------------------- Current User Dependency --------------------
def get_current_user(request: Request):
    """
    FastAPI dependency to get the current user from a Cognito JWT.
    Returns a dictionary with user info.
    """
    token = get_token_from_request(request)
    payload = verify_jwt(token)

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("custom:role", "user"),  # default role
        "claims": payload,
    }


# -------------------- Role-Based Access Control --------------------
def require_role(role: str):
    """
    Dependency to enforce RBAC in endpoints.
    Example:
        @app.get("/admin")
        def admin_route(user=Depends(require_role("admin"))):
            return {"msg": "Welcome admin"}
    """
    def role_checker(current_user=Depends(get_current_user)):
        if current_user["role"] != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user

    return role_checker
