"""Cross-module event handler registration.

The current modular event bus does not expose legacy per-domain handler
modules under ``pharmaviyum.modules``. Keep registration explicit and
side-effect free until concrete handlers are introduced.
"""

from ..core.logging import logger


def register_all_handlers() -> None:
    """Register currently available domain event handlers.

    Domain handlers are intentionally registered by their owning service.
    This function remains as the application-level hook for future handlers
    without importing modules that are not part of the current architecture.
    """
    logger.debug("No application-level event handlers require registration")
