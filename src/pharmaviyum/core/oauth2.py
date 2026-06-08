from datetime import datetime, timedelta
from jose import jwt
from typing import Dict
from src.pharmaviyum.config import settings


def create_access_token(subject: str, expires_delta: int | None = None) -> str:
	if not settings.API_SECRET_KEY:
		raise ValueError("API_SECRET_KEY must be set to generate access tokens.")

	expires_delta = expires_delta or settings.JWT_EXPIRY_HOURS * 3600
	to_encode: Dict[str, object] = {"sub": subject}
	expire = datetime.utcnow() + timedelta(seconds=expires_delta)
	to_encode.update({"exp": expire})
	return jwt.encode(to_encode, settings.API_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
