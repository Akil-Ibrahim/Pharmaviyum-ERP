"""
OpenTelemetry setup for distributed tracing.

The OTLP/protobuf stack can fail to import on Python 3.14 in some environments,
so we degrade gracefully instead of crashing the application during startup.
"""

from __future__ import annotations

from typing import Any

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
except Exception:  # pragma: no cover - compatibility fallback for Python 3.14
    trace = None
    TracerProvider = None
    BatchSpanProcessor = None
    ConsoleSpanExporter = None
    Resource = None
    FastAPIInstrumentor = None
    SQLAlchemyInstrumentor = None
    RedisInstrumentor = None
    HTTPXClientInstrumentor = None

from src.pharmaviyum.core.config import settings


def _otlp_exporter_available() -> bool:
    """Return whether the OTLP exporter is importable in this runtime."""
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore
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
        # Create resource with service info
        resource = Resource.create({
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.ENVIRONMENT.value,
        })

        # Create tracer provider
        provider = TracerProvider(resource=resource)

        # Add exporters
        if settings.OTEL_EXPORTER_ENDPOINT and _otlp_exporter_available():
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore

            exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_ENDPOINT)
        else:
            exporter = ConsoleSpanExporter()

        provider.add_span_processor(
            BatchSpanProcessor(
                exporter,
                max_queue_size=2048,
                schedule_delay_millis=5000,
            )
        )

        trace.set_tracer_provider(provider)

        # Instrument libraries
        if app and FastAPIInstrumentor is not None:
            FastAPIInstrumentor.instrument_app(app)

        if engine and SQLAlchemyInstrumentor is not None:
            SQLAlchemyInstrumentor().instrument(engine=engine)

        if RedisInstrumentor is not None:
            RedisInstrumentor().instrument()
        if HTTPXClientInstrumentor is not None:
            HTTPXClientInstrumentor().instrument()
    except Exception:
        # Best-effort telemetry: never fail the app startup because the tracing stack
        # is optional and the project must remain runnable on newer Python versions.
        return


def get_tracer(name: str) -> Any:
    """Get a tracer with the given name."""
    if trace is None:
        return None
    return trace.get_tracer(name)
