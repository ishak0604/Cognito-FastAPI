from fastapi import Depends, HTTPException
from app.core.security import get_current_user


def require_roles(allowed_roles: list[str]):
    def role_checker(user=Depends(get_current_user)):
        user_groups = user.get("groups", [])

        if not any(role in user_groups for role in allowed_roles):
            raise HTTPException(status_code=403, detail="Forbidden")

        return user
    return role_checker
