from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Finwise Scribe LLM"
    
    # AI Service Configs
    OLLAMA_URL: str = "http://ollama:11434"
    
    # --- ADD THIS LINE ---
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"

    class Config:
        env_file = ".env"

settings = Settings()