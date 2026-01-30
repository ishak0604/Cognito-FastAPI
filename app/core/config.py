import os
from dotenv import load_dotenv, find_dotenv

# Load generated devops/cognito.env first (if present), then fallback to devops/.env
devops_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "devops", "cognito.env")
if os.path.exists(os.path.abspath(devops_env_path)):
    load_dotenv(devops_env_path)
else:
    # fallback: project devops/.env (local parameters used for deploy)
    local_devops_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "devops", ".env")
    if os.path.exists(os.path.abspath(local_devops_env)):
        load_dotenv(local_devops_env)

# Also load repo root .env (if present) for DB dev overrides
load_dotenv(find_dotenv())

class Settings:
    # Cognito
    COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
    COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
    COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
    COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN")
    COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")

    # Database (for local dev fallback)
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_SECRET_ARN = os.getenv("DATABASE_SECRET_ARN")

settings = Settings()