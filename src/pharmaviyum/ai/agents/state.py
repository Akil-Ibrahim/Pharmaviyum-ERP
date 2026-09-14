"""
LangGraph Agent State Definition.

Best practice 2026:
- TypedDict for LangGraph state compatibility
- Annotated fields with custom reducers (e.g., add_messages)
- Strict typing for tool calls and context
"""
from __future__ import annotations
from typing import TypedDict, Annotated, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


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
        iteration: Counter to prevent infinite loops in planning
    """
    messages: Annotated[list[BaseMessage], add_messages]
    context: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    final_answer: str | None
    warnings: list[str]
    iteration: int
