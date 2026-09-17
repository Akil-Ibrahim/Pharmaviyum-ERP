"""Base repository for the synchronous data access layer."""

from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic CRUD repository for synchronous SQLAlchemy sessions."""

    def __init__(self, db: Session, model: type[Any]):
        self.db = db
        self.model = model

    def create(self, obj_in: dict[str, Any]) -> T:
        """Create and persist a new object."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_id(self, obj_id: int) -> T | None:
        """Get an object by its integer primary key."""
        return self.db.query(self.model).filter(self.model.id == obj_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Get all objects with pagination."""
        return list(self.db.query(self.model).offset(skip).limit(limit).all())

    def update(self, obj_id: int, obj_in: dict[str, Any]) -> T | None:
        """Update an existing object."""
        db_obj = self.get_by_id(obj_id)
        if db_obj:
            for key, value in obj_in.items():
                setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, obj_id: int) -> bool:
        """Delete an object by its integer primary key."""
        db_obj = self.get_by_id(obj_id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
