"""
Event Bus for inter-module communication.

In modular monolith architecture, modules communicate via events,
not direct dependencies. This enables:
- Loose coupling between modules
- Easy extraction of modules into microservices
- Async processing of side effects
- Audit trail of all domain events
"""

from .bus import DomainEvent, event_bus
from .handlers import register_all_handlers

__all__ = ["event_bus", "DomainEvent", "register_all_handlers"]
