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

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from src.pharmaviyum.db.base import Base


class AuditLog(Base):
	__tablename__ = "audit_logs"

	id = Column(Integer, primary_key=True, index=True)

	# Actor who performed the action (can be null for system events)
	actor_id = Column(Integer, nullable=True, index=True)
	actor_type = Column(String(50), nullable=True)

	# Action metadata
	action = Column(String(100), nullable=False, index=True)
	entity = Column(String(100), nullable=False, index=True)
	entity_id = Column(Integer, nullable=True, index=True)

	# Optional structured diff or payload describing the change
	changes = Column(JSON, nullable=True)

	# Request metadata useful for auditing and security
	ip_address = Column(String(45), nullable=True)
	user_agent = Column(String(512), nullable=True)

	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

	def __repr__(self) -> str:  # pragma: no cover - simple debug helper
		return (
			f"<AuditLog id={self.id} action={self.action} entity={self.entity} "
			f"entity_id={self.entity_id} actor_id={self.actor_id} created_at={self.created_at}>"
		)


__all__ = ["AuditLog"]
