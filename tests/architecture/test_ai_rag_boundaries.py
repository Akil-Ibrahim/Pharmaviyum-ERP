"""Architecture contracts for the AI/RAG boundary."""

from pathlib import Path


RAG_GRAPH = Path("src/pharmaviyum/ai/rag/graph.py")


def test_rag_orchestrator_does_not_import_concrete_infrastructure():
    source = RAG_GRAPH.read_text(encoding="utf-8")

    assert "from .vector_store import PgVectorStore" not in source
    assert "from .embeddings import EmbeddingsProvider" not in source


def test_rag_orchestrator_depends_on_ai_ports():
    source = RAG_GRAPH.read_text(encoding="utf-8")

    assert "from .ports import" in source
    assert "RetrieverPort" in source
    assert "EmbeddingsPort" in source
    assert "LLMPort" in source


def test_rag_graph_has_no_crm_mutation_dependencies():
    source = RAG_GRAPH.read_text(encoding="utf-8")

    forbidden = (
        "src.pharmaviyum.models.",
        "src.pharmaviyum.repositories.",
        "src.pharmaviyum.services.",
    )
    assert not any(marker in source for marker in forbidden)
