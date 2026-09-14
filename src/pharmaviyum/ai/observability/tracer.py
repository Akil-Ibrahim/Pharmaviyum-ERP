"""
Unified Observability Tracer: OpenTelemetry + LangSmith.

Best practice 2026:
- OpenTelemetry for distributed tracing across microservices (FastAPI -> Agent -> DB)
- LangSmith for LLM-specific tracing (prompts, token usage, tool calls, evaluations)
- Async-friendly span management
- Automatic correlation ID propagation
"""
from __future__ import annotations
import os
import json
from typing import Any, Optional
from contextlib import contextmanager
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode
from langsmith import Client as LangSmithClient
from langsmith.run_helpers import traceable
from src.pharmaviyum.core.logging import logger


class ObservabilityTracer:
    """
    Production-ready tracer combining OpenTelemetry and LangSmith.
    
    Usage:
        tracer = ObservabilityTracer()
        
        with tracer.start_span("agent_execution", session_id="123"):
            # ... agent logic ...
            tracer.log_to_langsmith(run_name="pharmacist_agent", inputs=..., outputs=...)
    """
    
    def __init__(
        self,
        service_name: str = "pharmaviyum-ai",
        otel_endpoint: str | None = None,
        langsmith_api_key: str | None = None,
        langsmith_project: str = "pharmaviyum-pharmacist-agent",
    ):
        self.service_name = service_name
        
        # 1. Initialize OpenTelemetry
        self._init_otel(otel_endpoint)
        
        # 2. Initialize LangSmith
        self._init_langsmith(langsmith_api_key, langsmith_project)
        
        self.tracer = trace.get_tracer(service_name)
    
    def _init_otel(self, endpoint: str | None):
        """Initialize OpenTelemetry TracerProvider with OTLP exporter."""
        # Resource attributes for filtering in Grafana/Jaeger
        resource = Resource.create({
            "service.name": self.service_name,
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })
        
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        
        # Export to OpenTelemetry Collector (or directly to Jaeger/Datadog)
        otlp_endpoint = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
        
        try:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
            logger.info(f"OpenTelemetry initialized, exporting to {otlp_endpoint}")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry exporter: {e}")
    
    def _init_langsmith(self, api_key: str | None, project: str):
        """Initialize LangSmith client for LLM-specific tracing."""
        ls_key = api_key or os.getenv("LANGCHAIN_API_KEY")
        ls_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
        
        if ls_key:
            os.environ["LANGCHAIN_API_KEY"] = ls_key
            os.environ["LANGCHAIN_PROJECT"] = project
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            if ls_endpoint:
                os.environ["LANGCHAIN_ENDPOINT"] = ls_endpoint
            
            self.langsmith_client = LangSmithClient()
            logger.info(f"LangSmith initialized for project: {project}")
        else:
            self.langsmith_client = None
            logger.warning("LangSmith API key not found. LLM tracing disabled.")
    
    @contextmanager
    def start_span(self, name: str, **attributes):
        """
        Context manager for OpenTelemetry spans.
        
        Usage:
            with tracer.start_span("rag_retrieval", query_length=len(query)) as span:
                # do work
                span.set_attribute("retrieved_chunks", 5)
        """
        with self.tracer.start_as_current_span(name) as span:
            # Set initial attributes
            for key, value in attributes.items():
                span.set_attribute(key, str(value) if not isinstance(value, (bool, int, float)) else value)
            
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def log_to_langsmith(
        self,
        run_name: str,
        run_type: str = "llm",
        inputs: dict[str, Any],
        outputs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        session_id: str | None = None,
    ) -> str | None:
        """
        Log an execution to LangSmith.
        
        Returns:
            The LangSmith run ID (for linking with OpenTelemetry traces)
        """
        if not self.langsmith_client:
            return None
        
        try:
            # Create run
            run = self.langsmith_client.create_run(
                name=run_name,
                run_type=run_type,
                inputs=inputs,
                outputs=outputs,
                metadata=metadata or {},
                tags=tags or [],
                session_id=session_id,
            )
            
            logger.debug(f"Logged to LangSmith: {run_name} (ID: {run.id})")
            return str(run.id)
            
        except Exception as e:
            logger.error(f"Failed to log to LangSmith: {e}", exc_info=True)
            return None
    
    def log_tool_call(
        self,
        tool_name: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any] | str,
        latency_ms: float,
        success: bool,
        session_id: str | None = None,
    ):
        """Convenience method for logging MCP tool executions to LangSmith."""
        self.log_to_langsmith(
            run_name=f"tool_{tool_name}",
            run_type="tool",
            inputs=inputs,
            outputs={"result": outputs, "success": success},
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
    ):
        """Log evaluation results to LangSmith as a separate run or feedback."""
        if not self.langsmith_client:
            return
        
        try:
            # Log as an 'evaluator' run
            self.langsmith_client.create_run(
                name="agent_evaluation",
                run_type="evaluator",
                inputs={"query": query, "answer": answer},
                outputs=evaluation_result,
                tags=["evaluation", "llm_as_judge"],
                session_id=session_id,
            )
        except Exception as e:
            logger.error(f"Failed to log evaluation to LangSmith: {e}")


# Global singleton instance
tracer = ObservabilityTracer()
