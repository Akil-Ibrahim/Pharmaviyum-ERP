"""
OpenTelemetry setup for distributed tracing
Best practice 2026: Observability is mandatory
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from src.pharmaviyum.core.config import settings


def setup_telemetry(app=None, engine=None) -> None:
    """
    Setup OpenTelemetry for the application
    
    Args:
        app: FastAPI application instance
        engine: SQLAlchemy engine instance
    """
    if not settings.OTEL_ENABLED:
        return
    
    # Create resource with service info
    resource = Resource.create({
        "service.name": settings.OTEL_SERVICE_NAME,
        "service.version": settings.APP_VERSION,
        "deployment.environment": settings.ENVIRONMENT.value,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Add exporters
    if settings.OTEL_EXPORTER_ENDPOINT:
        # Production: send to OTLP collector (Jaeger, Tempo, etc)
        exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_ENDPOINT)
    else:
        # Development: console output
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
    if app:
        FastAPIInstrumentor.instrument_app(app)
    
    if engine:
        SQLAlchemyInstrumentor().instrument(engine=engine)
    
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer with the given name"""
    return trace.get_tracer(name)
