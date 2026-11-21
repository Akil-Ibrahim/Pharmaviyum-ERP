"""Compatibility facade for the single application-owned OpenTelemetry provider.

All provider creation, sampling, exporters and instrumentation are centralized in
src.pharmaviyum.observability.opentelemetry. This module creates no SDK objects
and never registers a second global TracerProvider.
"""

from __future__ import annotations

from typing import Any

from opentelemetry import trace

from src.pharmaviyum.observability.opentelemetry import (
    configure_opentelemetry,
    shutdown_opentelemetry,
)


def setup_telemetry(app: Any = None, engine: Any = None) -> None:
    """Delegate the legacy lifecycle entry point to the canonical provider.

    ``engine`` remains accepted for backwards compatibility. The canonical
    module owns database instrumentation and applies the environment/privacy
    policy before enabling it.
    """
    del engine
    configure_opentelemetry(app)


def get_tracer(name: str) -> Any:
    """Return a tracer backed by the process-wide application provider."""
    return trace.get_tracer(name)


__all__ = [
    "configure_opentelemetry",
    "get_tracer",
    "setup_telemetry",
    "shutdown_opentelemetry",
]
