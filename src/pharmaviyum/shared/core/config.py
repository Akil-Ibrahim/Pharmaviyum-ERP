"""
Application configuration using Pydantic Settings.

Best practice 2026: Environment-aware configuration with:
- Feature flags for gradual rollouts
- Telemetry configuration (OpenTelemetry)
- Rate limiting and pagination defaults
- SEA region specific settings (Halal, COD, multi-currency)
"""

from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Deployment environments"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}

    # Application
    APP_NAME: str = "Pharmaviyum CRM"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Environment = Environment.PRODUCTION
    LOG_LEVEL: str = "INFO"

    # Database (single URL, best practice 2026)
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/pharmaviyum"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # Security
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Mortarium AI
    MORTARIUM_MODEL: str = "qwen2.5:7b"
    MORTARIUM_ENDPOINT: str = "http://localhost:11434"
    MORTARIUM_CONTEXT_LENGTH: int = 8192

    # Feature flags
    FEATURE_AI_RECOMMENDATIONS: bool = True
    FEATURE_HALAL_FILTER: bool = True
    FEATURE_SOCIAL_COMMERCE: bool = False

    # SEA region settings
    DEFAULT_LANGUAGE: str = "vi"
    DEFAULT_CURRENCY: str = "VND"

    # POS integrations
    KIOVIET_API_URL: Optional[str] = None
    KIOVIET_API_KEY: Optional[str] = None
    SAPO_API_URL: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()

# Add these settings to Settings class if not already present
# EMAILS_ENABLED: bool = True
# APP_URL: str = "http://localhost:3000"
