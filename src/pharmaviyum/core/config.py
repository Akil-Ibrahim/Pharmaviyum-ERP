"""Application configuration using Pydantic Settings."""

from enum import Enum
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings with environment-aware security defaults."""

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}

    APP_NAME: str = "Pharmaviyum CRM"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/pharmaviyum"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    SECRET_KEY: Optional[str] = None
    API_SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5

    @model_validator(mode="after")
    def validate_and_normalize_configuration(self) -> "Settings":
        """Normalize managed PostgreSQL URLs and enforce deployment security."""
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        elif self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        # Keep compatibility with the existing API_SECRET_KEY environment
        # variable while the application standardizes on SECRET_KEY.
        if not self.SECRET_KEY and self.API_SECRET_KEY:
            self.SECRET_KEY = self.API_SECRET_KEY

        if self.ENVIRONMENT in {Environment.STAGING, Environment.PRODUCTION}:
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be set to at least 32 characters in staging "
                    "and production"
                )
        return self

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 20
    EMAILS_ENABLED: bool = False
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "pharmaviyum-crm"
    OTEL_EXPORTER_ENDPOINT: Optional[str] = None
    OTEL_TRACES_SAMPLE_RATE: float = 0.1
    SUPPORTED_LANGUAGES: list[str] = ["vi", "en", "zh", "ko", "ms", "id", "th"]
    DEFAULT_LANGUAGE: str = "vi"
    NOTIFICATION_CHANNELS: dict = {
        "VN": "zalo",
        "TH": "line",
        "ID": "whatsapp",
        "MY": "whatsapp",
        "PH": "messenger",
        "SG": "whatsapp",
    }
    FEATURE_AI_RECOMMENDATIONS: bool = True
    FEATURE_HALAL_FILTER: bool = True
    FEATURE_TROPICAL_STORAGE: bool = True
    FEATURE_TELEMEDICINE: bool = False
    FEATURE_SOCIAL_COMMERCE: bool = False
    KIOVIET_API_URL: Optional[str] = None
    KIOVIET_API_KEY: Optional[str] = None
    SAPO_API_URL: Optional[str] = None
    SAPO_API_KEY: Optional[str] = None
    VIETTEL_PMS_API_URL: Optional[str] = None
    VIETTEL_PMS_API_KEY: Optional[str] = None
    ARQ_REDIS_URL: str = "redis://localhost:6379/1"
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100


settings = Settings()
