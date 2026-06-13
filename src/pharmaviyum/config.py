from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, ConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    BASE_DIR: Path = Path(__file__).resolve().parent
    AI_SERVICE_URL: AnyHttpUrl = "http://mortarium-ai:8000"
    LOG_LEVEL: str = "INFO"
    MORTARIUM_TIMEOUT_SECONDS: int = 15
    API_SECRET_KEY: str = "dev_api_secret_key_32_chars_minimum_for_jwt_signing"
    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: str = "Admin123!@#"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24


settings = Settings()
