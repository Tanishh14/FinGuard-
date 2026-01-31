"""
Configuration settings for FinGuard AI Backend
Compatible with Pydantic v2
"""

from typing import List, Optional
from functools import lru_cache
import secrets

from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator, model_validator


class Settings(BaseSettings):
    # =========================
    # Application
    # =========================
    PROJECT_NAME: str = "FinGuard AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    API_V1_STR: str = "/api/v1"

    # =========================
    # Security
    # =========================
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    # =========================
    # CORS
    # =========================
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://finguard-ai.com",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "finguard-ai.com"]

    # =========================
    # Database
    # =========================
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "finguard"
    POSTGRES_PASSWORD: str = "finguard_password"
    POSTGRES_DB: str = "finguard_db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    # =========================
    # Redis
    # =========================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None

    @model_validator(mode="after")
    def assemble_db_and_redis_urls(self):
        if not self.DATABASE_URL:
            from urllib.parse import quote_plus
            user = quote_plus(self.POSTGRES_USER)
            password = quote_plus(self.POSTGRES_PASSWORD)
            self.DATABASE_URL = f"postgresql+asyncpg://{user}:{password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        if not self.REDIS_URL:
            auth = f"{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
            self.REDIS_URL = f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return self

    # =========================
    # ML Service
    # =========================
    ML_SERVICE_URL: str = "http://localhost:8001"
    ML_MODEL_TIMEOUT: int = 30

    # =========================
    # Explainability Service
    # =========================
    EXPLAIN_SERVICE_URL: str = "http://localhost:8002"
    LLM_MODEL_NAME: str = "llama3"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # =========================
    # Alerting
    # =========================
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    ALERT_EMAIL_FROM: str = "alerts@finguard-ai.com"
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # =========================
    # Fraud Risk Thresholds
    # =========================
    RISK_SCORE_HIGH: float = 75.0
    RISK_SCORE_MEDIUM: float = 50.0
    RISK_SCORE_LOW: float = 25.0

    # =========================
    # Rate Limiting
    # =========================
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    # =========================
    # Monitoring
    # =========================
    ENABLE_PROMETHEUS: bool = True
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
