from __future__ import annotations

import pytest

from src.pharmaviyum.ai.optimization.token_budget import (
    TokenBudget,
    TokenBudgetExceeded,
    TokenBudgetManager,
)


def test_exact_tokenizer_is_used_when_available() -> None:
    manager = TokenBudgetManager(
        budget=TokenBudget(max_input_tokens=100, safety_margin_tokens=10),
        tokenizer=lambda text: len(text.split()),
    )
    result = manager.check_input("one two three")
    assert result.value == 3
    assert result.is_estimate is False


def test_fallback_count_is_explicitly_an_estimate() -> None:
    result = TokenBudgetManager().count("a" * 30)
    assert result.value == 30
    assert result.is_estimate is True


def test_over_budget_prompt_is_rejected_not_truncated() -> None:
    manager = TokenBudgetManager(
        budget=TokenBudget(max_input_tokens=20, safety_margin_tokens=2),
        tokenizer=lambda text: 19,
    )
    with pytest.raises(TokenBudgetExceeded, match="Clinical evidence was not truncated"):
        manager.check_input("clinical evidence")
