"""
Dialogue Memory for Agent Harness.

Best practice 2026:
- Redis-backed short-term memory (sliding window)
- Long-term memory via LLM summarization (token optimization)
- Episodic memory for key medical facts (allergies, chronic conditions)
- Async Redis operations for non-blocking I/O
"""

from __future__ import annotations

import json
from datetime import datetime

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.pharmaviyum.core.logging import logger


class DialogueMemory:
    """
    Production-ready dialogue memory with tiered storage.

    Tiers:
    1. Short-term: Last N messages (sliding window in Redis list)
    2. Long-term: Summarized context of older messages (Redis string)
    3. Episodic: Key medical facts extracted from conversation (Redis hash)
    """

    def __init__(
        self,
        redis_client,
        max_short_term_messages: int = 10,
        summarization_threshold: int = 20,
        ttl_seconds: int = 86400 * 7,  # 7 days
    ):
        self.redis = redis_client
        self.max_short_term = max_short_term_messages
        self.summarization_threshold = summarization_threshold
        self.ttl = ttl_seconds
        self._prefix = "agent:memory"

    async def load(self, session_id: str) -> list[BaseMessage]:
        """
        Load conversation history for a session.

        Combines:
        1. Long-term summary (if exists) as SystemMessage
        2. Short-term messages (last N) as Human/AIMessage pairs
        """
        messages: list[BaseMessage] = []

        # 1. Load long-term summary
        summary_key = f"{self._prefix}:{session_id}:summary"
        summary = await self.redis.get(summary_key)
        if summary:
            messages.append(
                SystemMessage(
                    content=f"Previous conversation summary: {summary.decode('utf-8') if isinstance(summary, bytes) else summary}"
                )
            )

        # 2. Load short-term messages
        short_term_key = f"{self._prefix}:{session_id}:messages"
        raw_messages = await self.redis.lrange(
            short_term_key, -self.max_short_term * 2, -1
        )

        for raw_msg in raw_messages:
            msg_data = json.loads(raw_msg)
            role = msg_data.get("role")
            content = msg_data.get("content", "")

            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        logger.debug(f"Loaded {len(messages)} messages for session {session_id}")
        return messages

    async def save(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """
        Save new message pair and manage memory tiers.

        If short-term memory exceeds threshold, triggers summarization.
        """
        short_term_key = f"{self._prefix}:{session_id}:messages"
        summary_key = f"{self._prefix}:{session_id}:summary"

        # Append new messages
        pipe = self.redis.pipeline()
        pipe.rpush(
            short_term_key,
            json.dumps(
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
        )
        pipe.rpush(
            short_term_key,
            json.dumps(
                {
                    "role": "assistant",
                    "content": assistant_message,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
        )

        # Trim to keep only recent messages (keep extra for overlap during summarization)
        max_keep = self.summarization_threshold * 2
        pipe.ltrim(short_term_key, -max_keep, -1)

        # Set TTL on the list
        pipe.expire(short_term_key, self.ttl)

        await pipe.execute()

        # Check if summarization is needed
        length = await self.redis.llen(short_term_key)
        if length >= self.summarization_threshold * 2:
            await self._summarize_and_compress(session_id, short_term_key, summary_key)

    async def _summarize_and_compress(
        self,
        session_id: str,
        short_term_key: str,
        summary_key: str,
    ) -> None:
        """
        Compress older messages into a summary and clear them from short-term.

        Note: In production, this would call an LLM. For now, we simulate
        the structure. The actual LLM call is injected via the harness.
        """
        # Get messages to summarize (older half of the window)
        to_summarize_count = self.summarization_threshold
        raw_messages = await self.redis.lrange(
            short_term_key, 0, to_summarize_count - 1
        )

        if not raw_messages:
            return

        # TODO: Inject LLM summarization here in the full harness
        # For now, we create a placeholder summary
        summary = f"Summarized {to_summarize_count} turns of conversation. Key topics: medical consultation."

        # If existing summary exists, append to it
        existing_summary = await self.redis.get(summary_key)
        if existing_summary:
            existing_text = (
                existing_summary.decode("utf-8")
                if isinstance(existing_summary, bytes)
                else existing_summary
            )
            summary = f"{existing_text}\n\n[Update]: {summary}"

        # Save new summary
        pipe = self.redis.pipeline()
        pipe.setex(summary_key, self.ttl, summary)

        # Remove summarized messages from short-term list
        pipe.ltrim(short_term_key, to_summarize_count, -1)

        await pipe.execute()
        logger.info(f"Summarized and compressed memory for session {session_id}")

    async def save_episodic_fact(
        self,
        session_id: str,
        fact_type: str,  # e.g., "allergy", "condition", "preference"
        fact_value: str,
    ) -> None:
        """
        Save a key medical fact for quick retrieval without reading full history.
        """
        episodic_key = f"{self._prefix}:{session_id}:episodic"

        # Store in Redis Hash
        await self.redis.hset(episodic_key, fact_type, fact_value)
        await self.redis.expire(episodic_key, self.ttl)

        logger.info(
            f"Saved episodic fact: {fact_type} = {fact_value} for session {session_id}"
        )

    async def get_episodic_facts(self, session_id: str) -> dict[str, str]:
        """Retrieve all episodic facts for a session."""
        episodic_key = f"{self._prefix}:{session_id}:episodic"
        facts = await self.redis.hgetall(episodic_key)

        # Decode bytes to strings
        return {
            k.decode("utf-8"): v.decode("utf-8") if isinstance(v, bytes) else v
            for k, v in facts.items()
        }

    async def clear(self, session_id: str) -> None:
        """Clear all memory for a session."""
        pipe = self.redis.pipeline()
        pipe.delete(f"{self._prefix}:{session_id}:messages")
        pipe.delete(f"{self._prefix}:{session_id}:summary")
        pipe.delete(f"{self._prefix}:{session_id}:episodic")
        await pipe.execute()
        logger.info(f"Cleared all memory for session {session_id}")
