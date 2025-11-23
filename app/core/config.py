# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "FinwiseBackend"
    DATABASE_URL: str
    ENVIRONMENT: str = "development"
    
    HUGGINGFACE_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
