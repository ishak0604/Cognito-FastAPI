from fastapi import Request, HTTPException, status
from app.core.security import verify_jwt


def get_current_user(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = verify_jwt(token)

    return {
        "user_id": payload["sub"],
        "email": payload.get("email"),
    }
