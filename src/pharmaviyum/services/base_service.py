"""Base service layer"""

from typing import Generic, TypeVar

T = TypeVar("T")


class BaseService(Generic[T]):
    """Base service class for business logic"""

    def __init__(self, repository):
        self.repository = repository

    async def get_by_id(self, obj_id: int) -> T:
        """Get object by ID"""
        obj = self.repository.get_by_id(obj_id)
        if not obj:
            raise ValueError(f"Object with id {obj_id} not found")
        return obj

    async def get_all(self, skip: int = 0, limit: int = 100):
        """Get all objects"""
        return self.repository.get_all(skip=skip, limit=limit)

    async def create(self, obj_in):
        """Create new object"""
        return self.repository.create(obj_in)

    async def update(self, obj_id: int, obj_in):
        """Update object"""
        obj = self.repository.update(obj_id, obj_in)
        if not obj:
            raise ValueError(f"Object with id {obj_id} not found")
        return obj

    async def delete(self, obj_id: int) -> bool:
        """Delete object"""
        return self.repository.delete(obj_id)
