"""
Token-Level Streaming for LangGraph Agent.

Best practice 2026:
- Real-time token streaming via LangChain astream_events
- SSE (Server-Sent Events) compatible output
- Distinguishes between node events and LLM token events
- Supports cancellation and timeout
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from langchain_core.messages import AIMessageChunk
from langgraph.graph.state import CompiledStateGraph

from src.pharmaviyum.core.logging import logger


class AgentStreamManager:
    """
    Manages token-level streaming from LangGraph agent.

    Provides:
    - Real-time LLM token streaming (not just node events)
    - Structured event format for SSE
    - Timeout and cancellation support
    """

    def __init__(self, graph: CompiledStateGraph, timeout_seconds: float = 60.0):
        self.graph = graph
        self.timeout_seconds = timeout_seconds

    async def stream_tokens(
        self,
        initial_state: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream agent execution with token-level granularity.

        Yields events:
        - {"type": "node_start", "node": "router", "timestamp": ...}
        - {"type": "token", "content": "The", "node": "reviewer", "timestamp": ...}
        - {"type": "tool_call", "tool": "check_drug_interactions", "args": {...}}
        - {"type": "node_end", "node": "reviewer", "timestamp": ...}
        - {"type": "complete", "final_state": {...}}
        """
        config = config or {}

        try:
            async with asyncio.timeout(self.timeout_seconds):
                graph: Any = self.graph
                async for event in graph.astream_events(
                    initial_state,
                    config=config,
                    version="v2",
                ):
                    event_kind = event.get("event")

                    # Node lifecycle events
                    if event_kind == "on_chain_start":
                        node_name = event.get("name", "unknown")
                        yield {
                            "type": "node_start",
                            "node": node_name,
                            "timestamp": event.get("timestamp"),
                        }

                    elif event_kind == "on_chain_end":
                        node_name = event.get("name", "unknown")
                        yield {
                            "type": "node_end",
                            "node": node_name,
                            "timestamp": event.get("timestamp"),
                        }

                    # LLM token streaming
                    elif event_kind == "on_chat_model_stream":
                        chunk: AIMessageChunk = event.get("data", {}).get("chunk")
                        if chunk and chunk.content:
                            yield {
                                "type": "token",
                                "content": chunk.content,
                                "node": event.get("name", "llm"),
                                "timestamp": event.get("timestamp"),
                            }

                    # Tool call events
                    elif event_kind == "on_tool_start":
                        tool_name = event.get("name", "unknown")
                        tool_input = event.get("data", {}).get("input", {})
                        yield {
                            "type": "tool_call",
                            "tool": tool_name,
                            "argument_count": (
                                len(tool_input) if isinstance(tool_input, dict) else 0
                            ),
                            "timestamp": event.get("timestamp"),
                        }

                    elif event_kind == "on_tool_end":
                        tool_name = event.get("name", "unknown")
                        tool_output = event.get("data", {}).get("output")
                        yield {
                            "type": "tool_result",
                            "tool": tool_name,
                            "output_type": type(tool_output).__name__,
                            "timestamp": event.get("timestamp"),
                        }

                # Final state
                final_state = await graph.ainvoke(
                    initial_state, config=config, version="v2"
                )
                yield {
                    "type": "complete",
                    "final_state": final_state,
                }

        except asyncio.TimeoutError:
            logger.error(f"Agent streaming timed out after {self.timeout_seconds}s")
            yield {
                "type": "error",
                "error": "Agent execution timed out",
                "timeout_seconds": self.timeout_seconds,
            }

        except Exception as exc:
            logger.error(
                "Agent streaming failed",
                extra={"error_type": type(exc).__name__},
            )
            yield {
                "type": "error",
                "error": "Agent execution failed",
            }
