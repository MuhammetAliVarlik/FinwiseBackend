import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Finwise Scribe API"
    VERSION: str = "1.0.0"
    
    # Defaults
    ENVIRONMENT: str = "development"
    # FIXED: Default to async driver 'postgresql+asyncpg'
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/finwise"
    
    # Model Path
    MODEL_PATH: str = "/app/ml_models/v1_adapter"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()