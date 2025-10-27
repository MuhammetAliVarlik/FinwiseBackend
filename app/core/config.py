# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FinwiseBackend"
    DATABASE_URL: str
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
