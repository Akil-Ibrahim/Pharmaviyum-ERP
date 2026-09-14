"""
Human-in-the-Loop (HITL) Interrupts for LangGraph.

Best practice 2026:
- Use `interrupt` to pause graph execution for human approval
- Critical for high-risk medical decisions (e.g., controlled substances)
- Resume execution using `Command(resume=...)`
"""
from __future__ import annotations
from typing import Any
from langgraph.types import interrupt, Command
from src.pharmaviyum.core.logging import logger


class PharmacistApprovalRequest:
    """Schema for data passed to the human reviewer during interrupt."""
    def __init__(self, query: str, draft_response: str, risk_level: str, reason: str):
        self.query = query
        self.draft_response = draft_response
        self.risk_level = risk_level  # "low", "medium", "high", "critical"
        self.reason = reason
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "draft_response": self.draft_response,
            "risk_level": self.risk_level,
            "reason": self.reason,
        }


async def require_pharmacist_approval_node(state: dict[str, Any]) -> Command:
    """
    Node that pauses execution and waits for human pharmacist approval.
    
    Triggered when:
    - Critical drug interaction detected
    - Controlled substance quantity exceeds limits
    - Safety score drops below threshold
    """
    draft_response = state.get("final_answer", "") or state.get("messages", [])[-1].content
    query = state.get("messages", [])[0].content
    
    request = PharmacistApprovalRequest(
        query=query,
        draft_response=draft_response,
        risk_level="high",
        reason="Potential critical drug interaction or controlled substance limit exceeded."
    )
    
    logger.warning(
        "Graph interrupted: Waiting for pharmacist approval",
        extra={"risk_level": request.risk_level, "reason": request.reason}
    )
    
    # Pause execution. The graph will halt here until `Command(resume=...)` is provided.
    approval_decision = interrupt(request.to_dict())
    
    # Execution resumes here after human input
    if approval_decision.get("approved"):
        logger.info("Pharmacist approved the response")
        # Optionally append approval note
        approved_response = f"{draft_response}\n\n*[Verified by licensed pharmacist]*"
        return Command(update={"final_answer": approved_response, "requires_human_review": False})
    else:
        logger.info("Pharmacist rejected the response")
        rejection_reason = approval_decision.get("reason", "Safety concerns.")
        return Command(update={
            "final_answer": f"I cannot fulfill this request. A supervising pharmacist reviewed this and determined it is not safe: {rejection_reason}",
            "requires_human_review": True,
            "warnings": ["pharmacist_rejected"]
        })
