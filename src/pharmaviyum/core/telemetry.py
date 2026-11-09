"""
OpenTelemetry setup for distributed tracing.

The OTLP/protobuf stack can fail to import on Python 3.14 in some environments,
so we degrade gracefully instead of crashing the application during startup.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from src.pharmaviyum.core.config import settings

trace: Any
TracerProvider: Any
BatchSpanProcessor: Any
Resource: Any
FastAPIInstrumentor: Any
SQLAlchemyInstrumentor: Any
HTTPXClientInstrumentor: Any

try:
    from opentelemetry import trace
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    try:
        FastAPIInstrumentor = import_module(
            "opentelemetry.instrumentation.fastapi"
        ).FastAPIInstrumentor
    except Exception:
        FastAPIInstrumentor = None
except Exception:  # pragma: no cover - compatibility fallback for Python 3.14
    trace = None
    TracerProvider = None
    BatchSpanProcessor = None
    Resource = None
    FastAPIInstrumentor = None
    SQLAlchemyInstrumentor = None
    HTTPXClientInstrumentor = None


def _otlp_exporter_available() -> bool:
    """Return whether the OTLP exporter is importable in this runtime."""
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # type: ignore
            OTLPSpanExporter,
        )

        return OTLPSpanExporter is not None
    except Exception:
        return False


def setup_telemetry(app=None, engine=None) -> None:
    """
    Setup OpenTelemetry for the application.

    Args:
        app: FastAPI application instance
        engine: SQLAlchemy engine instance
    """
    if not settings.OTEL_ENABLED or trace is None:
        return

    try:
        resource = Resource.create(
            {
                "service.name": settings.OTEL_SERVICE_NAME,
                "service.version": settings.APP_VERSION,
                "deployment.environment": settings.ENVIRONMENT.value,
            }
        )

        provider = TracerProvider(resource=resource)

        if settings.OTEL_EXPORTER_ENDPOINT and _otlp_exporter_available():
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # type: ignore
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_ENDPOINT)
            provider.add_span_processor(
                BatchSpanProcessor(
                    exporter,
                    max_queue_size=2048,
                    schedule_delay_millis=5000,
                )
            )
        # Without an explicit OTLP endpoint, keep spans local and never emit
        # potentially sensitive telemetry to stdout through a console exporter.

        trace.set_tracer_provider(provider)

        if app and FastAPIInstrumentor is not None:
            FastAPIInstrumentor.instrument_app(app)

        if engine and SQLAlchemyInstrumentor is not None:
            SQLAlchemyInstrumentor().instrument(engine=engine)

        if HTTPXClientInstrumentor is not None:
            HTTPXClientInstrumentor().instrument()
    except Exception:
        return


def get_tracer(name: str) -> Any:
    """Get a tracer with the given name."""
    if trace is None:
        return None
    return trace.get_tracer(name)
