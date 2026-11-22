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
    REQUIRE_POSTGRES: bool = os.environ.get("REQUIRE_POSTGRES", "false").lower() in ("true", "1")
    GEMINI_API_KEY: str = ""
    MODEL_PATH: str = str(BASE_DIR / "data" / "muril_classifier.joblib")
    USE_ML_MODEL: bool = True
    MAX_INPUT_LENGTH: int = 10000
    ADMIN_API_KEY: str = os.environ.get("ADMIN_API_KEY", "")
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "bhashashield-enterprise-secret-key-prod-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    RATE_LIMIT_PER_MINUTE: int = 120
    AUTH_RATE_LIMIT_LOGIN: int = 10
    AUTH_RATE_LIMIT_REGISTER: int = 5
    AUTH_FAILED_LOGIN_LOCKOUT_ATTEMPTS: int = 5
    AUTH_FAILED_LOGIN_LOCKOUT_SECONDS: int = 60

    @property
    def cors_origin_list(self) -> List[str]:
        raw_list = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip() and origin.strip() != "*"]
        if self.ENVIRONMENT.lower() == "production":
            # Production: strictly verified HTTPS origins only, never allow localhost or non-https
            prod_origins = [
                "https://bhashashield-api.onrender.com",
                "https://bhashashield.onrender.com"
            ]
            for o in raw_list:
                if o.startswith("https://") and "localhost" not in o and "127.0.0.1" not in o:
                    if o not in prod_origins:
                        prod_origins.append(o)
            return prod_origins
        else:
            # Development / Testing: include local development origins
            dev_origins = [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:4173",
                "http://127.0.0.1:4173",
                "http://localhost:8000",
                "http://127.0.0.1:8000"
            ]
            for o in raw_list:
                if o not in dev_origins:
                    dev_origins.append(o)
            return dev_origins

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
