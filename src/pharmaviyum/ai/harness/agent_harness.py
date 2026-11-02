"""
Production Agent Harness.

Best practice 2026:
- Centralized orchestration of all AI components
- Strict execution pipeline: Memory → Guardrails → Cache → Router → Agent → Guardrails → Memory
- Async non-blocking execution
- Structured, typed responses for API layer
- Comprehensive logging and error handling without medical-content previews
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
    """Production-ready wrapper around the LangGraph Pharmacist Agent."""

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

        # Memory summarization must use the same managed model lifecycle as the
        # agent.  This keeps summarization injectable/testable while avoiding a
        # second LLM client or a hidden global dependency.
        if self.memory.summarizer is None:
            self.memory.summarizer = getattr(agent, "main_llm", None)

    @staticmethod
    def _cache_context(context: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in context.items()
            if key
            in {
                "user_id",
                "pharmacy_id",
                "patient_id",
                "prescription_id",
                "country",
                "language",
                "halal_filter",
                "role",
                "permissions_version",
                "formulary_version",
                "inventory_version",
                "catalog_version",
                "force_fresh",
                "cache_disabled",
            }
        }

    async def _post_process(
        self,
        answer: str,
        question: str,
        sources: list[dict[str, Any]],
    ) -> tuple[str, list[str]]:
        result = await self.guardrails.post_process(
            answer=answer,
            question=question,
            sources=sources,
        )
        if not result.is_safe:
            logger.warning("Output blocked by guardrails")
            return (
                "⚠️ I cannot provide this information as it may be unsafe. "
                "Please consult a licensed pharmacist.",
                ["output_safety_block"],
            )
        return result.validated_output or answer, list(result.warnings)

    async def run(
        self,
        session_id: str,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start_time = time.perf_counter()
        context = context or {}
        trace_id = str(uuid.uuid4())

        logger.info(
            "Agent harness execution started",
            extra={"session_id": session_id, "trace_id": trace_id},
        )

        try:
            history = await self.memory.load(session_id)
            pre_process_result = await self.guardrails.pre_process(query)
            if not pre_process_result.is_safe:
                logger.warning("Input blocked by guardrails")
                return {
                    "success": False,
                    "answer": "I cannot process this request due to safety policies.",
                    "warnings": pre_process_result.warnings,
                    "trace_id": trace_id,
                }

            safe_query = pre_process_result.sanitized_input or query
            cache_key_context = self._cache_context(context)
            cached_response = await self.cache.get(safe_query, cache_key_context)

            if cached_response and not context.get("force_fresh"):
                logger.info(
                    "Cache HIT - returning validated response",
                    extra={"trace_id": trace_id},
                )
                return {
                    "success": True,
                    "answer": cached_response["answer"],
                    "warnings": cached_response.get("warnings", []),
                    "tool_results": cached_response.get("tool_results", []),
                    "model_used": cached_response.get("model_used", "cached"),
                    "cache_hit": True,
                    "trace_id": trace_id,
                    "latency_ms": (time.perf_counter() - start_time) * 1000,
                }

            await self.model_router.select(
                query=safe_query,
                history_length=len(history),
                context=context,
                requires_safety_check=bool(
                    context.get("halal_filter") or context.get("prescription_id")
                ),
            )

            agent_result = await self.agent.run(
                query=safe_query,
                context={**context, "trace_id": trace_id},
                thread_id=session_id,
            )
            if not agent_result.get("success"):
                raise RuntimeError("Agent execution failed")

            raw_answer = str(agent_result.get("answer", ""))
            agent_warnings = list(agent_result.get("warnings", []))
            tool_results = list(agent_result.get("tool_results", []))
            final_answer, post_warnings = await self._post_process(
                answer=raw_answer,
                question=safe_query,
                sources=tool_results,
            )
            agent_warnings.extend(post_warnings)

            await self.memory.save(
                session_id=session_id,
                user_message=safe_query,
                assistant_message=final_answer,
            )
            if not context.get("force_fresh") and not context.get("cache_disabled"):
                await self.cache.set(
                    prompt=safe_query,
                    response={
                        "answer": final_answer,
                        "warnings": agent_warnings,
                        "tool_results": tool_results,
                        "model_used": (
                            getattr(self.agent.main_llm, "model", None)
                            or getattr(self.agent.main_llm, "model_name", None)
                            or "configured-main"
                        ),
                    },
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
                "warnings": list(set(agent_warnings)),
                "tool_results": tool_results,
                "model_used": (
                    agent_result.get("model_used")
                    or getattr(self.agent.main_llm, "model", None)
                    or getattr(self.agent.main_llm, "model_name", None)
                    or "configured-main"
                ),
                "cache_hit": False,
                "trace_id": trace_id,
                "latency_ms": latency_ms,
            }

        except Exception:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Agent harness execution failed",
                extra={"session_id": session_id, "trace_id": trace_id},
                exc_info=True,
            )
            return {
                "success": False,
                "answer": (
                    "I encountered an error while processing your request. "
                    "Please try again or consult a pharmacist."
                ),
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
        start_time = time.perf_counter()
        context = context or {}
        trace_id = str(uuid.uuid4())
        yield {"event": "start", "trace_id": trace_id}

        try:
            yield {"event": "status", "message": "Validating input..."}
            pre_process = await self.guardrails.pre_process(query)
            if not pre_process.is_safe:
                yield {"event": "error", "message": "Input blocked by safety policies"}
                return

            safe_query = pre_process.sanitized_input or query
            cache_key_context = self._cache_context(context)
            yield {"event": "status", "message": "Checking knowledge cache..."}
            cached = await self.cache.get(safe_query, cache_key_context)
            if cached and not context.get("force_fresh"):
                yield {"event": "answer", "text": cached["answer"], "cache_hit": True}
                return

            final_answer: str | None = None
            final_warnings: list[str] = []
            tool_results: list[dict[str, Any]] = []

            yield {
                "event": "status",
                "message": "Thinking and retrieving information...",
            }
            async for stream_event in self.agent.astream(
                query=safe_query,
                context={**context, "trace_id": trace_id},
                thread_id=session_id,
            ):
                node = stream_event.get("node")
                data = stream_event.get("data", {})
                if node == "router":
                    yield {
                        "event": "status",
                        "message": (
                            f"Routing query: {data.get('query_intent', 'analyzing')}..."
                        ),
                    }
                elif node == "planner":
                    yield {"event": "status", "message": "Planning tool usage..."}
                elif node == "executor":
                    tool_results.extend(data.get("tool_results", []))
                    tools = [r.get("tool") for r in data.get("tool_results", [])]
                    yield {
                        "event": "status",
                        "message": f"Executing tools: {', '.join(tools) or 'none'}...",
                    }
                elif node == "reviewer":
                    final_answer = data.get("final_answer")
                    final_warnings.extend(data.get("warnings", []))
                    yield {"event": "status", "message": "Validating medical safety..."}

            if final_answer is None:
                raise RuntimeError("Streaming agent completed without a final answer")

            final_answer, post_warnings = await self._post_process(
                answer=str(final_answer),
                question=safe_query,
                sources=tool_results,
            )
            final_warnings.extend(post_warnings)

            await self.memory.save(
                session_id=session_id,
                user_message=safe_query,
                assistant_message=final_answer,
            )
            if not context.get("force_fresh") and not context.get("cache_disabled"):
                await self.cache.set(
                    prompt=safe_query,
                    response={
                        "answer": final_answer,
                        "warnings": final_warnings,
                    },
                    context=cache_key_context,
                )

            yield {"event": "status", "message": "Finalizing response..."}
            yield {
                "event": "answer",
                "text": final_answer,
                "warnings": list(set(final_warnings)),
                "cache_hit": False,
            }
            yield {
                "event": "complete",
                "message": "Response ready",
                "latency_ms": (time.perf_counter() - start_time) * 1000,
            }

        except Exception:
            logger.error(
                "Streaming failed",
                extra={"session_id": session_id, "trace_id": trace_id},
                exc_info=True,
            )
            yield {"event": "error", "message": "An error occurred during processing."}
