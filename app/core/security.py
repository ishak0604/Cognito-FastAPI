from jose import jwt
import requests
from fastapi import HTTPException, Request, status, Depends
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
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth.split(" ")[1]
    payload = verify_jwt(token)

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "claims": payload
    }


# 🔐 RBAC dependency
def require_role(role: str):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user["claims"].get("custom:role", "user") != role:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user
    return role_checker
