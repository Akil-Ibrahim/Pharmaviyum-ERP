"""
Model Router for Agent Harness.

Best practice 2026:
- Dynamic model selection based on query complexity, language, and context
- Cost optimization (use small models for simple tasks, large models for complex reasoning)
- Latency-aware routing
- Fallback mechanisms if primary model fails
"""
from __future__ import annotations
from typing import Any, Protocol
from src.pharmaviyum.core.logging import logger


class LLMProvider(Protocol):
    """Protocol for LLM providers to ensure compatibility."""
    model_name: str
    
    async def ainvoke(self, messages: list, **kwargs) -> Any:
        ...
    
    async def astream(self, messages: list, **kwargs) -> Any:
        ...


class ModelRouter:
    """
    Intelligent router for selecting the optimal LLM for a given query.
    
    Routing criteria:
    1. Query complexity (simple, medium, complex)
    2. Language requirements (some models are better at specific languages)
    3. Task type (routing, reasoning, safety review)
    """
    
    def __init__(self, models: dict[str, LLMProvider]):
        """
        Initialize with a dictionary of available models.
        
        Example:
        {
            "fast": Qwen1_5B_Provider(),      # For routing, simple queries
            "main": Qwen7B_Provider(),        # For general agent reasoning
            "complex": Qwen72B_Provider(),    # For complex medical interactions
            "fallback": OpenAI_GPT4_Provider() # Emergency fallback
        }
        """
        self.models = models
        self.default_model = "main"
        self.fallback_model = "fallback"
    
    async def select(
        self,
        query: str,
        history_length: int = 0,
        context: dict[str, Any] | None = None,
        requires_safety_check: bool = False,
    ) -> LLMProvider:
        """
        Select the optimal model for the current query.
        
        Args:
            query: The user's input text
            history_length: Number of previous turns in the conversation
            context: Additional context (country, language, patient_id)
            requires_safety_check: If True, force a more capable model
        
        Returns:
            The selected LLMProvider instance
        """
        complexity = self._estimate_complexity(query, history_length, context)
        language = (context or {}).get("language", "en").lower()
        
        logger.debug(
            f"Model routing: complexity={complexity}, language={language}",
            extra={"query_preview": query[:50]}
        )
        
        # Rule 1: Safety checks always require the main or complex model
        if requires_safety_check:
            return self._get_model("complex" if complexity == "complex" else "main")
        
        # Rule 2: Language-specific optimizations
        if language in ["vi", "th", "id", "ar"] and complexity == "complex":
            # For complex queries in SEA/MENA languages, use the most capable multilingual model
            return self._get_model("complex")
        
        # Rule 3: Complexity-based routing
        if complexity == "simple":
            return self._get_model("fast")
        elif complexity == "medium":
            return self._get_model("main")
        else:
            return self._get_model("complex")
    
    def _estimate_complexity(
        self,
        query: str,
        history_length: int,
        context: dict[str, Any] | None,
    ) -> str:
        """
        Estimate query complexity using heuristics.
        
        Returns: "simple", "medium", or "complex"
        """
        query_lower = query.lower()
        
        # Heuristic 1: Length-based
        if len(query) < 30 and history_length < 2:
            return "simple"
        
        # Heuristic 2: Keyword-based (medical complexity indicators)
        complex_keywords = [
            "interaction", "contraindication", "allergy", "side effect",
            "alternative", "dosage", "pregnancy", "renal", "hepatic",
            "halal", "haram", "prescription", "verify"
        ]
        
        if any(keyword in query_lower for keyword in complex_keywords):
            return "complex"
        
        # Heuristic 3: Context-based
        if context:
            if context.get("patient_id") or context.get("prescription_id"):
                return "complex"  # Requires tool calls and DB lookups
            if context.get("halal_filter"):
                return "medium"  # Requires specific compliance checks
        
        # Heuristic 4: Conversation depth
        if history_length > 5:
            return "complex"  # Long conversations require better context handling
        
        return "medium"
    
    def _get_model(self, model_key: str) -> LLMProvider:
        """Get model by key, with fallback."""
        if model_key in self.models:
            return self.models[model_key]
        
        logger.warning(f"Requested model '{model_key}' not found, using default")
        if self.default_model in self.models:
            return self.models[self.default_model]
        
        # Ultimate fallback
        fallback_keys = list(self.models.keys())
        if fallback_keys:
            return self.models[fallback_keys[0]]
        
        raise RuntimeError("No LLM models configured in ModelRouter")
    
    def get_fallback(self) -> LLMProvider:
        """Get the designated fallback model."""
        if self.fallback_model in self.models:
            return self.models[self.fallback_model]
        return self._get_model(self.default_model)
