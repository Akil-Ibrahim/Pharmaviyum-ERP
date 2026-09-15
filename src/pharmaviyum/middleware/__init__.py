"""Middleware package helpers.

Provide a simple entrypoint to register common middleware used across
the application (auth, logging, error handling). Keep imports lazy to
avoid side-effects at import time.
"""

from typing import Any


def add_middleware(app: Any) -> None:
    """Register default middleware components on the FastAPI `app`.

    This function keeps middleware registration in one place so tests
    and application factories can opt-in or modify behavior easily.
    """
    # Import lazily to avoid heavy startup work during package import
    from src.pharmaviyum.middleware.auth_middleware import add_auth_middleware
    from src.pharmaviyum.middleware.error_handler import \
        register_exception_handlers
    from src.pharmaviyum.middleware.logging_middleware import \
        add_logging_middleware

    add_logging_middleware(app)
    add_auth_middleware(app)
    register_exception_handlers(app)


__all__ = ["add_middleware"]
