"""Tests for the in-process application event bus."""

from datetime import datetime

import pytest

from src.pharmaviyum.services.event_bus import Event, EventBus, PatientCreatedEvent

pytestmark = pytest.mark.unit


def test_event_timestamp_is_created_by_model_default() -> None:
    before = datetime.now().astimezone()
    event = Event(event_type="example", data={})
    after = datetime.now().astimezone()

    timestamp = datetime.fromisoformat(event.timestamp)
    assert before <= timestamp <= after


def test_patient_event_uses_its_domain_event_type() -> None:
    event = PatientCreatedEvent(data={"patient_id": 42})

    assert event.event_type == "patient.created"
    assert event.data == {"patient_id": 42}


@pytest.mark.asyncio
async def test_event_bus_dispatches_handlers_in_registration_order() -> None:
    bus = EventBus()
    received: list[str] = []

    @bus.on("example")
    async def first(_event: Event) -> None:
        received.append("first")

    @bus.on("example")
    async def second(_event: Event) -> None:
        received.append("second")

    await bus.emit(Event(event_type="example", data={}))

    assert received == ["first", "second"]


@pytest.mark.asyncio
async def test_event_bus_continues_after_handler_failure() -> None:
    bus = EventBus()
    received: list[str] = []

    @bus.on("example")
    async def broken(_event: Event) -> None:
        raise RuntimeError("expected test failure")

    @bus.on("example")
    async def succeeding(_event: Event) -> None:
        received.append("succeeded")

    await bus.emit(Event(event_type="example", data={}))

    assert received == ["succeeded"]
