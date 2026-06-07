from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class CoreSettings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
	APP_NAME: str = "pharmaviyum"
	ENV: str = "development"
	LOG_LEVEL: str = "INFO"
	SENTRY_DSN: str | None = None
	REDIS_URL: str = "redis://localhost:6379/0"
	DATABASE_URL: str = "postgresql+asyncpg://postgres:pass@localhost:5432/pharmaviyum"
	APP_DIR: Path = Path(__file__).resolve().parents[2]


settings = CoreSettings()
