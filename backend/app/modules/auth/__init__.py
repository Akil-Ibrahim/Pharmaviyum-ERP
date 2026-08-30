"""
Authentication Module - Complete implementation based on ibrahimengpy template.

Features:
- OAuth2 password grant authentication
- JWT access tokens
- Public user registration
- Password recovery via email
- Password reset with tokens
- User CRUD (admin + self-management)
- Email enumeration protection
- Constant-time authentication
- Superuser protection

All endpoints match the ibrahimengpy/full-stack-fastapi-template structure.
"""
from .models import User
from .schemas import (
    UserCreate,
    UserRegister,
    UserPublic,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
    UpdatePassword,
    NewPassword,
    Token,
    Message,
)
from .deps import (
    get_current_user,
    get_current_active_user,
    get_current_active_superuser,
    CurrentUser,
    CurrentSuperuser,
    SessionDep,
)
from .routes.login import router as login_router
from .routes.users import router as users_router

__all__ = [
    "User",
    "UserCreate",
    "UserRegister",
    "UserPublic",
    "UsersPublic",
    "UserUpdate",
    "UserUpdateMe",
    "UpdatePassword",
    "NewPassword",
    "Token",
    "Message",
    "get_current_user",
    "get_current_active_user",
    "get_current_active_superuser",
    "CurrentUser",
    "CurrentSuperuser",
    "SessionDep",
    "login_router",
    "users_router",
]
