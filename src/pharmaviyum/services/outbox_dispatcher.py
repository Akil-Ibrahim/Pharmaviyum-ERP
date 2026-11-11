"""Reliable Pharmacy Edge outbox delivery to the Central Inbox."""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import aliased

from src.pharmaviyum.config import settings
from src.pharmaviyum.database import AsyncSessionLocal
from src.pharmaviyum.models.outbox import OutboxEvent

logger = logging.getLogger(__name__)

_EVENT_METADATA_KEYS = {
    "event_id",
    "event_type",
    "schema_version",
    "pharmacy_id",
    "occurred_at",
}


def _dispatcher_configuration() -> tuple[str, str, str] | None:
    """Return Edge credentials only when the node is fully enrolled/configured."""
    node_id = settings.PHARMAVIYUM_EDGE_NODE_ID
    token = settings.PHARMAVIYUM_EDGE_TOKEN
    central_url = settings.PHARMAVIYUM_CENTRAL_SYNC_URL
    if not node_id or not token or not central_url:
        return None
    return node_id, token, central_url.rstrip("/")


async def _claim_batch(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    batch_size: int,
    lease_seconds: int,
) -> list[tuple[int, str, str, int, str, int, str, int, datetime, dict[str, Any]]]:
    """Atomically lease the oldest eligible event per aggregate.

    SKIP LOCKED allows multiple dispatchers to claim disjoint work. The fencing
    token prevents an expired worker from acknowledging a lease acquired later.
    """
    now = datetime.now(timezone.utc)
    earlier = aliased(OutboxEvent)
    has_earlier_unpublished = exists(
        select(1).where(
            earlier.pharmacy_id == OutboxEvent.pharmacy_id,
            earlier.aggregate_type == OutboxEvent.aggregate_type,
            earlier.aggregate_id == OutboxEvent.aggregate_id,
            earlier.aggregate_version < OutboxEvent.aggregate_version,
            earlier.published_at.is_(None),
        )
    )

    async with session_factory() as session:
        async with session.begin():
            result = await session.scalars(
                select(OutboxEvent)
                .where(
                    OutboxEvent.published_at.is_(None),
                    OutboxEvent.available_at <= now,
                    (OutboxEvent.locked_until.is_(None))
                    | (OutboxEvent.locked_until <= now),
                    ~has_earlier_unpublished,
                )
                .order_by(OutboxEvent.created_at.asc(), OutboxEvent.id.asc())
                .limit(batch_size)
                .with_for_update(skip_locked=True)
            )
            events = list(result.all())
            claimed = []
            for event in events:
                lease_token = str(uuid4())
                event.lease_token = lease_token
                event.locked_until = now + timedelta(seconds=lease_seconds)
                event.attempts += 1
                claimed.append(
                    (
                        event.id,
                        event.event_id,
                        lease_token,
                        event.pharmacy_id,
                        event.event_type,
                        event.schema_version,
                        event.aggregate_type,
                        event.aggregate_version,
                        event.occurred_at,
                        dict(event.payload),
                    )
                )
        return claimed


def _event_envelope(
    event: tuple[int, str, str, int, str, int, str, int, datetime, dict[str, Any]],
    *,
    edge_node_id: str,
) -> dict[str, Any]:
    (
        _row_id,
        event_id,
        _lease_token,
        pharmacy_id,
        event_type,
        schema_version,
        aggregate_type,
        aggregate_version,
        occurred_at,
        stored_payload,
    ) = event
    payload = {
        key: value
        for key, value in stored_payload.items()
        if key not in _EVENT_METADATA_KEYS
    }
    return {
        "event_id": event_id,
        "edge_node_id": edge_node_id,
        "pharmacy_id": pharmacy_id,
        "event_type": event_type,
        "schema_version": schema_version,
        "aggregate_type": aggregate_type,
        "aggregate_id": str(stored_payload.get("sale_id", "")),
        "aggregate_version": aggregate_version,
        "occurred_at": occurred_at.isoformat(),
        "payload": payload,
    }


async def _release_for_retry(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    row_id: int,
    lease_token: str,
    attempts: int,
    error: str,
) -> bool:
    """Release only the lease still owned by this worker and schedule a retry."""
    now = datetime.now(timezone.utc)
    exponential = min(2 ** min(attempts, 12), 3600)
    delay_seconds = exponential + random.uniform(0, min(30, exponential * 0.2))
    async with session_factory() as session:
        async with session.begin():
            event = await session.scalar(
                select(OutboxEvent)
                .where(
                    OutboxEvent.id == row_id,
                    OutboxEvent.lease_token == lease_token,
                    OutboxEvent.published_at.is_(None),
                )
                .with_for_update()
            )
            if event is None:
                return False
            event.available_at = now + timedelta(seconds=delay_seconds)
            event.locked_until = None
            event.lease_token = None
            event.last_error = error[:1000]
            return True


async def _acknowledge_published(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    row_id: int,
    lease_token: str,
) -> bool:
    """Mark published only when the responding worker still owns the lease."""
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        async with session.begin():
            event = await session.scalar(
                select(OutboxEvent)
                .where(
                    OutboxEvent.id == row_id,
                    OutboxEvent.lease_token == lease_token,
                    OutboxEvent.published_at.is_(None),
                )
                .with_for_update()
            )
            if event is None:
                return False
            event.published_at = now
            event.locked_until = None
            event.lease_token = None
            event.last_error = None
            return True


async def dispatch_pending_outbox(
    *,
    session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
    http_client: httpx.AsyncClient | None = None,
) -> int:
    """Deliver a bounded batch; Central's durable acknowledgement is the boundary.

    A lost HTTP response is safe: the event is retried with the same event_id and
    Central Inbox deduplicates it. No business data is deleted from the outbox.
    """
    configuration = _dispatcher_configuration()
    if configuration is None:
        logger.info("sync_dispatcher_disabled_missing_edge_configuration")
        return 0

    edge_node_id, edge_token, central_url = configuration
    batch_size = max(1, min(settings.PHARMAVIYUM_SYNC_BATCH_SIZE, 500))
    lease_seconds = max(15, settings.PHARMAVIYUM_SYNC_LEASE_SECONDS)
    claimed = await _claim_batch(
        session_factory,
        batch_size=batch_size,
        lease_seconds=lease_seconds,
    )
    if not claimed:
        return 0

    owns_client = http_client is None
    client = http_client or httpx.AsyncClient(
        timeout=httpx.Timeout(settings.PHARMAVIYUM_SYNC_HTTP_TIMEOUT_SECONDS)
    )
    published = 0
    try:
        for event in claimed:
            (
                row_id,
                event_id,
                lease_token,
                _pharmacy_id,
                _event_type,
                _schema_version,
                _aggregate_type,
                aggregate_version,
                _occurred_at,
                _payload,
            ) = event
            try:
                response = await client.post(
                    f"{central_url}/api/v1/sync/events",
                    json=_event_envelope(event, edge_node_id=edge_node_id),
                    headers={"X-Edge-Token": edge_token},
                )
                response.raise_for_status()
                acknowledgement = response.json()
                if (
                    acknowledgement.get("status") != "accepted"
                    or acknowledgement.get("event_id") != event_id
                ):
                    raise ValueError("Central returned an invalid event acknowledgement")
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                await _release_for_retry(
                    session_factory,
                    row_id=row_id,
                    lease_token=lease_token,
                    attempts=aggregate_version,
                    error=f"Central delivery failed: {type(exc).__name__}",
                )
                logger.warning(
                    "sync_event_delivery_failed",
                    extra={"event_id": event_id, "error_type": type(exc).__name__},
                )
                continue

            if await _acknowledge_published(
                session_factory,
                row_id=row_id,
                lease_token=lease_token,
            ):
                published += 1
    finally:
        if owns_client:
            await client.aclose()
    return published


def run_outbox_dispatcher() -> int:
    """Sync entry point for Celery; reuses the worker's event loop."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Celery event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(dispatch_pending_outbox())
