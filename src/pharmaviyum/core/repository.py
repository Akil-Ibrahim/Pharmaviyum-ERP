"""Generic async repository for SQLAlchemy 2.0 models."""

from typing import Any, Generic, TypeVar, cast

from sqlalchemy import delete, func, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Generic repository for async CRUD operations."""

    def __init__(self, model: type[Any], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> ModelType | None:
        """Get an entity by its integer primary key."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Any = None,
    ) -> list[ModelType]:
        """Get entities with pagination and optional ordering."""
        query = select(self.model)
        if order_by is not None:
            query = query.order_by(order_by)
        result = await self.session.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count(self, **filters: Any) -> int:
        """Count entities matching optional field/value filters."""
        query = select(func.count(self.model.id))
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, entity: ModelType) -> ModelType:
        """Persist a new entity and refresh generated fields."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        """Flush changes and refresh the entity."""
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: int) -> bool:
        """Delete an entity by primary key and report whether it existed."""
        result = cast(
            CursorResult[Any],
            await self.session.execute(delete(self.model).where(self.model.id == id)),
        )
        await self.session.flush()
        return result.rowcount > 0

    async def exists(self, **filters: Any) -> bool:
        """Check whether at least one entity matches the supplied filters."""
        query = select(func.count(self.model.id))
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        result = await self.session.execute(query)
        return result.scalar_one() > 0
