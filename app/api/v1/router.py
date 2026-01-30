from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# Include Cognito authentication endpoints
from app.api.v1.endpoints.cognito_auth_endpoints import router as cognito_auth_router
api_router.include_router(cognito_auth_router)

# Include health check endpoint
from app.api.v1.endpoints.health import router as health_router
api_router.include_router(health_router)
