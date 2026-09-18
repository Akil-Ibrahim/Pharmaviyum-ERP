"""
Configuration management using pydantic-settings.
Best Practice: All sensitive data MUST come from environment variables.
Never hardcode secrets in source code.
"""

from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application
    PROJECT_NAME: str = "PharmaViyum CRM"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # Security
    API_SECRET_KEY: str = Field(
        default="dev_secret_key_for_local_testing_only_32_chars_min", min_length=32
    )
    ADMIN_USER: str = "admin"
    ADMIN_EMAIL: str = "Admin"
    ADMIN_PASSWORD: str = "Admin123!@#"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_AUDIENCE: str = "pharmaviyum-api-dev"
    JWT_ISSUER: str = "pharmaviyum-dev"
    JWT_EXPIRY_HOURS: int = 24  # Token expiry in hours

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://pharmaviyum:postgres@db:5432/pharmaviyum_dev"
    )
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10

    # Observability
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = False

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_DEFAULT: str = "1000/minute"
    RATE_LIMIT_STORAGE_URI: str = "redis://redis:6379/1"


# Global settings instance
settings = Settings()
