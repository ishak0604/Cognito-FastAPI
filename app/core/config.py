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
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    COGNITO_USER_POOL_ID: str = Field(
        default="",
        description="Cognito User Pool ID"
    )
    COGNITO_CLIENT_ID: str = Field(
        default="",
        description="Cognito User Pool Client ID"
    )
    USE_COGNITO: bool = Field(
        default=False,
        description="Enable Cognito authentication"
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
