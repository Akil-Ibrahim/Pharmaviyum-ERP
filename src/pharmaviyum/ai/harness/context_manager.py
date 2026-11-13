"""
Context Window Management for Agent Harness.

Best practice 2026:
- Dynamic token estimation to prevent context window overflow
- Priority-based message truncation (keep system prompts + recent turns)
- Automatic summarization trigger when approaching limits
"""

from __future__ import annotations

from langchain_core.messages import BaseMessage, SystemMessage

from src.pharmaviyum.core.logging import logger


class ContextWindowManager:
    """
    Manages LLM context window limits to prevent overflow errors and control costs.
    """

    def __init__(
        self,
        max_tokens: int = 8000,  # Conservative limit for most 8k-32k models
        tokens_per_char_estimate: float = 0.25,  # ~4 chars per token
        reserve_tokens: int = 1000,  # Reserve for system prompt and final response
    ):
        self.max_tokens = max_tokens
        self.available_tokens = max_tokens - reserve_tokens
        self.tokens_per_char = tokens_per_char_estimate

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (fast, no external API calls)."""
        return int(len(text) * self.tokens_per_char)

    def truncate_messages(
        self,
        messages: list[BaseMessage],
        system_prompt: str | None = None,
    ) -> list[BaseMessage]:
        """
        Truncate message history to fit within token limits.

        Priority:
        1. System prompt (always kept)
        2. Most recent user/assistant turns
        3. Older turns (dropped first)
        """
        if not messages:
            return [SystemMessage(content=system_prompt)] if system_prompt else []

        # Estimate total tokens
        total_text = "\n".join([getattr(m, "content", str(m)) for m in messages])
        if system_prompt:
            total_text += system_prompt

        estimated_tokens = self.estimate_tokens(total_text)

        if estimated_tokens <= self.available_tokens:
            # Fits within limits, return as-is
            result = (
                [SystemMessage(content=system_prompt)] + messages
                if system_prompt
                else messages
            )
            return result

        # Truncation needed: keep the most recent N messages
        logger.warning(
            f"Context window exceeded ({estimated_tokens} > {self.available_tokens}). Truncating history."
        )

        truncated_messages: list[BaseMessage] = []
        current_tokens = self.estimate_tokens(system_prompt) if system_prompt else 0

        # Iterate backwards to keep most recent messages
        for msg in reversed(messages):
            msg_tokens = self.estimate_tokens(getattr(msg, "content", str(msg)))
            if current_tokens + msg_tokens <= self.available_tokens:
                truncated_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break  # Stop adding older messages

        # Always prepend system prompt if available
        if system_prompt:
            truncated_messages.insert(0, SystemMessage(content=system_prompt))

        # Add a truncation notice for the LLM
        if len(truncated_messages) < len(messages):
            truncation_notice = SystemMessage(
                content="[Note: Earlier conversation history was truncated due to length limits. Focus on the most recent messages.]"
            )
            # Insert after the main system prompt
            truncated_messages.insert(1, truncation_notice)

        logger.info(
            f"Truncated history from {len(messages)} to {len(truncated_messages)} messages"
        )
        return truncated_messages
