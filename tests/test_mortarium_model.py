import sys
from pathlib import Path

import pytest
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mortarium-ai"))

from config import settings
from core.model import MockLLM, load_qwen_model


class StructuredMockSchema(BaseModel):
    is_relevant: bool
    rewritten_query: str


def test_load_qwen_model_falls_back_to_mock_when_missing(tmp_path, monkeypatch):
    missing_path = tmp_path / "missing-model"
    monkeypatch.setattr(settings, "MODEL_PATH", missing_path)

    llm = load_qwen_model()

    assert isinstance(llm, MockLLM)
    response = llm.invoke("hello")
    assert hasattr(response, "content")
    assert "Mock response" in response.content


def test_mock_llm_with_structured_output_returns_schema_object():
    llm = MockLLM().with_structured_output(StructuredMockSchema)
    result = llm.invoke({"question": "hello"})

    assert isinstance(result, StructuredMockSchema)
    assert result.is_relevant is False
    assert result.rewritten_query == "hello"


def test_load_qwen_model_uses_first_gguf_in_directory(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    (model_dir / "first.gguf").write_text("dummy")
    (model_dir / "second.gguf").write_text("dummy")

    monkeypatch.setattr(settings, "MODEL_PATH", model_dir)
    monkeypatch.setattr("core.model.LlamaCpp", lambda *args, **kwargs: "llm-loaded")

    llm = load_qwen_model()

    assert llm == "llm-loaded"
