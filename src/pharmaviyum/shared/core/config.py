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

from pydantic import model_validator
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
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
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
    # A secret is mandatory outside local development. Never fall back to a
    # known value in staging/production.
    SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

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
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100

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

    settings_config = None


settings = Settings()

# Add these settings to Settings class if not already present
# EMAILS_ENABLED: bool = True
# APP_URL: str = "http://localhost:3000"
