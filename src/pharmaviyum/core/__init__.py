"""
Core module - Configuration, database, and utilities
Best practice 2026: Clean architecture foundation
"""

from .config import settings
from .database import Base, async_session, engine, get_db
from .logging import get_logger, setup_logging
from .repository import BaseRepository
from .security import create_access_token, get_password_hash, verify_password
from .uow import UnitOfWork

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
