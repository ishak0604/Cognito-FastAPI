import logging
import time
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.v1.router import api_router
from app.database.base import Base
from app.database.session import engine
from app.database.models import User
from app.exceptions import format_validation_errors

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI(title="Production FastAPI Auth Service")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log incoming requests and outgoing responses."""
    
    async def dispatch(self, request: Request, call_next):
        # Log incoming request
        logger.info(
            f"[REQUEST] {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'Unknown'}"
        )
        
        # Track execution time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate execution time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"[RESPONSE] {request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {process_time:.3f}s"
        )
        
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
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(api_router)
