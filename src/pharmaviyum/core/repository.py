"""
Base repository pattern implementation
Best practice 2026: Abstraction over data access layer
"""

from typing import Any, Generic, Optional, Type, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository for CRUD operations

    Provides common database operations with type safety.
    All methods are async and use SQLAlchemy 2.0 style.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository with model and session

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get entity by ID

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None,
    ) -> list[ModelType]:
        """
        Get all entities with pagination

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            order_by: Order by clause

        Returns:
            List of entities
        """
        query = select(self.model)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, **filters) -> int:
        """
        Count entities with optional filters

        Args:
            **filters: Filter conditions

        Returns:
            Count of entities
        """
        query = select(func.count(self.model.id))

        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, entity: ModelType) -> ModelType:
        """
        Create new entity

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        """
        Update existing entity

        Args:
            entity: Entity to update

        Returns:
            Updated entity
        """
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: int) -> bool:
        """
        Delete entity by ID

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def exists(self, **filters) -> bool:
        """
        Check if entity exists with given filters

        Args:
            **filters: Filter conditions

        Returns:
            True if exists, False otherwise
        """
        query = select(func.count(self.model.id))

        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)

        result = await self.session.execute(query)
        return result.scalar_one() > 0
