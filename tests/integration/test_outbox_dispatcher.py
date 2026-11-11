"""Integration coverage for durable, ordered Pharmacy Edge outbox delivery."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.pharmaviyum.config import settings
from src.pharmaviyum.models.outbox import OutboxEvent
from src.pharmaviyum.models.pharmacy import Pharmacy
from src.pharmaviyum.services.outbox import record_outbox_event
from src.pharmaviyum.services.outbox_dispatcher import dispatch_pending_outbox


def _configure_edge(monkeypatch, *, batch_size: int = 20) -> str:
    node_id = "7ec6b2b7-9e7c-4f4b-9f77-8b1d22b22e11"
    monkeypatch.setattr(settings, "PHARMAVIYUM_EDGE_NODE_ID", node_id)
    monkeypatch.setattr(
        settings, "PHARMAVIYUM_EDGE_TOKEN", "test-edge-token-value-123456"
    )
    monkeypatch.setattr(
        settings, "PHARMAVIYUM_CENTRAL_SYNC_URL", "https://central.example.test"
    )
    monkeypatch.setattr(settings, "PHARMAVIYUM_SYNC_BATCH_SIZE", batch_size)
    monkeypatch.setattr(settings, "PHARMAVIYUM_SYNC_LEASE_SECONDS", 30)
    monkeypatch.setattr(settings, "PHARMAVIYUM_SYNC_HTTP_TIMEOUT_SECONDS", 5.0)
    return node_id


async def _add_outbox_event(
    test_db,
    *,
    pharmacy_id: int,
    aggregate_id: str,
    aggregate_version: int,
    event_type: str = "pos.sale.created",
) -> OutboxEvent:
    return await record_outbox_event(
        test_db,
        pharmacy_id=pharmacy_id,
        event_type=event_type,
        aggregate_type="sale",
        aggregate_id=aggregate_id,
        aggregate_version=aggregate_version,
        payload={
            "sale_id": int(aggregate_id),
            "receipt_number": f"PV-{aggregate_id}",
            "sale_status": "completed",
        },
    )


@pytest.mark.integration
async def test_dispatcher_sends_envelope_and_marks_event_published(
    test_db, test_engine, monkeypatch
):
    node_id = _configure_edge(monkeypatch)
    pharmacy = Pharmacy(name="Dispatcher Pharmacy", code="DISPATCH-OK")
    test_db.add(pharmacy)
    await test_db.flush()
    event = await _add_outbox_event(
        test_db,
        pharmacy_id=pharmacy.id,
        aggregate_id="501",
        aggregate_version=1,
    )
    event_id = event.event_id
    await test_db.commit()

    received = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        received.append((request, body))
        return httpx.Response(
            202,
            json={
                "event_id": body["event_id"],
                "status": "accepted",
                "duplicate": False,
            },
        )

    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        delivered = await dispatch_pending_outbox(
            session_factory=factory,
            http_client=client,
        )

    assert delivered == 1
    assert len(received) == 1
    request, envelope = received[0]
    assert str(request.url) == "https://central.example.test/api/v1/sync/events"
    assert request.headers["X-Edge-Token"] == "test-edge-token-value-123456"
    assert envelope["edge_node_id"] == node_id
    assert envelope["pharmacy_id"] == pharmacy.id
    assert envelope["aggregate_id"] == "501"
    assert envelope["aggregate_version"] == 1
    assert envelope["event_id"] == event_id
    assert envelope["payload"]["sale_id"] == 501
    assert "event_id" not in envelope["payload"]

    async with factory() as session:
        stored = await session.scalar(
            select(OutboxEvent).where(OutboxEvent.event_id == event_id)
        )
        assert stored is not None
        assert stored.published_at is not None
        assert stored.lease_token is None
        assert stored.locked_until is None
        assert stored.last_error is None


@pytest.mark.integration
async def test_dispatcher_releases_failed_delivery_for_retry(
    test_db, test_engine, monkeypatch
):
    _configure_edge(monkeypatch)
    pharmacy = Pharmacy(name="Retry Pharmacy", code="DISPATCH-RETRY")
    test_db.add(pharmacy)
    await test_db.flush()
    event = await _add_outbox_event(
        test_db,
        pharmacy_id=pharmacy.id,
        aggregate_id="502",
        aggregate_version=1,
    )
    event_id = event.event_id
    await test_db.commit()

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "temporarily unavailable"})

    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        delivered = await dispatch_pending_outbox(
            session_factory=factory,
            http_client=client,
        )

    assert delivered == 0
    async with factory() as session:
        stored = await session.scalar(
            select(OutboxEvent).where(OutboxEvent.event_id == event_id)
        )
        assert stored is not None
        assert stored.published_at is None
        assert stored.lease_token is None
        assert stored.locked_until is None
        assert stored.attempts == 1
        assert stored.last_error == "Central delivery failed: HTTPStatusError"
        assert stored.available_at > datetime.now(timezone.utc)


@pytest.mark.integration
async def test_dispatcher_never_sends_later_aggregate_version_first(
    test_db, test_engine, monkeypatch
):
    _configure_edge(monkeypatch)
    pharmacy = Pharmacy(name="Ordering Pharmacy", code="DISPATCH-ORDER")
    test_db.add(pharmacy)
    await test_db.flush()
    first = await _add_outbox_event(
        test_db,
        pharmacy_id=pharmacy.id,
        aggregate_id="503",
        aggregate_version=1,
    )
    second = await _add_outbox_event(
        test_db,
        pharmacy_id=pharmacy.id,
        aggregate_id="503",
        aggregate_version=2,
        event_type="pos.sale.cancelled",
    )
    first_id = first.event_id
    second_id = second.event_id
    await test_db.commit()

    delivered_ids = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        delivered_ids.append(body["event_id"])
        return httpx.Response(
            202,
            json={
                "event_id": body["event_id"],
                "status": "accepted",
                "duplicate": False,
            },
        )

    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        first_batch = await dispatch_pending_outbox(
            session_factory=factory,
            http_client=client,
        )
        assert first_batch == 1
        assert delivered_ids == [first_id]

        second_batch = await dispatch_pending_outbox(
            session_factory=factory,
            http_client=client,
        )
        assert second_batch == 1
        assert delivered_ids == [first_id, second_id]

    async with factory() as session:
        rows = list(
            (
                await session.scalars(
                    select(OutboxEvent)
                    .where(OutboxEvent.event_id.in_([first_id, second_id]))
                    .order_by(OutboxEvent.aggregate_version.asc())
                )
            ).all()
        )
        assert len(rows) == 2
        assert all(row.published_at is not None for row in rows)


@pytest.mark.integration
async def test_expired_lease_fences_off_the_previous_worker(
    test_db, test_engine
):
    from datetime import timedelta

    from src.pharmaviyum.services.outbox_dispatcher import (
        _acknowledge_published,
        _claim_batch,
    )

    pharmacy = Pharmacy(name="Lease Fencing Pharmacy", code="DISPATCH-FENCE")
    test_db.add(pharmacy)
    await test_db.flush()
    event = await _add_outbox_event(
        test_db,
        pharmacy_id=pharmacy.id,
        aggregate_id="504",
        aggregate_version=1,
    )
    event.lease_token = "00000000-0000-0000-0000-000000000001"
    event.locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    event_id = event.event_id
    await test_db.commit()

    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    claimed = await _claim_batch(factory, batch_size=10, lease_seconds=30)
    assert len(claimed) == 1
    assert claimed[0].event_id == event_id
    assert claimed[0].lease_token != "00000000-0000-0000-0000-000000000001"
    assert claimed[0].attempts == 1

    stale_ack = await _acknowledge_published(
        factory,
        row_id=claimed[0].row_id,
        lease_token="00000000-0000-0000-0000-000000000001",
    )
    assert stale_ack is False

    async with factory() as session:
        stored = await session.scalar(
            select(OutboxEvent).where(OutboxEvent.event_id == event_id)
        )
        assert stored is not None
        assert stored.published_at is None
        assert stored.lease_token == claimed[0].lease_token
