import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router

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
    # Simple error formatting since we removed custom format function
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


@app.on_event("startup")
async def on_startup():
    """Initialize application on startup."""
    logger.info("Application starting up - using AWS Cognito for authentication")
    logger.info("Application startup completed successfully")


app.include_router(api_router)
