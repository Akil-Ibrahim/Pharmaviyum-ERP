from datetime import datetime, timedelta
from jose import jwt
from typing import Dict
from src.pharmaviyum.config import settings


def create_access_token(subject: str, expires_delta: int = 3600) -> str:
	to_encode: Dict[str, object] = {"sub": subject}
	expire = datetime.utcnow() + timedelta(seconds=expires_delta)
	to_encode.update({"exp": expire})
	key = settings.API_SECRET_KEY or ""  # type: ignore[attr-defined]
	return jwt.encode(to_encode, key, algorithm="HS256")
