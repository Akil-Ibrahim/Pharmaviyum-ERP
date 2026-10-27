"""In-process event dispatch for application-level notifications.

This bus is intentionally process-local. It is suitable for best-effort
notifications, not durable integration events or inventory transaction
coordination. Use a transactional outbox when delivery must survive restarts.
"""

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class Event(BaseModel):
    """Base event model shared by application event notifications."""

    event_type: str
    data: dict[str, Any]
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    correlation_id: str = ""


EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """Register and sequentially dispatch async handlers for event types.

    Handler failures are logged and isolated so remaining subscribers still run.
    This policy is appropriate only for best-effort in-process notifications;
    callers must not use this bus as proof that a business-critical event was
    durably delivered.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def on(self, event_type: str) -> Callable[[EventHandler], EventHandler]:
        """Register an async handler and return it unchanged."""

        def decorator(func: EventHandler) -> EventHandler:
            self._handlers.setdefault(event_type, []).append(func)
            return func

        return decorator

    async def emit(self, event: Event) -> None:
        """Dispatch to registered handlers sequentially."""
        handlers = self._handlers.get(event.event_type, [])

        if not handlers:
            logger.debug("No handlers for event: %s", event.event_type)
            return

        logger.info(
            "Emitting event: %s",
            event.event_type,
            extra={"handlers_count": len(handlers)},
        )

        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "Event handler failed",
                    extra={
                        "event_type": event.event_type,
                        "handler": getattr(handler, "__qualname__", type(handler).__name__),
                    },
                )


event_bus = EventBus()


class PatientCreatedEvent(Event):
    """Event emitted when a patient is created."""

    event_type: str = "patient.created"


class PatientUpdatedEvent(Event):
    """Event emitted when a patient is updated."""

    event_type: str = "patient.updated"


class PrescriptionCreatedEvent(Event):
    """Event emitted when a prescription is created."""

    event_type: str = "prescription.created"


class PrescriptionFilledEvent(Event):
    """Event emitted when a prescription is filled."""

    event_type: str = "prescription.filled"


class OrderCreatedEvent(Event):
    """Event emitted when an order is created."""

    event_type: str = "order.created"
