from fastapi import APIRouter

from app.api.v1.endpoints.signup import router as signup_router
from app.api.v1.endpoints.login import router as login_router
from app.api.v1.endpoints.password import router as password_router
from app.api.v1.endpoints.profile import router as profile_router
from app.api.v1.endpoints.token import router as token_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(signup_router)
api_router.include_router(login_router)
api_router.include_router(password_router)
api_router.include_router(profile_router)
api_router.include_router(token_router)
