"""Security package exports for authentication and authorization."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from src.pharmaviyum.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def _signing_key() -> str:
    """Return the configured signing key, with a process-local development key."""
    if settings.SECRET_KEY:
        return settings.SECRET_KEY
    if not hasattr(_signing_key, "_dev_key"):
        _signing_key._dev_key = secrets.token_urlsafe(48)  # type: ignore[attr-defined]
    return _signing_key._dev_key  # type: ignore[attr-defined]


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived JWT access token."""
    to_encode = data.copy()
    to_encode["type"] = "access"
    now = datetime.now(timezone.utc)
    to_encode["iat"] = now
    to_encode["exp"] = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return jwt.encode(to_encode, _signing_key(), algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a refresh JWT with a unique identifier for rotation/revocation."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + (
            expires_delta
            if expires_delta is not None
            else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        ),
    }
    return jwt.encode(payload, _signing_key(), algorithm=settings.ALGORITHM)


def create_password_reset_token(email: str) -> str:
    """Create a 48-hour password-reset JWT."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email,
        "type": "password_reset",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(hours=48),
    }
    return jwt.encode(payload, _signing_key(), algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decode and accept only explicitly issued access tokens."""
    try:
        payload = jwt.decode(token, _signing_key(), algorithms=[settings.ALGORITHM])
        return payload if payload.get("type") == "access" else None
    except jwt.PyJWTError:
        return None


def decode_refresh_token(token: str) -> dict | None:
    """Decode and accept only refresh tokens carrying a unique JTI."""
    try:
        payload = jwt.decode(token, _signing_key(), algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh" or not payload.get("jti"):
            return None
        return payload
    except jwt.PyJWTError:
        return None


def decode_password_reset_token(token: str) -> dict | None:
    """Decode and accept only password-reset tokens carrying a unique JTI."""
    try:
        payload = jwt.decode(token, _signing_key(), algorithms=[settings.ALGORITHM])
        if payload.get("type") != "password_reset" or not payload.get("jti"):
            return None
        return payload
    except jwt.PyJWTError:
        return None
