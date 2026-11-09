"""Tests for OpenTelemetry configuration used by the API process."""

from __future__ import annotations

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


def test_telemetry_does_not_enable_sensitive_redis_or_console_exporters():
    from src.pharmaviyum.core import telemetry as legacy_telemetry
    from src.pharmaviyum.observability import opentelemetry as app_telemetry

    assert not hasattr(legacy_telemetry, "RedisInstrumentor")
    assert not hasattr(legacy_telemetry, "ConsoleSpanExporter")
    assert not hasattr(app_telemetry, "RedisInstrumentor")
