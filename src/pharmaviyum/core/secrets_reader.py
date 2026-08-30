"""Docker Secrets Reader with env fallback."""
from pathlib import Path
from functools import lru_cache
import os


@lru_cache(maxsize=32)
def read_secret(secret_name: str, default=None):
    """Read secret from /run/secrets/ or environment."""
    secret_path = Path(f"/run/secrets/{secret_name}")
    if secret_path.exists():
        return secret_path.read_text().strip()
    return os.getenv(secret_name.upper(), default)


def get_db_password() -> str:
    pwd = read_secret("pharmaviyum_db_password") or read_secret("DB_PASSWORD")
    if not pwd:
        raise ValueError("Database password not found")
    return pwd


def get_jwt_secret() -> str:
    secret = read_secret("pharmaviyum_jwt_secret") or read_secret("JWT_SECRET_KEY")
    if not secret:
        raise ValueError("JWT secret not found")
    return secret
