"""OpenTelemetry tracing setup for the Pharmaviyum application.

The SDK is optional at runtime: when no OTLP endpoint is configured, spans are
still created locally but are not exported. Instrumentation never blocks app
startup when an optional exporter cannot be initialized.
"""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlsplit

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
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


def _is_production_environment(environment: str) -> bool:
    """Recognize production aliases consistently across telemetry policies."""
    return environment.strip().lower() in {"production", "prod"}


def _allow_sensitive_client_instrumentation(
    environment: str, explicitly_enabled: bool
) -> bool:
    """Sensitive SQL/Redis/HTTP client spans are development-only opt-ins."""
    return explicitly_enabled and environment.strip().lower() in {
        "development",
        "test",
    }


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
                environment = str(
                    getattr(settings.environment, "value", settings.environment)
                ).lower()
                if parsed_endpoint.scheme in {"http", "https"}:
                    target = parsed_endpoint.netloc
                    insecure = parsed_endpoint.scheme == "http"
                    if insecure and (
                        _is_production_environment(environment)
                        or parsed_endpoint.hostname
                        not in {"localhost", "127.0.0.1", "::1", "otel-collector"}
                    ):
                        raise ValueError(
                            "Production and non-local OTLP export require HTTPS"
                        )
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
            except Exception as exc:
                # Observability must not prevent the pharmacy API from starting.
                logger.error(
                    "OpenTelemetry exporter initialization failed",
                    extra={"error_type": type(exc).__name__},
                )
        else:
            logger.warning(
                "OpenTelemetry is enabled without an OTLP endpoint; spans will "
                "not be exported. Set OTEL_EXPORTER_ENDPOINT or "
                "OTEL_EXPORTER_OTLP_ENDPOINT."
            )

        trace.set_tracer_provider(provider)
        _provider = provider

    if not _instrumented:
        instrumentations = [
            (
                "FastAPI",
                lambda: FastAPIInstrumentor.instrument_app(
                    app,
                    tracer_provider=_provider,
                    excluded_urls="health,ready,metrics,openapi.json,docs,redoc",
                ),
            )
        ]

        environment = (
            str(getattr(settings.environment, "value", settings.environment))
            .strip()
            .lower()
        )
        allow_sensitive_client_spans = _allow_sensitive_client_instrumentation(
            environment,
            os.getenv("OTEL_ENABLE_SENSITIVE_CLIENT_INSTRUMENTATION", "false").lower()
            == "true",
        )
        if allow_sensitive_client_spans:
            instrumentations.extend(
                [
                    (
                        "SQLAlchemy",
                        lambda: SQLAlchemyInstrumentor().instrument(
                            engine=engine.sync_engine,
                            tracer_provider=_provider,
                        ),
                    ),
                    (
                        "Redis",
                        lambda: RedisInstrumentor().instrument(
                            tracer_provider=_provider
                        ),
                    ),
                    (
                        "HTTPX",
                        lambda: HTTPXClientInstrumentor().instrument(
                            tracer_provider=_provider
                        ),
                    ),
                ]
            )
        else:
            logger.info(
                "SQLAlchemy, Redis and HTTPX auto-instrumentation disabled by "
                "telemetry privacy policy"
            )

        for name, instrument in instrumentations:
            try:
                instrument()
                logger.info("OpenTelemetry %s instrumentation enabled", name)
            except Exception as exc:
                logger.error(
                    "OpenTelemetry instrumentation setup failed",
                    extra={"instrumentation": name, "error_type": type(exc).__name__},
                )
        _instrumented = True
    return _provider


def shutdown_opentelemetry() -> None:
    """Flush and shut down the SDK provider during application shutdown."""
    global _provider, _instrumented

    if _provider is not None:
        try:
            _provider.force_flush(timeout_millis=5_000)
        except Exception as exc:
            logger.error(
                "OpenTelemetry span flush failed",
                extra={"error_type": type(exc).__name__},
            )
        try:
            _provider.shutdown()
        except Exception as exc:
            logger.error(
                "OpenTelemetry provider shutdown failed",
                extra={"error_type": type(exc).__name__},
            )
        _provider = None
        _instrumented = False
