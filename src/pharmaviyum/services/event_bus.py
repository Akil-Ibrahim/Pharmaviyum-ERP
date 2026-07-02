"""
Event bus for asynchronous event processing
Best practice 2026: Decoupled architecture via events
"""
from typing import Callable, Any, Dict, List
from datetime import datetime, timezone
from pydantic import BaseModel
from src.pharmaviyum.core.logging import get_logger

logger = get_logger(__name__)


class Event(BaseModel):
    """Base event model"""
    event_type: str
    data: Dict[str, Any]
    timestamp: str = ""
    correlation_id: str = ""
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class EventBus:
    """
    In-memory event bus for domain events
    
    Supports:
    - Event publishing
    - Event subscription
    - Async event handlers
    - Error handling per handler
    
    Usage:
        event_bus = EventBus()
        
        @event_bus.on("patient.created")
        async def send_welcome_email(event: Event):
            ...
        
        await event_bus.emit(Event(
            event_type="patient.created",
            data={"patient_id": 123}
        ))
    """
    
    def __init__(self):
        """Initialize event bus"""
        self._handlers: Dict[str, List[Callable]] = {}
    
    def on(self, event_type: str):
        """
        Decorator to register event handler
        
        Usage:
            @event_bus.on("patient.created")
            async def handler(event: Event):
                ...
        """
        def decorator(func: Callable):
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(func)
            return func
        return decorator
    
    async def emit(self, event: Event) -> None:
        """
        Emit event to all registered handlers
        
        Args:
            event: Event to emit
        """
        handlers = self._handlers.get(event.event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers for event: {event.event_type}")
            return
        
        logger.info(
            f"Emitting event: {event.event_type}",
            extra={"handlers_count": len(handlers)},
        )
        
        # Execute all handlers
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"Event handler error: {e}",
                    extra={
                        "event_type": event.event_type,
                        "handler": handler.__name__,
                    },
                    exc_info=True,
                )


# Singleton instance
event_bus = EventBus()


# Domain events
class PatientCreatedEvent(Event):
    """Event emitted when patient is created"""
    event_type: str = "patient.created"


class PatientUpdatedEvent(Event):
    """Event emitted when patient is updated"""
    event_type: str = "patient.updated"


class PrescriptionCreatedEvent(Event):
    """Event emitted when prescription is created"""
    event_type: str = "prescription.created"


class PrescriptionFilledEvent(Event):
    """Event emitted when prescription is filled"""
    event_type: str = "prescription.filled"


class OrderCreatedEvent(Event):
    """Event emitted when order is created"""
    event_type: str = "order.created"
