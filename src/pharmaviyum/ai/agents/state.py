"""
LangGraph Agent State Definition.

Best practice 2026:
- TypedDict for LangGraph state compatibility
- Annotated fields with custom reducers (e.g., add_messages)
- Strict typing for tool calls and context
"""

from __future__ import annotations

from operator import add
from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    State shared across all nodes in the Pharmacist Agent graph.

    Attributes:
        messages: Conversation history (automatically appended via add_messages)
        context: Query context (patient_id, country, language, halal_filter)
        tool_calls: List of tool calls made by the LLM
        tool_results: Results returned from MCP tools
        final_answer: The validated final response to the user
        warnings: Safety/regulatory warnings generated during execution
        rag_context: Tenant-scoped evidence supplied by Mortarium RAG
        rag_sources: Source citations returned by Mortarium RAG
        iteration: Counter to prevent infinite loops in planning
    """

    messages: Annotated[list[BaseMessage], add_messages]
    context: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    tool_results: Annotated[list[dict[str, Any]], add]
    final_answer: str | None
    warnings: list[str]
    rag_context: str
    rag_sources: list[dict[str, Any]]
    iteration: int
    model_used: str
