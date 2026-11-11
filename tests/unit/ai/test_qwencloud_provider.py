from pydantic import SecretStr
import pytest

from src.pharmaviyum.ai import dependencies
from src.pharmaviyum.ai.config import QwenSettings


def test_qwen_settings_default_to_demo_model_and_free_only() -> None:
    settings = QwenSettings(_env_file=None)
    assert settings.model == "qwen3.8-flash"
    assert settings.free_quota_only is False
    assert settings.base_url.endswith("/compatible-mode/v1")


def test_qwencloud_builds_openai_compatible_chat_model(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_chat_openai(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(dependencies, "ChatOpenAI", fake_chat_openai)
    monkeypatch.setattr(dependencies.settings, "use_cloud_llm", True)
    monkeypatch.setattr(dependencies.settings, "cloud_llm_provider", "qwencloud")
    monkeypatch.setattr(
        dependencies.settings.qwen, "api_key", SecretStr("test-secret")
    )
    monkeypatch.setattr(dependencies.settings.qwen, "free_quota_only", True)

    result = dependencies._build_llm("qwen3.8-flash")

    assert result is not None
    assert captured["model"] == "qwen3.8-flash"
    assert captured["api_key"] == "test-secret"
    assert captured["base_url"] == dependencies.settings.qwen.base_url
    assert captured["max_retries"] == 0
    assert captured["max_tokens"] == dependencies.settings.qwen.max_output_tokens
    assert captured["stream_usage"] is True
    assert captured["callbacks"][0].model_name == "qwen3.8-flash"


def test_qwencloud_fails_closed_without_api_key(monkeypatch) -> None:
    monkeypatch.setattr(dependencies.settings, "use_cloud_llm", True)
    monkeypatch.setattr(dependencies.settings, "cloud_llm_provider", "qwencloud")
    monkeypatch.setattr(dependencies.settings.qwen, "api_key", None)

    with pytest.raises(RuntimeError, match="QWEN_API_KEY"):
        dependencies._build_llm("qwen3.8-flash")


def test_qwencloud_fails_closed_when_paid_usage_is_allowed(monkeypatch) -> None:
    monkeypatch.setattr(dependencies.settings, "use_cloud_llm", True)
    monkeypatch.setattr(dependencies.settings, "cloud_llm_provider", "qwencloud")
    monkeypatch.setattr(
        dependencies.settings.qwen, "api_key", SecretStr("test-secret")
    )
    monkeypatch.setattr(dependencies.settings.qwen, "free_quota_only", False)

    with pytest.raises(RuntimeError, match="paid usage is disabled"):
        dependencies._build_llm("qwen3.8-flash")
