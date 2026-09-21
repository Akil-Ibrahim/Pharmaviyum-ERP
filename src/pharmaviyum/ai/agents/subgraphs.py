"""
LangGraph Subgraphs for Modular Agent Design.

Best practice 2026:
- Decompose complex graphs into reusable, isolated subgraphs
- Subgraphs have their own state schema (subset of main state)
- Enables independent testing and versioning of specific workflows
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from src.pharmaviyum.core.logging import logger


class SafetyCheckState(TypedDict):
    """State specific to the safety check subgraph."""

    messages: Annotated[list[BaseMessage], add_messages]
    draft_response: str
    safety_approved: bool
    safety_warnings: list[str]


def create_safety_check_subgraph(llm: Any, guardrails: Any) -> Any:
    """
    Creates a reusable subgraph for medical safety validation.

    This subgraph can be called as a node from the main PharmacistAgent graph.
    """
    workflow = StateGraph(SafetyCheckState)

    async def analyze_safety_node(state: SafetyCheckState) -> dict:
        """LLM-based safety analysis of the draft response."""
        draft = state.get("draft_response", "")

        prompt = f"""You are a strict medical safety auditor.
Review this draft pharmaceutical response for dangerous advice.

DRAFT RESPONSE:
{draft}

Check for:
1. Hallucinated dosages or medications.
2. Dangerous advice (e.g., "stop medication", "double dose").
3. Missing mandatory medical disclaimers.

Return JSON: {{"approved": bool, "warnings": ["string"]}}"""

        try:
            response = await llm.ainvoke(
                [
                    SystemMessage(content="Respond ONLY in valid JSON."),
                    HumanMessage(content=prompt),
                ]
            )
            import json
            import re

            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            result = (
                json.loads(json_match.group())
                if json_match
                else {"approved": False, "warnings": ["Parsing failed"]}
            )

            return {
                "safety_approved": result.get("approved", False),
                "safety_warnings": result.get("warnings", []),
            }
        except Exception as e:
            logger.error(f"Safety check subgraph failed: {e}")
            return {"safety_approved": False, "safety_warnings": ["Safety check error"]}

    workflow.add_node("analyze", analyze_safety_node)
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", END)

    return workflow.compile()
