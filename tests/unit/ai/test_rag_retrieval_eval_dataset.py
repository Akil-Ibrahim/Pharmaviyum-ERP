from scripts.evaluate_rag_retrieval import (
    CORPUS,
    GOLDEN_SET,
    _chunk_id,
    _validate_dataset,
)


def test_synthetic_retrieval_golden_set_has_valid_relevant_chunks():
    _validate_dataset()
    primary_keys = {chunk.key for chunk in CORPUS if chunk.tenant == "primary"}

    assert len(GOLDEN_SET) == 30
    assert all(set(case.relevant_chunk_keys) <= primary_keys for case in GOLDEN_SET)
    assert len({_chunk_id(chunk.key) for chunk in CORPUS}) == len(CORPUS)


def test_synthetic_retrieval_corpus_contains_cross_tenant_decoys():
    assert any(chunk.tenant == "other" for chunk in CORPUS)
    assert all(
        case.relevant_chunk_keys
        and all(
            next(chunk for chunk in CORPUS if chunk.key == key).tenant == "primary"
            for key in case.relevant_chunk_keys
        )
        for case in GOLDEN_SET
    )
