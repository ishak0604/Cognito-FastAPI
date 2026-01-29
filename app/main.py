import logging
import time
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.v1.router import api_router
from app.exceptions import format_validation_errors

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI(title="Production FastAPI Auth Service")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Optimized middleware for request logging."""
    
    # Pre-compile path set for faster lookup
    SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/favicon.ico"}
    
    async def dispatch(self, request: Request, call_next):
        # Fast path check - skip logging for static/health endpoints
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)
        
        # Process request with minimal overhead
        start_time = time.perf_counter()
        response = await call_next(request)
        
        # Only log if there's an issue (error or performance problem)
        if response.status_code >= 400:
            process_time = time.perf_counter() - start_time
            logger.error(
                f"{request.method} {request.url.path} - {response.status_code} ({process_time:.2f}s)"
            )
        elif time.perf_counter() - start_time > 2.0:  # Only log very slow requests
            logger.warning(f"Slow request: {request.method} {request.url.path} ({time.perf_counter() - start_time:.2f}s)")
        
        return response


# Add request/response logging middleware
app.add_middleware(RequestLoggingMiddleware)


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
