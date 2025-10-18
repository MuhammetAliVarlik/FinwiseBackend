import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://admin:admin@db:5432/finwise_db")
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"

settings = Settings()