from src.pharmaviyum.ai.observability.cost_tracker import calculate_llm_cost


def test_local_qwen_cost_is_zero_api_cost() -> None:
    assert calculate_llm_cost("qwen3:8b", 1000, 500) == 0.0


def test_unknown_model_cost_is_not_fabricated() -> None:
    assert calculate_llm_cost("unlisted-model", 1000, 500) is None


def test_known_cloud_model_cost_uses_configured_rates() -> None:
    assert calculate_llm_cost("gpt-4o-mini", 1000, 1000) == 0.00075
