"""Utilities for normalizing language-model response content."""

from __future__ import annotations

from typing import Any


def response_text(response: Any) -> str:
    """Extract text from either plain-string or content-block model responses."""
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [
            block["text"]
            for block in content
            if isinstance(block, dict)
            and isinstance(block.get("text"), str)
            and block.get("type", "text") == "text"
        ]
        if text_parts:
            return "\n".join(text_parts)
        raise ValueError("Language model response contained no text content")
    raise TypeError("Language model response content must be text or text blocks")


def total_token_usage(usage_by_model: Any) -> int:
    """Sum provider-reported token usage across models in a callback result."""
    if not isinstance(usage_by_model, dict):
        return 0
    total = 0
    for usage in usage_by_model.values():
        if not isinstance(usage, dict):
            continue
        reported_total = usage.get("total_tokens")
        if isinstance(reported_total, int) and reported_total >= 0:
            total += reported_total
            continue
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        if (
            isinstance(input_tokens, int)
            and input_tokens >= 0
            and isinstance(output_tokens, int)
            and output_tokens >= 0
        ):
            total += input_tokens + output_tokens
    return total
