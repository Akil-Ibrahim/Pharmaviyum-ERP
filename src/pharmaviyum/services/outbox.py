"""Helpers for recording durable integration events inside business transactions."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.models.outbox import OutboxEvent


async def record_outbox_event(
    session: AsyncSession,
    *,
    pharmacy_id: int,
    event_type: str,
    aggregate_type: str,
    aggregate_id: int | str,
    aggregate_version: int,
    payload: dict[str, Any],
) -> OutboxEvent:
    """Stage an immutable event; the caller owns the surrounding DB commit.

    This function deliberately does not commit or publish. If the business
    transaction rolls back, the outbox row rolls back with it.
    """
    event_id = str(uuid4())
    occurred_at = datetime.now(timezone.utc)
    event = OutboxEvent(
        event_id=event_id,
        pharmacy_id=pharmacy_id,
        event_type=event_type,
        schema_version=1,
        aggregate_type=aggregate_type,
        aggregate_id=str(aggregate_id),
        aggregate_version=aggregate_version,
        occurred_at=occurred_at,
        created_at=occurred_at,
        available_at=occurred_at,
        payload={
            **payload,
            "event_id": event_id,
            "event_type": event_type,
            "schema_version": 1,
            "pharmacy_id": pharmacy_id,
            "occurred_at": occurred_at.isoformat(),
        },
    )
    session.add(event)
    return event
