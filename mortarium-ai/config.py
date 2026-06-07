from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    BASE_DIR: Path = Path(__file__).resolve().parent
    VECTOR_STORE_PATH: Path = BASE_DIR / "data" / "vector_store"
    MODEL_PATH: Path = BASE_DIR / "models" / "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
    MODEL_N_CTX: int = 32000
    MODEL_N_GPU_LAYERS: int = -1
    MODEL_TEMPERATURE: float = 0.15
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:pass@localhost:5432/mortarium_db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    OTEL_EXPORTER_ENDPOINT: str = os.getenv("OTEL_EXPORTER_ENDPOINT", "http://otel-collector:4317")
    SERVICE_NAME: str = "mortarium-ai"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "")
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 60

settings = Settings()
