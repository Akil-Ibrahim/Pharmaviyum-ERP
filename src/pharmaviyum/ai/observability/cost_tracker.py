"""
LLM Cost Tracker.

Best practice 2026:
- Approximate cost calculation based on model pricing (per 1K tokens)
- Supports open-source (Ollama/Qwen) and commercial (OpenAI/Anthropic) models
- Used for budget alerting and ROI analysis of AI features
"""

from __future__ import annotations

# Approximate pricing per 1,000 tokens (USD)
# Note: Local models (Ollama) have $0 API cost, but we track compute equivalence
MODEL_PRICING: dict[str, dict[str, float]] = {
    # Open-source / Local (via Ollama) - API cost is 0, but tracked for comparison
    "qwen3.5:9b": {"input": 0.0, "output": 0.0},
    "mxbai-embed-large": {"input": 0.0, "output": 0.0},
    # Commercial APIs (Fallback / Enterprise)
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
}


def calculate_llm_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate estimated cost for an LLM call.

    Args:
        model_name: Name of the model used (e.g., "qwen3.5:9b", "gpt-4o")
        input_tokens: Number of prompt tokens
        output_tokens: Number of completion tokens

    Returns:
        Estimated cost in USD
    """
    # Normalize model name for lookup
    model_key = model_name.lower().strip()

    # Fallback to cheapest commercial model if unknown
    pricing = MODEL_PRICING.get(model_key, MODEL_PRICING["gpt-4o-mini"])

    input_cost = (input_tokens / 1000.0) * pricing["input"]
    output_cost = (output_tokens / 1000.0) * pricing["output"]

    return round(input_cost + output_cost, 6)


def get_model_info(model_name: str) -> dict:
    """Get pricing info for a model."""
    model_key = model_name.lower().strip()
    return MODEL_PRICING.get(model_key, {"input": 0.0, "output": 0.0, "unknown": True})
