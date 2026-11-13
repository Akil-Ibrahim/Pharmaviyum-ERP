from datetime import datetime, timedelta
from typing import Dict

import jwt
from jwt import PyJWTError

from src.pharmaviyum.config import settings


def decode_access_token(token: str) -> dict | None:
    """Decode and validate an API JWT using the same signing configuration."""
    if not settings.API_SECRET_KEY:
        return None
    try:
        return jwt.decode(
            token,
            settings.API_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except PyJWTError:
        return None


def create_access_token(subject: str, expires_delta: int | None = None) -> str:
    if not settings.API_SECRET_KEY:
        raise ValueError("API_SECRET_KEY must be set to generate access tokens.")

    expires_delta = expires_delta or settings.JWT_EXPIRY_HOURS * 3600
    to_encode: Dict[str, object] = {"sub": subject}
    expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.API_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
