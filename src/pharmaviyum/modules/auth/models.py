"""
User domain model for authentication.

Based on ibrahimengpy/full-stack-fastapi-template structure.
Uses SQLAlchemy 2.0 Mapped[] type hints for type safety.

Security features:
- UUID primary key (prevents enumeration)
- Hashed passwords (bcrypt)
- is_active flag for soft-deletion
- is_superuser flag for admin privileges
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...shared.core.database import Base


class User(Base):
    """
    User entity for authentication and authorization.

    Fields:
        id: UUID primary key (non-sequential to prevent enumeration)
        email: Unique email address (used as username)
        hashed_password: Bcrypt-hashed password
        full_name: Display name
        is_active: False = account disabled (soft-delete)
        is_superuser: True = has all permissions
        created_at: Account creation timestamp
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
