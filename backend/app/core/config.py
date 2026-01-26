"""
Configuration settings for FinGuard AI Backend
Uses pydantic-settings for environment variable management
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator, PostgresDsn, RedisDsn
from functools import lru_cache
import secrets


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "FinGuard AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, testing, production
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)
    API_V1_STR: str = "/api/v1"
    
    # Security
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # Frontend dev
        "http://localhost:8000",  # Backend dev
        "https://finguard-ai.com",  # Production frontend
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "finguard-ai.com"]
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "finguard"
    POSTGRES_PASSWORD: str = "finguard_password"
    POSTGRES_DB: str = "finguard_db"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"{values.get('POSTGRES_DB') or ''}",
        )
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[RedisDsn] = None
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        
        password = values.get("REDIS_PASSWORD")
        auth = f"{password}@" if password else ""
        
        return f"redis://{auth}{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
    
    # ML Service
    ML_SERVICE_URL: str = "http://localhost:8001"
    ML_MODEL_TIMEOUT: int = 30
    
    # Explanation Service
    EXPLAIN_SERVICE_URL: str = "http://localhost:8002"
    LLM_MODEL_NAME: str = "llama3"  # or "gpt-4", "claude", etc.
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Alerting
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    ALERT_EMAIL_FROM: str = "alerts@finguard-ai.com"
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Fraud Detection Thresholds
    RISK_SCORE_HIGH: float = 75.0
    RISK_SCORE_MEDIUM: float = 50.0
    RISK_SCORE_LOW: float = 25.0
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Monitoring
    ENABLE_PROMETHEUS: bool = True
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()