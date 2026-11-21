"""Privacy regression tests for AI telemetry export boundaries."""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from opentelemetry.trace import Status, StatusCode

from src.pharmaviyum.ai.observability.tracer import ObservabilityTracer


def test_ai_span_names_and_attributes_are_allowlisted():
    span = MagicMock()
    tracer = ObservabilityTracer.__new__(ObservabilityTracer)

    @contextmanager
    def start_as_current_span(name):
        tracer.recorded_span_name = name
        yield span

    tracer.tracer = MagicMock()
    tracer.tracer.start_as_current_span.side_effect = start_as_current_span

    with tracer.start_span(
        "patient.lookup/123",
        **{
            "ai.model_name": "model-a",
            "patient.id": "patient-123",
            "ai.prompt": "sensitive clinical prompt",
            "ai.rag.source_count": 3,
        },
    ):
        pass

    assert tracer.recorded_span_name == "pharmaviyum.ai.operation"
    span.set_attribute.assert_any_call("ai.model_name", "model-a")
    span.set_attribute.assert_any_call("ai.rag.source_count", 3)
    attribute_names = {call.args[0] for call in span.set_attribute.call_args_list}
    assert "patient.id" not in attribute_names
    assert "ai.prompt" not in attribute_names


def test_ai_span_records_exception_type_without_exception_content():
    span = MagicMock()
    tracer = ObservabilityTracer.__new__(ObservabilityTracer)

    @contextmanager
    def start_as_current_span(_name):
        yield span

    tracer.tracer = MagicMock()
    tracer.tracer.start_as_current_span.side_effect = start_as_current_span

    with pytest.raises(RuntimeError, match="private clinical value"):
        with tracer.start_span("mortarium.agent.execute"):
            raise RuntimeError("private clinical value")

    span.set_attribute.assert_any_call("error.type", "RuntimeError")
    span.set_status.assert_any_call(Status(StatusCode.ERROR, "RuntimeError"))
    span.record_exception.assert_not_called()


def test_langsmith_export_uses_redacted_payload_and_allowlisted_metadata():
    client = MagicMock()
    tracer = ObservabilityTracer.__new__(ObservabilityTracer)
    tracer.langsmith_client = client
    tracer.include_content = False

    tracer.log_to_langsmith(
        run_name="patient-query-123",
        inputs={"query": "private clinical prompt"},
        outputs={"answer": "private clinical answer"},
        metadata={"latency_ms": 25, "patient_id": 123, "tenant": "pharmacy-7"},
        tags=["mcp_tool", "patient:123"],
        session_id="raw-session-id",
    )

    kwargs = client.create_run.call_args.kwargs
    assert kwargs["name"] == "pharmaviyum.ai.llm"
    assert kwargs["inputs"] == {"content_redacted": True, "field_count": 1}
    assert kwargs["outputs"] == {"content_redacted": True, "field_count": 1}
    assert kwargs["metadata"] == {"latency_ms": 25}
    assert kwargs["tags"] == ["mcp_tool"]
    assert "session_id" not in kwargs
