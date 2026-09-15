"""
Application configuration using Pydantic Settings
Best practice 2026: Environment-aware, feature flags, telemetry config
"""

from enum import Enum
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Deployment environments"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}

    # Application
    APP_NAME: str = "Pharmaviyum CRM"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/pharmaviyum"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # Security
    SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        """Fail closed when a deployment environment lacks a JWT secret."""
        if self.ENVIRONMENT in {Environment.STAGING, Environment.PRODUCTION}:
            if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be set to at least 32 characters in staging "
                    "and production"
                )
        return self

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 20

    # Mortarium AI
    MORTARIUM_MODEL_PATH: str = "./models/qwen2.5-7b-instruct-q4_k_m.gguf"
    MORTARIUM_EMBEDDING_MODEL: str = "BAAI/bge-m3"
    MORTARIUM_CONTEXT_LENGTH: int = 8192
    MORTARIUM_CACHE_TTL: int = 3600
    MORTARIUM_MAX_CONCURRENT: int = 5

    # Telemetry (OpenTelemetry 2026)
    # Disable by default for Python 3.14 compatibility because the OTLP/protobuf
    # stack can fail during import on newer interpreters. It can be re-enabled in
    # a compatible environment if needed.
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "pharmaviyum-crm"
    OTEL_EXPORTER_ENDPOINT: Optional[str] = None
    OTEL_TRACES_SAMPLE_RATE: float = 0.1

    # Supported languages (SEA region)
    SUPPORTED_LANGUAGES: list[str] = ["vi", "en", "zh", "ko", "ms", "id", "th"]
    DEFAULT_LANGUAGE: str = "vi"

    # Notification channels by country
    NOTIFICATION_CHANNELS: dict = {
        "VN": "zalo",
        "TH": "line",
        "ID": "whatsapp",
        "MY": "whatsapp",
        "PH": "messenger",
        "SG": "whatsapp",
    }

    # Feature flags (2026 best practice)
    FEATURE_AI_RECOMMENDATIONS: bool = True
    FEATURE_HALAL_FILTER: bool = True
    FEATURE_TROPICAL_STORAGE: bool = True
    FEATURE_TELEMEDICINE: bool = False
    FEATURE_SOCIAL_COMMERCE: bool = False

    # POS integrations
    KIOVIET_API_URL: Optional[str] = None
    KIOVIET_API_KEY: Optional[str] = None
    SAPO_API_URL: Optional[str] = None
    SAPO_API_KEY: Optional[str] = None
    VIETTEL_PMS_API_URL: Optional[str] = None
    VIETTEL_PMS_API_KEY: Optional[str] = None

    # Background jobs
    ARQ_REDIS_URL: str = "redis://localhost:6379/1"

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100


settings = Settings()
