"""
Global event handler registration.

This module imports all module-specific event handlers to register them
with the event bus. This is the single place where cross-module
event subscriptions are wired up.
"""

from ..core.logging import logger


def register_all_handlers() -> None:
    """Register all event handlers from all modules."""
    # Import module handlers to trigger registration
    # Each module registers its handlers at import time
    try:
        from ...modules.patients import events as patient_events  # noqa: F401

        logger.info("Patient event handlers registered")
    except ImportError:
        logger.warning("Patient module not available")

    try:
        from ...modules.prescriptions import \
            events as prescription_events  # noqa: F401

        logger.info("Prescription event handlers registered")
    except ImportError:
        logger.warning("Prescription module not available")

    try:
        from ...modules.orders import events as order_events  # noqa: F401

        logger.info("Order event handlers registered")
    except ImportError:
        logger.warning("Order module not available")

    try:
        from ...modules.notifications import \
            events as notification_events  # noqa: F401

        logger.info("Notification event handlers registered")
    except ImportError:
        logger.warning("Notification module not available")
