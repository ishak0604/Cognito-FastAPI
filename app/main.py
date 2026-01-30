import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.exceptions import format_validation_errors

# Configure minimal logging for memory efficiency
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Production FastAPI Auth Service",
    docs_url=None,  # Disable docs in production for memory savings
    redoc_url=None
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors with user-friendly format.
    
    This is called when:
    - Missing required fields
    - Invalid field format
    - Type validation fails
    - Custom validators fail
    """
    errors, status_code = format_validation_errors(exc.errors())
    
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "details": errors
        }
    )


@app.on_event("startup")
async def on_startup():
    """Initialize application on startup."""
    logger.info("Application starting up")
    try:
        # Lazy import for faster startup
        from app.database.base import Base
        from app.database.session import engine
        
        logger.info("Initializing database tables")
        Base.metadata.create_all(bind=engine)
        logger.info("Application startup completed successfully")
    except ImportError as e:
        logger.error(f"Database import failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


app.include_router(api_router)

# Add health check endpoints
from app.api.v1.endpoints.health import router as health_router
app.include_router(health_router)
