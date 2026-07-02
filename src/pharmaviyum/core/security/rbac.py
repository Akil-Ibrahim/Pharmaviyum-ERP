"""
Role-Based Access Control (RBAC) decorator
Best practice 2026: Fine-grained authorization
"""
from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from src.pharmaviyum.core.database import get_db
from src.pharmaviyum.core.security import decode_access_token
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    "cashier": 1,
    "pharmacist": 2,
    "manager": 3,
    "admin": 4,
    "superadmin": 5,
}


def require_role(minimum_role: str):
    """
    Decorator to require minimum role for endpoint
    
    Usage:
        @router.get("/admin-only")
        @require_role("admin")
        async def admin_endpoint():
            ...
    
    Args:
        minimum_role: Minimum role required
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get credentials from kwargs (injected by FastAPI)
            credentials = kwargs.get("credentials")
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            # Decode token
            payload = decode_access_token(credentials.credentials)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            # Check role
            user_role = payload.get("role")
            if not user_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Role not found in token"
                )
            
            # Compare role hierarchy
            user_level = ROLE_HIERARCHY.get(user_role, 0)
            required_level = ROLE_HIERARCHY.get(minimum_role, 0)
            
            if user_level < required_level:
                logger.warning(
                    f"Access denied: user role '{user_role}' < required '{minimum_role}'",
                    extra={"user_id": payload.get("sub")},
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {minimum_role} role or higher"
                )
            
            # Add user to kwargs
            kwargs["current_user"] = payload
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Dependency to get current authenticated user
    
    Returns:
        User payload from JWT token
    """
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return payload


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Dependency to get current active user
    
    Checks if user is active (not disabled)
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return current_user
