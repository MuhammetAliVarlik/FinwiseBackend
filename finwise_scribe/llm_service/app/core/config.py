import os

class Settings:
    PROJECT_NAME: str = "Finwise Scribe Engine"
    VERSION: str = "1.0.0"
    # Connects to the Ollama container defined in docker-compose
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://ollama:11434")
    MODEL_NAME: str = "finwise_scribe_v1" # Matches the tag we will give in Ollama

settings = Settings()