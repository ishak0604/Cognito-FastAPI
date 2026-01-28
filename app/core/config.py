import logging
from pydantic_settings import BaseSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
logger.info(f"Settings loaded successfully from .env")
logger.info(f"Database URL: {settings.DATABASE_URL[:20]}...***")
