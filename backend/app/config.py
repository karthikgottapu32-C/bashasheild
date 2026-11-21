from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "production"
    CORS_ORIGINS: str = (
        "https://bhashashield-api.onrender.com,"
        "https://bhashashield.onrender.com,"
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "http://localhost:4173,"
        "http://127.0.0.1:4173"
    )
    DATABASE_PATH: str = str(BASE_DIR / "data" / "bhashashield.db")
    DATABASE_URL: Optional[str] = os.environ.get("DATABASE_URL")
    GEMINI_API_KEY: str = ""
    MODEL_PATH: str = str(BASE_DIR / "data" / "muril_classifier.joblib")
    USE_ML_MODEL: bool = True
    MAX_INPUT_LENGTH: int = 10000
    ADMIN_API_KEY: str = os.environ.get("ADMIN_API_KEY", "")
    RATE_LIMIT_PER_MINUTE: int = 120

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip() and origin.strip() != "*"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
