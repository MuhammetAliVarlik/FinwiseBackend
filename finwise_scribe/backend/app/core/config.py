import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Finwise Scribe API"
    VERSION: str = "1.0.0"
    
    # Defaults
    ENVIRONMENT: str = "development"  # Options: 'development', 'test', 'production'
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/finwise"
    
    # Model Path (Mounted via Docker volume)
    MODEL_PATH: str = "/app/ml_models/v1_adapter"

    class Config:
        # Tries to read .env from the root or current directory
        env_file = ".env"
        extra = "ignore" # Ignore unknown variables to prevent crash

settings = Settings()