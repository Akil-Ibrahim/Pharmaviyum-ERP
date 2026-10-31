from src.pharmaviyum.ai.harness.agent_harness import AgentHarness


def test_cache_context_preserves_prescription_scope() -> None:
    context = {
        "user_id": "user-1",
        "pharmacy_id": 7,
        "prescription_id": "rx-1001",
    }

    cache_context = AgentHarness._cache_context(context)

    assert cache_context["prescription_id"] == "rx-1001"


def test_cache_context_does_not_mix_distinct_prescriptions() -> None:
    first = AgentHarness._cache_context(
        {"user_id": "user-1", "pharmacy_id": 7, "prescription_id": "rx-1001"}
    )
    second = AgentHarness._cache_context(
        {"user_id": "user-1", "pharmacy_id": 7, "prescription_id": "rx-1002"}
    )

    assert first != second
