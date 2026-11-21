from types import SimpleNamespace

import pytest

from src.pharmaviyum.ai.llm_utils import response_text, total_token_usage


def test_response_text_returns_plain_string_content():
    assert response_text(SimpleNamespace(content="Answer")) == "Answer"


def test_response_text_joins_gemini_text_blocks_and_skips_non_text_blocks():
    response = SimpleNamespace(
        content=[
            {"type": "text", "text": "First sentence."},
            {"type": "image", "data": "not user-facing text"},
            {"type": "text", "text": "Second sentence."},
        ]
    )

    assert response_text(response) == "First sentence.\nSecond sentence."


def test_response_text_rejects_content_without_text():
    with pytest.raises(ValueError, match="contained no text content"):
        response_text(SimpleNamespace(content=[{"type": "image", "data": "..."}]))


def test_response_text_rejects_unsupported_content_type():
    with pytest.raises(TypeError, match="must be text or text blocks"):
        response_text(SimpleNamespace(content={"text": "not a list"}))


def test_total_token_usage_sums_provider_usage_and_fallback_fields():
    usage_by_model = {
        "gemini-flash": {
            "input_tokens": 9,
            "output_tokens": 96,
            "total_tokens": 105,
        },
        "gemini-flash-lite": {"input_tokens": 10, "output_tokens": 20},
    }

    assert total_token_usage(usage_by_model) == 135


def test_total_token_usage_ignores_missing_or_malformed_usage():
    assert total_token_usage({"unknown": None, "bad": {"input_tokens": "9"}}) == 0
