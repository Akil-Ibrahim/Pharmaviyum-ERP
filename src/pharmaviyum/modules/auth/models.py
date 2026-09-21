"""
User and tenant authorization models.

Best practice:
- Explicit application role for MCP authorization
- Explicit user-to-pharmacy membership for tenant isolation
- No implicit privileged/system role at AI boundaries
"""

from datetime import datetime
from typing import Literal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...shared.core.database import Base
from src.pharmaviyum.models.user import User

UserRole = Literal["patient", "pharmacist", "admin", "system"]


class PharmacyMembership(Base):
    """Explicit user-to-pharmacy tenant membership."""

    __tablename__ = "pharmacy_memberships"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "pharmacy_id",
            name="uq_pharmacy_membership_user_pharmacy",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pharmacy_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
