from fastapi import APIRouter
from app.api.v1.endpoints.cognito_auth_endpoints import router as cognito_auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.user import router as user_router
from app.api.v1.endpoints.admin import router as admin_router
api_router = APIRouter()  # remove prefix here

api_router.include_router(cognito_auth_router)
api_router.include_router(health_router)
api_router.include_router(user_router)
api_router.include_router(admin_router)