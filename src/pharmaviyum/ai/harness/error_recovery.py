"""
Error Recovery and Graceful Degradation for Agent Harness.

Best practice 2026:
- Fallback responses when LLM or tools are completely unavailable
- Circuit breaker integration at the harness level
- Clear user communication during degradation
"""
from __future__ import annotations
from .structured_output import AgentResponse, Warning
from src.pharmaviyum.core.logging import logger


class GracefulDegradation:
    """
    Provides safe fallback responses when the AI system experiences failures.
    """
    
    @staticmethod
    def get_fallback_response(
        session_id: str,
        query: str,
        error_type: str,
        trace_id: str,
    ) -> AgentResponse:
        """
        Generate a safe, structured fallback response.
        
        Args:
            session_id: Current conversation session
            query: Original user query
            error_type: 'llm_unavailable', 'tool_failure', 'timeout', 'unknown'
            trace_id: For observability correlation
        """
        logger.warning(
            f"Triggering graceful degradation: {error_type}",
            extra={"session_id": session_id, "trace_id": trace_id}
        )
        
        if error_type == "llm_unavailable":
            answer = (
                "⚠️ Our AI assistant is currently experiencing high load or technical difficulties. "
                "For your safety and to ensure accurate information, please consult a licensed pharmacist "
                "or contact our support team directly."
            )
            warning_code = "ai_service_degraded"
            warning_msg = "AI service temporarily unavailable"
            
        elif error_type == "tool_failure":
            answer = (
                "⚠️ I was unable to retrieve the necessary medical database information to answer your question safely. "
                "Please consult a licensed pharmacist for accurate medication advice."
            )
            warning_code = "tool_dependency_failed"
            warning_msg = "Critical tool dependency failed"
            
        else:
            answer = (
                "⚠️ An unexpected error occurred while processing your request. "
                "For your safety, please consult a licensed pharmacist."
            )
            warning_code = "unknown_error"
            warning_msg = "Unexpected processing error"
        
        return AgentResponse(
            session_id=session_id,
            query=query,
            answer=answer,
            sources=[],
            tool_calls=[],
            confidence=0.0,
            requires_human_review=True,
            escalation_reason=error_type,
            warnings=[
                Warning(
                    code=warning_code,
                    severity="critical",
                    message=warning_msg,
                    details={"trace_id": trace_id},
                )
            ],
            safety_score=1.0,  # Fallback is safe because it refuses to answer
            model_used="fallback_system",
            total_latency_ms=0.0,
            trace_id=trace_id,
        )
