"""Unified OpenTelemetry and metadata-only LangSmith observability."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator, Literal

from langsmith import Client as LangSmithClient
from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode

from src.pharmaviyum.core.logging import logger

LangSmithRunType = Literal[
    "tool", "chain", "llm", "retriever", "embedding", "prompt", "parser"
]
_SAFE_METADATA_KEYS = {
    "model_name",
    "provider",
    "latency_ms",
    "cache_hit",
    "source_count",
    "tool_count",
    "retry_count",
    "status",
    "error_type",
    "accuracy",
    "safety",
    "completeness",
    "compliance",
    "overall_score",
}

_SAFE_SPAN_NAMES = {
    "mortarium.agent.execute",
    "mortarium.agent.stream",
    "mortarium.model_router.select",
    "mortarium.rag.retrieve",
    "mortarium.mcp.tool",
    "pharmaviyum.ai.operation",
}
_SAFE_SPAN_ATTRIBUTES = {
    "ai.model_name",
    "ai.rag.source_count",
    "ai.rag.rewrite_count",
    "ai.rag.retrieved_count",
    "ai.rag.graded_count",
    "ai.rag.warning_count",
    "ai.rag.input_source_count",
    "ai.tool_result_count",
    "ai.execution_success",
    "ai.stream.cancelled",
    "ai.history_length",
    "ai.safety_check_required",
    "mcp.tool_success",
    "latency_ms",
    "cache_hit",
    "error.type",
}


def _safe_span_name(name: str) -> str:
    """Keep span names static and low-cardinality."""
    return name if name in _SAFE_SPAN_NAMES else "pharmaviyum.ai.operation"


def _safe_span_attributes(
    attributes: dict[str, Any],
) -> dict[str, bool | int | float | str]:
    """Allow only reviewed, bounded operational span attributes."""
    return {
        key: value
        for key, value in attributes.items()
        if key in _SAFE_SPAN_ATTRIBUTES
        and isinstance(value, (bool, int, float, str))
        and (not isinstance(value, str) or len(value) <= 128)
    }


def _content_tracing_allowed() -> bool:
    environment = os.getenv("ENVIRONMENT", "").strip().lower()
    return environment in {"development", "test"}


class ObservabilityTracer:
    """Telemetry facade that excludes content and identifiers by default.

    Content tracing is permitted only as an explicit development-only opt-in.
    Production always forces LangChain automatic content tracing off.
    """

    def __init__(
        self,
        service_name: str = "pharmaviyum-ai",
        otel_endpoint: str | None = None,
        langsmith_api_key: str | None = None,
        langsmith_project: str = "pharmaviyum-pharmacist-agent",
    ):
        self.service_name = service_name
        requested_content = (
            os.getenv("AI_TELEMETRY_INCLUDE_CONTENT", "false").lower() == "true"
        )
        self.include_content = requested_content and _content_tracing_allowed()
        if requested_content and not self.include_content:
            logger.warning(
                "AI telemetry content export is forbidden in production; redaction enforced"
            )
        self._init_otel(otel_endpoint)
        self._init_langsmith(langsmith_api_key, langsmith_project)
        self.tracer = trace.get_tracer(service_name)

    def _init_otel(self, endpoint: str | None) -> None:
        """Use the application-owned OpenTelemetry provider.

        The FastAPI application configures one process-wide TracerProvider and
        OTLP exporter. Creating another provider here would cause duplicate or
        ignored global-provider registration depending on import order.
        """
        if os.getenv("OTEL_ENABLED", "false").lower() == "true":
            logger.info(
                "AI spans will use the application-managed OpenTelemetry provider"
            )
        else:
            logger.info("OpenTelemetry exporter disabled")

    def _init_langsmith(self, api_key: str | None, project: str) -> None:
        """Initialize manual LangSmith client without implicit content tracing."""
        ls_key = api_key or os.getenv("LANGCHAIN_API_KEY")
        if not ls_key:
            self.langsmith_client = None
            logger.info("LangSmith API key not found; tracing disabled")
            return

        os.environ["LANGCHAIN_API_KEY"] = ls_key
        os.environ["LANGCHAIN_PROJECT"] = project
        # Automatic LangChain callbacks export prompts/outputs. Keep them off
        # unless a developer explicitly opts in outside production.
        os.environ["LANGCHAIN_TRACING_V2"] = "true" if self.include_content else "false"
        endpoint = os.getenv("LANGCHAIN_ENDPOINT")
        if endpoint:
            os.environ["LANGCHAIN_ENDPOINT"] = endpoint
        try:
            self.langsmith_client = LangSmithClient()
            logger.info("LangSmith metadata client initialized")
        except Exception as exc:
            self.langsmith_client = None
            logger.warning(
                "LangSmith initialization failed",
                extra={"error_type": type(exc).__name__},
            )

    @contextmanager
    def start_span(self, name: str, **attributes: Any) -> Iterator[Span]:
        """Create a span; record only exception type, never exception content."""
        with self.tracer.start_as_current_span(_safe_span_name(name)) as span:
            for key, value in _safe_span_attributes(attributes).items():
                span.set_attribute(key, value)
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as exc:
                error_type = type(exc).__name__
                span.set_attribute("error.type", error_type)
                span.set_status(Status(StatusCode.ERROR, error_type))
                raise

    def _payload(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        """Return a bounded payload summary unless dev-only content opt-in is set."""
        if self.include_content:
            return payload or {}
        payload = payload or {}
        return {"content_redacted": True, "field_count": len(payload)}

    @staticmethod
    def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
        """Allow only low-risk operational scalar attributes."""
        safe: dict[str, Any] = {}
        for key, value in (metadata or {}).items():
            if key in _SAFE_METADATA_KEYS and isinstance(value, (bool, int, float)):
                safe[key] = value
            elif key in _SAFE_METADATA_KEYS and isinstance(value, str):
                safe[key] = value[:64]
        return safe

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
        """Log redacted payload summaries and allowlisted metadata only."""
        if not self.langsmith_client:
            return None
        try:
            self.langsmith_client.create_run(
                name=f"pharmaviyum.ai.{run_type}",
                run_type=run_type,
                inputs=self._payload(inputs),
                outputs=self._payload(outputs),
                metadata=self._safe_metadata(metadata),
                tags=[
                    tag
                    for tag in (tags or [])
                    if tag in {"mcp_tool", "evaluation", "llm_as_judge"}
                ],
                # Session identifiers are intentionally never exported.
            )
            return None
        except Exception as exc:
            logger.error(
                "LangSmith run export failed",
                extra={"error_type": type(exc).__name__},
            )
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
        """Log a tool outcome without payloads, tenant IDs or session IDs."""
        return self.log_to_langsmith(
            run_name="tool_execution",
            run_type="tool",
            inputs=inputs,
            outputs={"success": success},
            metadata={
                "latency_ms": latency_ms,
                "status": "success" if success else "error",
            },
            tags=["mcp_tool"],
        )

    def log_evaluation(
        self,
        query: str,
        answer: str,
        evaluation_result: dict[str, Any],
        session_id: str | None = None,
    ) -> None:
        """Log only evaluation scores; query and answer remain redacted."""
        if not self.langsmith_client:
            return
        self.log_to_langsmith(
            run_name="evaluation",
            run_type="chain",
            inputs={"query": query},
            outputs={"answer": answer, **evaluation_result},
            metadata=evaluation_result,
            tags=["evaluation", "llm_as_judge"],
        )


tracer = ObservabilityTracer()
