from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging, time
from app.api.v1.router import api_router
from app.database import Base, engine
from app.services import cognito_service

# Logging config
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Production FastAPI Auth Service", docs_url=None, redoc_url=None)


# ---------------------- Middleware for Logging ----------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round(time.time() - start_time, 3)
    logger.info(f"{request.method} {request.url.path} Status:{response.status_code} Time:{duration}s")
    return response


# ---------------------- Exception Handlers ----------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [{"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"], "type": err["type"]} for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": "Validation error", "error_code": "VALIDATION_ERROR", "details": errors}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"success": False, "message": "Internal server error"})


# ---------------------- Startup Event ----------------------
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Starting FastAPI Auth Service...")
    logger.info("📦 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database ready")

    # Sync Cognito users into DB
    try:
        cognito_service.sync_cognito_users_to_db()
        logger.info("✅ Cognito users synced successfully")
    except Exception as e:
        logger.error(f"❌ Failed to sync Cognito users: {e}")


# ---------------------- Include API Router ----------------------
app.include_router(api_router, prefix="/api/v1")
