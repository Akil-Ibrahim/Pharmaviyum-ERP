"""Unified OpenTelemetry and LangSmith observability tracer."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator, Literal

from langsmith import Client as LangSmithClient
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span, Status, StatusCode

from src.pharmaviyum.core.logging import logger


LangSmithRunType = Literal["tool", "chain", "llm", "retriever", "embedding", "prompt", "parser"]


class ObservabilityTracer:
    """Production tracer combining OpenTelemetry and LangSmith.

    AI prompts, answers and tool payloads are never exported by default because
    they may contain patient or other sensitive data. Content export requires
    explicit opt-in through ``AI_TELEMETRY_INCLUDE_CONTENT=true``.
    """

    def __init__(
        self,
        service_name: str = "pharmaviyum-ai",
        otel_endpoint: str | None = None,
        langsmith_api_key: str | None = None,
        langsmith_project: str = "pharmaviyum-pharmacist-agent",
    ):
        self.service_name = service_name
        self.include_content = (
            os.getenv("AI_TELEMETRY_INCLUDE_CONTENT", "false").lower() == "true"
        )
        self._init_otel(otel_endpoint)
        self._init_langsmith(langsmith_api_key, langsmith_project)
        self.tracer = trace.get_tracer(service_name)

    def _init_otel(self, endpoint: str | None) -> None:
        """Initialize OpenTelemetry with an optional OTLP exporter."""
        resource = Resource.create(
            {
                "service.name": self.service_name,
                "deployment.environment": os.getenv("ENVIRONMENT", "development"),
            }
        )
        provider = TracerProvider(resource=resource)
        try:
            trace.set_tracer_provider(provider)
        except Exception:
            pass

        otlp_endpoint = endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"
        )
        if os.getenv("OTEL_ENABLED", "false").lower() != "true":
            logger.info("OpenTelemetry exporter disabled")
            return
        try:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OpenTelemetry initialized")
        except Exception as exc:
            logger.warning("Failed to initialize OpenTelemetry exporter: %s", exc)

    def _init_langsmith(self, api_key: str | None, project: str) -> None:
        """Initialize LangSmith tracing only when explicitly configured."""
        ls_key = api_key or os.getenv("LANGCHAIN_API_KEY")
        if not ls_key:
            self.langsmith_client = None
            logger.info("LangSmith API key not found; LLM tracing disabled")
            return

        os.environ["LANGCHAIN_API_KEY"] = ls_key
        os.environ["LANGCHAIN_PROJECT"] = project
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        endpoint = os.getenv("LANGCHAIN_ENDPOINT")
        if endpoint:
            os.environ["LANGCHAIN_ENDPOINT"] = endpoint
        try:
            self.langsmith_client = LangSmithClient()
            logger.info("LangSmith initialized")
        except Exception as exc:
            self.langsmith_client = None
            logger.warning("Failed to initialize LangSmith client: %s", exc)

    @contextmanager
    def start_span(self, name: str, **attributes: Any) -> Iterator[Span]:
        """Create an OpenTelemetry span and record failures."""
        with self.tracer.start_as_current_span(name) as span:
            for key, value in attributes.items():
                span.set_attribute(
                    key,
                    value if isinstance(value, (bool, int, float, str)) else str(value),
                )
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as exc:
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                span.record_exception(exc)
                raise

    def _payload(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        """Return telemetry-safe payload metadata unless content export is opted in."""
        if self.include_content:
            return payload or {}
        payload = payload or {}
        return {"content_redacted": True, "field_count": len(payload)}

    def log_to_langsmith(
        self,
        run_name: str,
        inputs: dict[str, Any],
        run_type: LangSmithRunType = "llm",
        outputs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        session_id: str | None = None,
    ) -> str | None:
        """Log execution metadata without exporting sensitive content by default."""
        if not self.langsmith_client:
            return None
        try:
            run = self.langsmith_client.create_run(
                name=run_name,
                run_type=run_type,
                inputs=self._payload(inputs),
                outputs=self._payload(outputs),
                metadata=metadata or {},
                tags=tags or [],
                session_id=session_id,
            )
            run_id = getattr(run, "id", None)
            return str(run_id) if run_id is not None else None
        except Exception as exc:
            logger.error("Failed to log to LangSmith: %s", exc, exc_info=True)
            return None

    def log_tool_call(
        self,
        tool_name: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any] | str,
        latency_ms: float,
        success: bool,
        session_id: str | None = None,
    ) -> str | None:
        """Log an MCP tool execution without exporting tool payloads by default."""
        output_payload = outputs if isinstance(outputs, dict) else {"result": outputs}
        return self.log_to_langsmith(
            run_name=f"tool_{tool_name}",
            run_type="tool",
            inputs=inputs,
            outputs={"result": output_payload, "success": success},
            metadata={"latency_ms": latency_ms},
            tags=["mcp_tool", tool_name],
            session_id=session_id,
        )

    def log_evaluation(
        self,
        query: str,
        answer: str,
        evaluation_result: dict[str, Any],
        session_id: str | None = None,
    ) -> None:
        """Log evaluation metadata without exporting query/answer by default."""
        if not self.langsmith_client:
            return
        try:
            self.langsmith_client.create_run(
                name="agent_evaluation",
                run_type="chain",
                inputs=self._payload({"query": query}),
                outputs=self._payload({"answer": answer, **evaluation_result}),
                tags=["evaluation", "llm_as_judge"],
                session_id=session_id,
            )
        except Exception as exc:
            logger.error("Failed to log evaluation to LangSmith: %s", exc)


tracer = ObservabilityTracer()
