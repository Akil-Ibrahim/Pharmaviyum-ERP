"""
Core module - Configuration, database, and utilities
Best practice 2026: Clean architecture foundation
"""
from .config import settings
from .database import Base, engine, async_session, get_db
from .security import verify_password, get_password_hash, create_access_token
from .repository import BaseRepository
from .uow import UnitOfWork
from .logging import setup_logging, get_logger

__all__ = [
    "settings",
    "Base",
    "engine",
    "async_session",
    "get_db",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "BaseRepository",
    "UnitOfWork",
    "setup_logging",
    "get_logger",
]
