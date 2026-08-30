"""
Security utilities for authentication.

Security features:
- Bcrypt password hashing with automatic salt
- Constant-time comparison to prevent timing attacks
- JWT token creation with user ID subject
"""
import hmac
from datetime import datetime, timedelta
from typing import Any
from jose import jwt
from passlib.context import CryptContext
from ...shared.core.config import settings

# Password hashing with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Bcrypt automatically handles:
    - Salt generation (unique per password)
    - Cost factor (default 12 rounds)
    - Safe storage format
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Uses passlib's verify which is constant-time internally.
    """
    return pwd_context.verify(plain_password, hashed_password)


def constant_time_compare(a: str, b: str) -> bool:
    """
    Constant-time string comparison to prevent timing attacks.
    
    Uses hmac.compare_digest which is implemented in C and takes
    the same time regardless of where strings differ.
    """
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def create_access_token(
    subject: Any,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: User ID (will be converted to string)
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT string
        
    Token payload:
    {
        "exp": <expiration timestamp>,
        "sub": "<user_id>"
    }
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def verify_token(token: str) -> dict | None:
    """
    Verify and decode a JWT token.
    
    Returns:
        Token payload if valid, None if invalid
    """
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except Exception:
        return None
