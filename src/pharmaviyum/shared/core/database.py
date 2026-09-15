"""
Async database session management.

Best practice 2026: Async SQLAlchemy 2.0 with proper connection pooling,
health checks, and graceful shutdown support.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncAttrs, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,  # Recycle connections every hour
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    AsyncAttrs enables async access to lazy-loaded relationships:
        patient = await session.get(Patient, 1)
        prescriptions = await patient.awaitable_attrs.prescriptions
    """

    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session per request.

    Session is automatically committed on success and rolled back on error.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
