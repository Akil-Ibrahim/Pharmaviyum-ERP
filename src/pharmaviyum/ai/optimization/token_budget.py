"""Provider-agnostic input token budgeting for Mortarium AI.

Exact counts require a tokenizer for the selected model. When unavailable, the
manager uses a conservative character-based estimate and exposes that fact.
It never silently truncates clinical evidence to fit a budget.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class TokenBudgetExceeded(ValueError):
    """Raised when a prompt exceeds its configured input-token budget."""


@dataclass(frozen=True, slots=True)
class TokenCount:
    value: int
    is_estimate: bool


@dataclass(frozen=True, slots=True)
class TokenBudget:
    max_input_tokens: int = 6000
    max_output_tokens: int = 500
    safety_margin_tokens: int = 256

    def __post_init__(self) -> None:
        if self.max_input_tokens < 1 or self.max_output_tokens < 1:
            raise ValueError("Token budgets must be positive")
        if self.safety_margin_tokens < 0:
            raise ValueError("Token safety margin cannot be negative")
        if self.safety_margin_tokens >= self.max_input_tokens:
            raise ValueError("Token safety margin must be smaller than input budget")


class TokenBudgetManager:
    """Preflight prompts without discarding source evidence or safety warnings."""

    def __init__(
        self,
        budget: TokenBudget | None = None,
        tokenizer: Callable[[str], int] | None = None,
    ) -> None:
        self.budget = budget or TokenBudget()
        self.tokenizer = tokenizer

    def count(self, text: str) -> TokenCount:
        if self.tokenizer is not None:
            try:
                return TokenCount(max(0, int(self.tokenizer(text))), False)
            except Exception:
                # A tokenizer failure must not break requests or masquerade as exact.
                pass
        # One token per character is deliberately conservative for multilingual text.
        # This is a planning bound, not an authoritative tokenizer result.
        return TokenCount(len(text), True)

    def check_input(self, prompt: str) -> TokenCount:
        count = self.count(prompt)
        effective_limit = (
            self.budget.max_input_tokens - self.budget.safety_margin_tokens
        )
        if count.value > effective_limit:
            qualifier = "estimated " if count.is_estimate else ""
            raise TokenBudgetExceeded(
                f"Prompt uses {qualifier}{count.value} tokens; "
                f"budget is {effective_limit}. Reduce non-essential context "
                "or select a larger context profile. Clinical evidence was not truncated."
            )
        return count
