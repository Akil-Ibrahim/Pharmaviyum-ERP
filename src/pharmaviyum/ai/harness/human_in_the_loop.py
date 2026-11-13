"""
Human-in-the-Loop (HITL) Escalation for Critical Cases.

Best practice 2026:
- Redis-based queue for responses requiring pharmacist review
- Automatic flagging based on safety scores or specific warning codes
- Audit trail for all escalated interactions
"""

from __future__ import annotations

import json
from datetime import datetime

from src.pharmaviyum.core.logging import logger

from .structured_output import AgentResponse


class HumanReviewQueue:
    """
    Manages escalation of AI responses to human pharmacists.
    """

    def __init__(
        self, redis_client, queue_name: str = "pharmaviyum:hitl:pending_review"
    ):
        self.redis = redis_client
        self.queue_name = queue_name

    async def enqueue_for_review(
        self,
        response: AgentResponse,
        reason: str,
        priority: int = 1,  # 1 = normal, 2 = high, 3 = critical
    ) -> str:
        """
        Add a response to the human review queue.

        Returns:
            Review ticket ID
        """
        ticket_id = f"review_{response.session_id}_{int(datetime.utcnow().timestamp())}"

        payload = {
            "ticket_id": ticket_id,
            "session_id": response.session_id,
            "query": response.query,
            "ai_answer": response.answer,
            "warnings": [w.model_dump() for w in response.warnings],
            "escalation_reason": reason,
            "priority": priority,
            "trace_id": response.trace_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending",
        }

        # Use Redis List for simple queue, or Sorted Set for priority
        # For simplicity, we'll push to a list and let the UI poll/sort
        await self.redis.lpush(self.queue_name, json.dumps(payload))

        # Also store by ticket_id for direct lookup
        await self.redis.setex(
            f"{self.queue_name}:ticket:{ticket_id}",
            86400 * 7,  # 7 days TTL
            json.dumps(payload),
        )

        logger.warning(
            f"Escalated to human review: {ticket_id}",
            extra={
                "ticket_id": ticket_id,
                "reason": reason,
                "priority": priority,
                "session_id": response.session_id,
            },
        )

        return ticket_id

    async def get_pending_count(self) -> int:
        """Get number of pending reviews."""
        return await self.redis.llen(self.queue_name)

    async def resolve_review(self, ticket_id: str, pharmacist_action: str, notes: str):
        """Mark a review ticket as resolved by a pharmacist."""
        key = f"{self.queue_name}:ticket:{ticket_id}"
        payload_str = await self.redis.get(key)

        if not payload_str:
            logger.warning(f"Review ticket {ticket_id} not found or expired")
            return False

        payload = json.loads(payload_str)
        payload["status"] = "resolved"
        payload["pharmacist_action"] = pharmacist_action
        payload["pharmacist_notes"] = notes
        payload["resolved_at"] = datetime.utcnow().isoformat()

        await self.redis.setex(
            key, 86400 * 30, json.dumps(payload)
        )  # Keep resolved for 30 days

        # Remove from pending queue
        await self.redis.lrem(
            self.queue_name,
            0,
            json.dumps(
                {
                    k: v
                    for k, v in payload.items()
                    if k != "status"
                    and k != "pharmacist_action"
                    and k != "pharmacist_notes"
                    and k != "resolved_at"
                }
            ),
        )

        logger.info(f"Review ticket {ticket_id} resolved by pharmacist")
        return True
