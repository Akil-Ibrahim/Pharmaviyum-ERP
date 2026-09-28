from src.pharmaviyum.ai.mortarium_rag.graph import LangGraphRAG
from src.pharmaviyum.ai.mortarium_rag.pipeline import RAGPipeline
from src.pharmaviyum.ai.mortarium_rag.schemas import QueryContext


def test_legacy_rag_halal_filter_requires_halal_status() -> None:
    context = QueryContext(user_id="u1", pharmacy_id=1, halal_filter=True)

    assert RAGPipeline._build_filters(context)["halal_status"] == "halal"


def test_langgraph_rag_halal_filter_requires_halal_status() -> None:
    context = QueryContext(user_id="u1", pharmacy_id=1, halal_filter=True)

    assert LangGraphRAG._build_filters(context)["halal_status"] == "halal"


def test_halal_filter_disabled_does_not_add_halal_constraint() -> None:
    context = QueryContext(user_id="u1", pharmacy_id=1, halal_filter=False)

    filters = RAGPipeline._build_filters(context)

    assert "halal_status" not in filters
