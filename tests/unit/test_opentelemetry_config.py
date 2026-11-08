"""Tests for OpenTelemetry configuration used by the API process."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.pharmaviyum.ai.config import OTelSettings


def test_otel_settings_accept_standard_otlp_endpoint(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OTEL_ENABLED", "true")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://otel.example.com:4317")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "pharmaviyum-api")
    monkeypatch.setenv("OTEL_SAMPLE_RATE", "0.25")

    settings = OTelSettings(_env_file=None)

    assert settings.enabled is True
    assert settings.exporter_endpoint == "https://otel.example.com:4317"
    assert settings.service_name == "pharmaviyum-api"
    assert settings.sample_rate == 0.25


def test_otel_settings_accept_legacy_endpoint_name(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OTEL_EXPORTER_ENDPOINT", "http://collector:4317")

    settings = OTelSettings(_env_file=None)

    assert settings.exporter_endpoint == "http://collector:4317"


def test_otel_sampling_rate_is_bounded():
    with pytest.raises(ValueError):
        OTelSettings(sample_rate=1.1)


def test_agent_harness_trace_id_uses_active_w3c_trace():
    from opentelemetry.sdk.trace import TracerProvider

    from src.pharmaviyum.ai.harness.agent_harness import _current_trace_id

    provider = TracerProvider()
    tracer = provider.get_tracer("test")
    with tracer.start_as_current_span("request") as span:
        expected = f"{span.get_span_context().trace_id:032x}"
        assert _current_trace_id() == expected
    provider.shutdown()


def test_otel_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OTEL_ENABLED", raising=False)

    settings = OTelSettings(_env_file=None)

    assert settings.enabled is False


def test_sensitive_client_spans_are_opt_in_and_never_enabled_in_production():
    from src.pharmaviyum.observability.opentelemetry import (
        _allow_sensitive_client_instrumentation,
    )

    assert _allow_sensitive_client_instrumentation("development", True) is True
    assert _allow_sensitive_client_instrumentation("development", False) is False
    assert _allow_sensitive_client_instrumentation("production", True) is False
    assert _allow_sensitive_client_instrumentation("prod", True) is False


def test_custom_span_attributes_are_allowlisted():
    from src.pharmaviyum.ai.observability.tracer import ObservabilityTracer

    span = MagicMock()
    span_context = MagicMock()
    span_context.__enter__.return_value = span
    tracer = MagicMock()
    tracer.start_as_current_span.return_value = span_context
    observability = ObservabilityTracer.__new__(ObservabilityTracer)
    observability.tracer = tracer

    with observability.start_span(
        "mortarium.test",
        **{
            "ai.rag.source_count": 3,
            "ai.model_name": "test-model",
            "patient.id": 123,
            "prompt": "sensitive clinical query",
        },
    ):
        pass

    recorded = {call.args[0] for call in span.set_attribute.call_args_list}
    assert recorded == {"ai.rag.source_count", "ai.model_name"}
