from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Finwise Scribe API"
    VERSION: str = "1.0.0"

    # Runtime environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Backing services (all configurable via environment)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/finwise"
    SCRIBE_SERVICE_URL: str = "http://scribe:8001"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # App behavior
    DB_ECHO: bool = False
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://0.0.0.0:3000",
        ]
    )

    # Security-related configuration
    APP_SECRET_KEY: str = "dev-insecure-key"

    # Model path
    MODEL_PATH: str = "/app/ml_models/v1_adapter"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        accepted = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        upper = value.upper()
        if upper not in accepted:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(accepted)}")
        return upper

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError("DATABASE_URL must use an async SQLAlchemy driver")
        return value

    @field_validator("APP_SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 16:
            raise ValueError("APP_SECRET_KEY must be at least 16 characters")
        return value

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        accepted = {"development", "test", "staging", "production"}
        lower = value.lower()
        if lower not in accepted:
            raise ValueError(f"ENVIRONMENT must be one of {sorted(accepted)}")
        return lower

settings = Settings()

# Fail fast in production if unsafe defaults are still used.
if settings.ENVIRONMENT == "production":
    if "postgres:postgres" in settings.DATABASE_URL or "admin:admin" in settings.DATABASE_URL:
        raise ValueError("Unsafe DATABASE_URL credentials for production")
    if settings.APP_SECRET_KEY == "dev-insecure-key":
        raise ValueError("APP_SECRET_KEY must be changed in production")