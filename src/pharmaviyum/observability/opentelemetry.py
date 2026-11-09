"""OpenTelemetry tracing setup for the Pharmaviyum application.

The SDK is optional at runtime: when no OTLP endpoint is configured, spans are
still created locally but are not exported. Instrumentation never blocks app
startup when an optional exporter cannot be initialized.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlsplit

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

from src.pharmaviyum.ai.config import settings
from src.pharmaviyum.database import engine

logger = logging.getLogger(__name__)

_provider: TracerProvider | None = None
_instrumented = False


def configure_opentelemetry(app: Any) -> TracerProvider | None:
    """Configure process-wide tracing and instrument application dependencies."""
    global _provider, _instrumented

    if not settings.otel.enabled:
        logger.info("OpenTelemetry is disabled")
        return None

    if _provider is None:
        resource = Resource.create(
            {
                "service.name": settings.otel.service_name,
                "service.version": "1.0.0",
                "deployment.environment.name": settings.environment,
            }
        )
        sampler = ParentBased(root=TraceIdRatioBased(settings.otel.sample_rate))
        provider = TracerProvider(resource=resource, sampler=sampler)

        endpoint = settings.otel.exporter_endpoint
        if endpoint:
            try:
                parsed_endpoint = urlsplit(endpoint)
                if parsed_endpoint.scheme in {"http", "https"}:
                    target = parsed_endpoint.netloc
                    insecure = parsed_endpoint.scheme == "http"
                else:
                    target = endpoint
                    insecure = False
                if not target:
                    raise ValueError("OTLP gRPC endpoint must include a host and port")
                provider.add_span_processor(
                    BatchSpanProcessor(
                        OTLPSpanExporter(endpoint=target, insecure=insecure)
                    )
                )
                logger.info("OpenTelemetry OTLP exporter configured")
            except Exception:
                # Observability must not prevent the pharmacy API from starting.
                logger.exception("OpenTelemetry exporter initialization failed")
        else:
            logger.warning(
                "OpenTelemetry is enabled without an OTLP endpoint; spans will "
                "not be exported. Set OTEL_EXPORTER_ENDPOINT or "
                "OTEL_EXPORTER_OTLP_ENDPOINT."
            )

        trace.set_tracer_provider(provider)
        _provider = provider

    if not _instrumented:
        instrumentations = (
            (
                "FastAPI",
                lambda: FastAPIInstrumentor.instrument_app(
                    app,
                    tracer_provider=_provider,
                    excluded_urls="health,ready,metrics,openapi.json,docs,redoc",
                ),
            ),
            (
                "SQLAlchemy",
                lambda: SQLAlchemyInstrumentor().instrument(
                    engine=engine.sync_engine,
                    tracer_provider=_provider,
                ),
            ),
            # Redis auto-instrumentation is deliberately omitted: db.statement
            # can contain command arguments, prompts, and clinical memory payloads.
            (
                "HTTPX",
                lambda: HTTPXClientInstrumentor().instrument(tracer_provider=_provider),
            ),
        )
        for name, instrument in instrumentations:
            try:
                instrument()
                logger.info("OpenTelemetry %s instrumentation enabled", name)
            except Exception:
                logger.exception("OpenTelemetry %s instrumentation setup failed", name)
        _instrumented = True
    return _provider


def shutdown_opentelemetry() -> None:
    """Flush and shut down the SDK provider during application shutdown."""
    global _provider, _instrumented

    if _provider is not None:
        try:
            _provider.force_flush(timeout_millis=5_000)
        except Exception:
            logger.exception("OpenTelemetry span flush failed")
        try:
            _provider.shutdown()
        except Exception:
            logger.exception("OpenTelemetry provider shutdown failed")
        _provider = None
        _instrumented = False
