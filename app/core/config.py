from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    AWS_REGION: str = "ap-south-1"
    COGNITO_USER_POOL_ID: str
    COGNITO_CLIENT_ID: str
    COGNITO_DOMAIN: str
    COGNITO_REGION: str
    CALLBACK_URL: str = "http://localhost:8000/api/v1/auth/callback"
    LOGOUT_URL: str = "http://localhost:3000/logout"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    DATABASE_URL: str 
    

settings = Settings()
