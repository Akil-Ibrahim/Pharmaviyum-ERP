"""
In-memory event bus for publishing and subscribing to domain events.

Each module can:
- Publish events (e.g., PatientCreated, PrescriptionFilled)
- Subscribe to events from other modules (without importing them)

In microservices, this would be replaced with Kafka/RabbitMQ.
"""
import asyncio
from typing import Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from ..core.logging import logger


@dataclass
class DomainEvent:
    """Base class for all domain events."""
    event_type: str
    data: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: str = ""
    source_module: str = ""


class EventBus:
    """In-memory event bus for domain events."""
    
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}
    
    def on(self, event_type: str):
        """Decorator to register an event handler."""
        def decorator(func: Callable):
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(func)
            return func
        return decorator
    
    async def emit(self, event: DomainEvent) -> None:
        """Emit an event to all registered handlers."""
        handlers = self._handlers.get(event.event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers for event: {event.event_type}")
            return
        
        logger.info(
            f"Emitting event: {event.event_type}",
            extra={"source_module": event.source_module, "handlers": len(handlers)},
        )
        
        # Execute handlers (in production: use background tasks)
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"Event handler failed: {e}",
                    extra={"event_type": event.event_type, "handler": handler.__name__},
                    exc_info=True,
                )


# Singleton instance
event_bus = EventBus()
