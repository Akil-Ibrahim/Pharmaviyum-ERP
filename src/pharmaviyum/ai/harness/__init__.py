"""
Agent Harness Module — Production wrapper for LangGraph agents.

Public API:
- AgentHarness: Main orchestrator
- DialogueMemory: Redis-backed conversation memory
- MedicalGuardrails: Input/output safety validation
- PromptCache: Semantic and exact prompt caching
- ModelRouter: Complexity-aware LLM selection
- AgentResponse: Structured output schema
- ToolCallingLayer: High-level tool orchestration
- ContextWindowManager: Dynamic token limit management
- GracefulDegradation: Fallback responses for system failures
- HumanReviewQueue: HITL escalation for critical cases
"""
from .agent_harness import AgentHarness
from .memory import DialogueMemory
from .guardrails import MedicalGuardrails
from .cache import PromptCache
from .model_router import ModelRouter
from .structured_output import (
    AgentResponse,
    SourceCitation,
    ToolCallRecord,
    Warning,
    StreamingEvent,
)
from .tool_calling import ToolCallingLayer, ToolSpec
from .context_manager import ContextWindowManager
from .error_recovery import GracefulDegradation
from .human_in_the_loop import HumanReviewQueue

__all__ = [
    "AgentHarness",
    "DialogueMemory",
    "MedicalGuardrails",
    "PromptCache",
    "ModelRouter",
    "AgentResponse",
    "SourceCitation",
    "ToolCallRecord",
    "Warning",
    "StreamingEvent",
    "ToolCallingLayer",
    "ToolSpec",
    "ContextWindowManager",
    "GracefulDegradation",
    "HumanReviewQueue",
]
