"""Audit log ORM model.

This model captures immutable audit events for important operations in
the application. It is intentionally minimal and suitable for Postgres.

Fields:
 - actor_id/actor_type: who performed the action (user id or system)
 - action: short action verb (create/update/delete)
 - entity/entity_id: target resource identification
 - changes: optional structured JSON describing the change
 - ip_address/user_agent: request metadata
 - created_at: event timestamp
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from src.pharmaviyum.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Actor who performed the action (can be null for system events)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    actor_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Action metadata
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Optional structured diff or payload describing the change
    changes: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Request metadata useful for auditing and security
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - simple debug helper
        return (
            f"<AuditLog id={self.id} action={self.action} entity={self.entity} "
            f"entity_id={self.entity_id} actor_id={self.actor_id} created_at={self.created_at}>"
        )


__all__ = ["AuditLog"]
