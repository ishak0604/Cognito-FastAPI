from fastapi import APIRouter, Depends
from app.core.security import RoleChecker


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/admin-data")
def admin_data(user=Depends(RoleChecker(["admin"]))):
    return {"msg": "Welcome admin"}

