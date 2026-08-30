"""
Docker Secrets Reader.
Reads secrets from /run/secrets/ with fallback to environment variables.
"""
from pathlib import Path
from functools import lru_cache
import os


@lru_cache(maxsize=32)
def read_secret(secret_name: str, default=None):
    """Read secret from Docker secrets or environment."""
    secret_path = Path(f"/run/secrets/{secret_name}")
    
    if secret_path.exists():
        return secret_path.read_text().strip()
    
    env_var = secret_name.upper()
    return os.getenv(env_var, default)
