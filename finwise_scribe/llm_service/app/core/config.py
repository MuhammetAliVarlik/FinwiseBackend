from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Finwise Scribe LLM"

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # AI service configs
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_NUM_CTX: int = 1024
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"
    NEWS_RSS_TEMPLATE: str = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        accepted = {"development", "test", "staging", "production"}
        lower = value.lower()
        if lower not in accepted:
            raise ValueError(f"ENVIRONMENT must be one of {sorted(accepted)}")
        return lower

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        accepted = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        upper = value.upper()
        if upper not in accepted:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(accepted)}")
        return upper

    @field_validator("OLLAMA_NUM_CTX")
    @classmethod
    def validate_ollama_num_ctx(cls, value: int) -> int:
        if value < 256:
            raise ValueError("OLLAMA_NUM_CTX must be >= 256")
        return value

settings = Settings()