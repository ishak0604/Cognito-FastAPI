from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# Lazy load routers to improve startup time
def include_routers():
    from app.api.v1.endpoints.signup import router as signup_router
    from app.api.v1.endpoints.login import router as login_router
    from app.api.v1.endpoints.password import router as password_router
    from app.api.v1.endpoints.profile import router as profile_router
    from app.api.v1.endpoints.token import router as token_router
    from app.api.v1.endpoints.cognito_auth_endpoints import router as cognito_auth_router

    api_router.include_router(signup_router)
    api_router.include_router(login_router)
    api_router.include_router(password_router)
    api_router.include_router(profile_router)
    api_router.include_router(token_router)
    api_router.include_router(cognito_auth_router)

# Initialize routers
include_routers()
