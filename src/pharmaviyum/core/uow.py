"""
Unit of Work pattern for transaction management
Best practice 2026: Centralized transaction control
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.core.database import async_session
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class UnitOfWork:
    """
    Unit of Work for managing transactions

    Ensures atomic operations across multiple repositories.
    Implements context manager pattern for clean resource management.

    Usage:
        async with UnitOfWork() as uow:
            patient = await uow.patients.create(patient_data)
            prescription = await uow.prescriptions.create(prescription_data)
            await uow.commit()
    """

    def __init__(self):
        """Initialize Unit of Work"""
        self._session: Optional[AsyncSession] = None
        self._repositories = {}

    async def __aenter__(self):
        """Enter context manager - create session"""
        self._session = async_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - rollback on error, close session"""
        if exc_type is not None:
            # Exception occurred - rollback
            logger.error(
                "UnitOfWork rollback",
                extra={"exception": str(exc_val)},
            )
            await self.rollback()

        if self._session:
            await self._session.close()

    @property
    def session(self) -> AsyncSession:
        """Get current session"""
        if not self._session:
            raise RuntimeError(
                "UnitOfWork not initialized. Use 'async with UnitOfWork()'"
            )
        return self._session

    async def commit(self) -> None:
        """Commit transaction"""
        if not self._session:
            raise RuntimeError("UnitOfWork not initialized")

        try:
            await self._session.commit()
            logger.debug("UnitOfWork committed successfully")
        except Exception as e:
            logger.error(f"UnitOfWork commit failed: {e}")
            await self._session.rollback()
            raise

    async def rollback(self) -> None:
        """Rollback transaction"""
        if self._session:
            await self._session.rollback()
            logger.warning("UnitOfWork rolled back")

    async def refresh(self, entity) -> None:
        """Refresh entity from database"""
        if self._session:
            await self._session.refresh(entity)
