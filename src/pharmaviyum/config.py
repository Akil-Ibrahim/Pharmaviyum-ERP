from pydantic import BaseSettings, AnyHttpUrl
from pathlib import Path


class Settings(BaseSettings):
	BASE_DIR: Path = Path(__file__).resolve().parent
	AI_SERVICE_URL: AnyHttpUrl = "http://mortarium-ai:8000"
	LOG_LEVEL: str = "INFO"
	MORTARIUM_TIMEOUT_SECONDS: int = 15

	class Config:
		env_file = ".env"


settings = Settings()
