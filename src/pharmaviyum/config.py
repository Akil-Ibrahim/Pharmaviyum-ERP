"""
Configuration management using pydantic-settings.
Best Practice: All sensitive data MUST come from environment variables.
Never hardcode secrets in source code.
"""

from typing import List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator, model_validator
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
    # SECRET_KEY is the documented deployment variable. API_SECRET_KEY remains
    # supported for compatibility with existing deployments.
    SECRET_KEY: Optional[str] = None
    API_SECRET_KEY: Optional[str] = None
    ADMIN_USER: str = "admin"
    ADMIN_EMAIL: str = "admin@pharmaviyum.local"
    # Bootstrap login is disabled unless an operator explicitly configures it.
    ADMIN_PASSWORD: Optional[str] = None

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

    @model_validator(mode="after")
    def validate_security_configuration(self) -> "Settings":
        """Reject unsafe production secrets and disable default admin credentials."""
        environment = self.ENVIRONMENT.strip().lower()
        secret_key = self.API_SECRET_KEY or self.SECRET_KEY

        if environment in {"production", "staging"}:
            if not secret_key or len(secret_key) < 32:
                raise ValueError(
                    "SECRET_KEY (or API_SECRET_KEY) must be configured with at "
                    "least 32 characters in staging and production"
                )
        elif not secret_key:
            secret_key = "dev_secret_key_for_local_testing_only_32_chars_min"

        self.SECRET_KEY = secret_key
        self.API_SECRET_KEY = secret_key

        if self.ADMIN_PASSWORD is not None and not self.ADMIN_PASSWORD.strip():
            self.ADMIN_PASSWORD = None
        elif (
            environment in {"production", "staging"}
            and self.ADMIN_PASSWORD is not None
            and len(self.ADMIN_PASSWORD) < 16
        ):
            raise ValueError(
                "ADMIN_PASSWORD must contain at least 16 characters when "
                "bootstrap login is enabled in staging or production"
            )

        return self

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql+asyncpg://", 1)
        elif value.startswith("postgresql://"):
            value = value.replace("postgresql://", "postgresql+asyncpg://", 1)
        # SQLAlchemy's asyncpg dialect passes URL query parameters directly to
        # asyncpg.connect(). Translate libpq's sslmode and drop unsupported
        # channel_binding, which otherwise raises TypeError at connection time.
        parts = urlsplit(value)
        query = []
        for key, item in parse_qsl(parts.query, keep_blank_values=True):
            normalized_key = "ssl" if key.lower() == "sslmode" else key
            if normalized_key.lower() == "channel_binding":
                continue
            query.append((normalized_key, item))
        return urlunsplit(parts._replace(query=urlencode(query)))

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
