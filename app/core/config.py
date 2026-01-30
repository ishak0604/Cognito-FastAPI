"""Application configuration settings."""

import logging
from functools import lru_cache
from typing import List

from pydantic import Field, validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Database Configuration
    DATABASE_URL: str = Field(..., description="Database connection URL")
    
    # JWT Configuration
    SECRET_KEY: str = Field(
        ..., 
        min_length=32,
        description="JWT secret key - must be at least 32 characters"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, 
        ge=1, 
        le=1440,  # Max 24 hours
        description="Access token expiry in minutes"
    )
    
    # Application Configuration
    ENVIRONMENT: str = Field(
        default="development",
        description="Application environment"
    )
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # AWS Cognito Configuration
    COGNITO_USER_POOL_ID: str = Field(
        default="",
        description="Cognito User Pool ID"
    )
    COGNITO_CLIENT_ID: str = Field(
        default="",
        description="Cognito User Pool Client ID"
    )
    COGNITO_CLIENT_SECRET: str = Field(
        default="",
        description="Cognito User Pool Client Secret"
    )
    COGNITO_REGION: str = Field(
        default="us-east-1",
        description="AWS region for Cognito"
    )
    COGNITO_DOMAIN: str = Field(
        default="",
        description="Cognito domain URL"
    )
    

    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if v == "fallback-secret-key-change-in-production":
            raise ValueError("Must set a secure SECRET_KEY in production")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL URL")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        validate_assignment = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    try:
        settings = Settings()
        
        # Log configuration (safely)
        logger.info(f"Settings loaded for {settings.ENVIRONMENT} environment")
        logger.info(f"Database configured: {settings.DATABASE_URL.split('@')[0]}@***")
        logger.info(f"JWT expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
        logger.info(f"Debug mode: {settings.DEBUG}")
        
        return settings
        
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        raise RuntimeError(f"Configuration error: {e}") from e


# Global settings instance
settings = get_settings()


def get_cognito_jwks() -> str:
    """Get Cognito JWKS URL for token verification."""
    return f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"


def get_cognito_config() -> Dict[str, str]:
    """Return all Cognito configuration settings."""
    return {
        "user_pool_id": settings.COGNITO_USER_POOL_ID,
        "client_id": settings.COGNITO_CLIENT_ID,
        "client_secret": settings.COGNITO_CLIENT_SECRET,
        "region": settings.COGNITO_REGION,
        "domain": settings.COGNITO_DOMAIN,
        "jwks_url": get_cognito_jwks()
    }


def validate_cognito_connection() -> bool:
    """Test connection to Cognito by fetching JWKS."""
    try:
        import requests
        jwks_url = get_cognito_jwks()
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()

        jwks = response.json()
        if "keys" in jwks and len(jwks["keys"]) > 0:
            logger.info("Cognito connection validated successfully")
            return True
        else:
            logger.error("Invalid JWKS response from Cognito")
            return False

    except Exception as e:
        logger.error(f"Cognito connection validation failed: {e}")
        return False
