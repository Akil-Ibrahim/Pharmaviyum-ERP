"""Async repository primitives for SQLAlchemy models.

Repositories stage changes in the caller's session. Transaction ownership belongs
to the request dependency or Unit of Work, so multiple writes can be committed
or rolled back atomically by the application service.
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class AsyncRepository(Generic[T]):
    """Generic async CRUD repository that does not own transactions."""

    def __init__(self, model: type[Any], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, id: int) -> T | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        values: Sequence[T] = result.scalars().all()
        return list(values)

    async def add(self, obj: T) -> T:
        """Stage an insert/update; caller commits or rolls back the transaction."""
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: T) -> None:
        """Stage deletion without committing the caller's transaction."""
        await self.session.delete(obj)
        await self.session.flush()
