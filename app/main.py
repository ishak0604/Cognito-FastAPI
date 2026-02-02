import logging
import time
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.database import Base, engine
from app.models import user  # registers model

# ---------------- LOGGING CONFIG ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------- FASTAPI INIT ----------------
app = FastAPI(
    title="Production FastAPI Auth Service",
    docs_url=None,
    redoc_url=None,
)

# ---------------- REQUEST LOGGING MIDDLEWARE ----------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = round(time.time() - start_time, 3)
    logger.info(
        f"{request.method} {request.url.path} "
        f"Status:{response.status_code} Time:{duration}s"
    )

    return response


# ---------------- VALIDATION ERROR HANDLER ----------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "details": errors
        }
    )


# ---------------- STARTUP EVENT ----------------
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Starting FastAPI Auth Service...")
    logger.info("📦 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database ready")


# ---------------- ROUTERS ----------------
app.include_router(api_router, prefix="/api/v1")
