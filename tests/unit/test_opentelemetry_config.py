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