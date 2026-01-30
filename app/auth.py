import os
import requests
from jose import jwt
from jose.exceptions import JWTError
from time import time
from typing import Optional

COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

# JWKS caching
_jwks = None
_jwks_last_fetch = 0
_jwks_ttl = 3600  # seconds

def _get_jwks():
    global _jwks, _jwks_last_fetch
    if _jwks and time() - _jwks_last_fetch < _jwks_ttl:
        return _jwks
    if not COGNITO_USER_POOL_ID or not COGNITO_REGION:
        raise RuntimeError("COGNITO_USER_POOL_ID and COGNITO_REGION must be set")
    jwks_url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    r = requests.get(jwks_url, timeout=10)
    r.raise_for_status()
    _jwks = r.json()
    _jwks_last_fetch = time()
    return _jwks

def verify_cognito_jwt(token: str) -> Optional[dict]:
    """
    Verify a Cognito-issued JWT (id or access token) using JWKS.
    Returns claims dict if token is valid, otherwise None.
    """
    try:
        jwks = _get_jwks()
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        if not kid:
            return None
        key = None
        for k in jwks.get("keys", []):
            if k.get("kid") == kid:
                key = k
                break
        if not key:
            return None
        claims = jwt.decode(
            token,
            key,
            algorithms=[unverified.get("alg", "RS256")],
            audience=COGNITO_CLIENT_ID,
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
        )
        return claims
    except JWTError:
        return None
    except Exception:
        return None