"""Security utilities for authentication."""

import hmac
from datetime import datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from src.pharmaviyum.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison (prevents timing attacks)."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def create_access_token(subject: Any, expires_delta: timedelta | None = None) -> str:
    """Create short-lived JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Any) -> str:
    """Create long-lived refresh token (7 days)."""
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str, expected_type: str = "access") -> dict | None:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != expected_type:
            return None
        return payload
    except jwt.PyJWTError:
        return None
