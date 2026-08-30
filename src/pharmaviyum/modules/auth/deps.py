"""
FastAPI dependencies for authentication.

Provides reusable dependency functions for:
- Getting current user from JWT token
- Requiring active user
- Requiring superuser privileges
- Database session
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import uuid

from .models import User
from ...shared.core.config import settings
from ...shared.core.database import get_session


# OAuth2 scheme: extracts Bearer token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/access-token")

# Type alias for database session
SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user(
    session: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """
    Dependency: Extract and validate current user from JWT token.
    
    Raises:
        HTTPException 400: Invalid token
        HTTPException 400: User not found
        
    Returns:
        Current authenticated user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Could not validate credentials",
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
    
    user = session.get(User, user_id)
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency: Ensure current user is active.
    
    Raises:
        HTTPException 400: Inactive user
        
    Returns:
        Active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user


def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Dependency: Ensure current user is active superuser.
    
    Raises:
        HTTPException 403: Not authorized
        
    Returns:
        Active superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


# Type aliases for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentSuperuser = Annotated[User, Depends(get_current_active_superuser)]
