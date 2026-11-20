from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,*"
    DATABASE_PATH: str = str(BASE_DIR / "data" / "bhashashield.db")
    GEMINI_API_KEY: str = ""
    MODEL_PATH: str = str(BASE_DIR / "data" / "muril_classifier.joblib")
    USE_ML_MODEL: bool = True
    MAX_INPUT_LENGTH: int = 10000
    ADMIN_API_KEY: str = ""
    RATE_LIMIT_PER_MINUTE: int = 120

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
