"""
Production Agent Harness.

Best practice 2026:
- Centralized orchestration of all AI components
- Strict execution pipeline: Memory → Guardrails → Cache → Router → Agent → Guardrails → Memory
- Async non-blocking execution
- Structured, typed responses for API layer
- Comprehensive logging and error handling
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from src.pharmaviyum.ai.agents import PharmacistAgent
from src.pharmaviyum.core.logging import logger

from .cache import PromptCache
from .guardrails import MedicalGuardrails
from .memory import DialogueMemory
from .model_router import ModelRouter


class AgentHarness:
    """
    Production-ready wrapper around the LangGraph Pharmacist Agent.

    Provides:
    - Dialogue memory management (short-term + long-term)
    - Input/output safety guardrails
    - Semantic prompt caching
    - Intelligent model routing
    - Structured execution tracing
    """

    def __init__(
        self,
        agent: PharmacistAgent,
        memory: DialogueMemory,
        guardrails: MedicalGuardrails,
        cache: PromptCache,
        model_router: ModelRouter,
    ):
        self.agent = agent
        self.memory = memory
        self.guardrails = guardrails
        self.cache = cache
        self.model_router = model_router

    async def run(
        self,
        session_id: str,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Main entry point for agent execution.

        Args:
            session_id: Unique identifier for the conversation
            query: User's input message
            context: Additional context (patient_id, country, language, halal_filter)

        Returns:
            Structured dictionary with answer, warnings, and metadata
        """
        start_time = time.perf_counter()
        context = context or {}
        trace_id = str(uuid.uuid4())

        logger.info(
            "Agent harness execution started",
            extra={
                "session_id": session_id,
                "trace_id": trace_id,
                "query_preview": query[:50],
            },
        )

        try:
            # 1. Load dialogue memory
            history = await self.memory.load(session_id)

            # 2. Pre-process input (Guardrails: PII removal, injection detection)
            pre_process_result = await self.guardrails.pre_process(query)
            if not pre_process_result.is_safe:
                logger.warning(
                    f"Input blocked by guardrails: {pre_process_result.blocked_reason}"
                )
                return {
                    "success": False,
                    "answer": "I cannot process this request due to safety policies.",
                    "warnings": pre_process_result.warnings,
                    "trace_id": trace_id,
                }

            safe_query = pre_process_result.sanitized_input or query

            # 3. Check prompt cache
            cache_key_context = {
                k: v
                for k, v in context.items()
                if k in ["country", "language", "halal_filter"]
            }
            cached_response = await self.cache.get(safe_query, cache_key_context)

            if cached_response and not context.get("force_fresh"):
                logger.info(
                    "Cache HIT - returning cached response",
                    extra={"trace_id": trace_id},
                )
                return {
                    "success": True,
                    "answer": cached_response["answer"],
                    "warnings": cached_response.get("warnings", []),
                    "cache_hit": True,
                    "trace_id": trace_id,
                    "latency_ms": (time.perf_counter() - start_time) * 1000,
                }

            # 4. Select optimal model via router
            selected_llm = self.model_router.select(
                query=safe_query,
                history_length=len(history),
                context=context,
                requires_safety_check=bool(
                    context.get("halal_filter") or context.get("prescription_id")
                ),
            )

            # 5. Execute LangGraph Agent
            # Note: In a full implementation, we'd inject the selected LLM into the agent dynamically.
            # For now, we pass the context to the agent's run method.
            agent_result = await self.agent.run(
                query=safe_query,
                context={**context, "trace_id": trace_id},
                thread_id=session_id,
            )

            if not agent_result.get("success"):
                raise RuntimeError(agent_result.get("error", "Agent execution failed"))

            raw_answer = agent_result.get("answer", "")
            agent_warnings = agent_result.get("warnings", [])

            # 6. Post-process output (Guardrails: safety check, disclaimer)
            post_process_result = await self.guardrails.post_process(
                answer=raw_answer,
                question=safe_query,
                sources=agent_result.get("tool_results", []),
            )

            if not post_process_result.is_safe:
                logger.warning(
                    f"Output blocked by guardrails: {post_process_result.blocked_reason}"
                )
                final_answer = "⚠️ I cannot provide this information as it may be unsafe. Please consult a licensed pharmacist."
                agent_warnings.append("output_safety_block")
            else:
                final_answer = post_process_result.validated_output or raw_answer
                agent_warnings.extend(post_process_result.warnings)

            # 7. Save to dialogue memory
            await self.memory.save(
                session_id=session_id,
                user_message=safe_query,
                assistant_message=final_answer,
            )

            # 8. Update prompt cache
            await self.cache.set(
                prompt=safe_query,
                response={"answer": final_answer, "warnings": agent_warnings},
                context=cache_key_context,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "Agent harness execution completed successfully",
                extra={
                    "session_id": session_id,
                    "trace_id": trace_id,
                    "latency_ms": latency_ms,
                    "warnings_count": len(agent_warnings),
                },
            )

            return {
                "success": True,
                "answer": final_answer,
                "warnings": list(set(agent_warnings)),  # Unique warnings
                "cache_hit": False,
                "trace_id": trace_id,
                "latency_ms": latency_ms,
            }

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Agent harness execution failed: {e}",
                extra={"session_id": session_id, "trace_id": trace_id, "error": str(e)},
                exc_info=True,
            )

            return {
                "success": False,
                "answer": "I encountered an error while processing your request. Please try again or consult a pharmacist.",
                "warnings": ["harness_execution_error"],
                "trace_id": trace_id,
                "latency_ms": latency_ms,
            }

    async def astream(
        self,
        session_id: str,
        query: str,
        context: dict[str, Any] | None = None,
    ):
        """
        Stream agent execution events for real-time UI updates.

        Yields dictionaries with event type and payload.
        """
        context = context or {}
        trace_id = str(uuid.uuid4())

        yield {"event": "start", "trace_id": trace_id}

        try:
            # Pre-process
            yield {"event": "status", "message": "Validating input..."}
            pre_process = await self.guardrails.pre_process(query)
            if not pre_process.is_safe:
                yield {"event": "error", "message": "Input blocked by safety policies"}
                return

            safe_query = pre_process.sanitized_input or query

            # Cache check
            yield {"event": "status", "message": "Checking knowledge cache..."}
            cache_key_context = {
                k: v
                for k, v in context.items()
                if k in ["country", "language", "halal_filter"]
            }
            cached = await self.cache.get(safe_query, cache_key_context)
            if cached and not context.get("force_fresh"):
                yield {"event": "answer", "text": cached["answer"], "cache_hit": True}
                return

            # Stream LangGraph execution
            yield {
                "event": "status",
                "message": "Thinking and retrieving information...",
            }
            async for stream_event in self.agent.astream(
                query=safe_query, context={**context, "trace_id": trace_id}
            ):
                node = stream_event.get("node")
                data = stream_event.get("data", {})

                if node == "router":
                    yield {
                        "event": "status",
                        "message": f"Routing query: {data.get('query_intent', 'analyzing')}...",
                    }
                elif node == "planner":
                    yield {"event": "status", "message": "Planning tool usage..."}
                elif node == "executor":
                    tools = [r.get("tool") for r in data.get("tool_results", [])]
                    yield {
                        "event": "status",
                        "message": f"Executing tools: {', '.join(tools) or 'none'}...",
                    }
                elif node == "reviewer":
                    yield {"event": "status", "message": "Validating medical safety..."}

            # Get final result (simplified for streaming demo; in prod, track state)
            yield {"event": "status", "message": "Finalizing response..."}

            # For a true stream of tokens, the agent's reviewer node would need to yield tokens.
            # Here we yield a placeholder indicating completion.
            yield {"event": "complete", "message": "Response ready"}

        except Exception as e:
            logger.error(f"Streaming failed: {e}", exc_info=True)
            yield {"event": "error", "message": "An error occurred during processing."}
