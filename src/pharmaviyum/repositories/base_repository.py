"""Base repository for data access layer"""

from typing import Generic, TypeVar, List, Optional, Type
from sqlalchemy.orm import Session
from sqlalchemy import select

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository class for CRUD operations"""

    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def create(self, obj_in: dict) -> T:
        """Create new object"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_id(self, obj_id: int) -> Optional[T]:
        """Get object by ID"""
        return self.db.query(self.model).filter(
            self.model.id == obj_id
        ).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all objects with pagination"""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def update(self, obj_id: int, obj_in: dict) -> Optional[T]:
        """Update object"""
        db_obj = self.get_by_id(obj_id)
        if db_obj:
            for key, value in obj_in.items():
                setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, obj_id: int) -> bool:
        """Delete object"""
        db_obj = self.get_by_id(obj_id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
