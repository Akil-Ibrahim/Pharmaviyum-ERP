"""Tests for read-only verification of the Alembic-managed pgvector schema."""

from types import SimpleNamespace

import pytest

from src.pharmaviyum.ai.mortarium_rag.vector_store import PgVectorStore

REQUIRED_INDEXES = {
    "idx_document_chunks_embedding",
    "idx_document_chunks_metadata",
    "idx_document_chunks_pharmacy_id",
    "idx_document_chunks_content_fts",
    "idx_document_chunks_content_fts_simple",
}


class _Result:
    def __init__(self, row):
        self._row = row

    def one(self):
        return self._row


class _Session:
    def __init__(self, row):
        self.row = row
        self.statement = None
        self.params = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def execute(self, statement, params=None):
        self.statement = statement
        self.params = params
        return _Result(self.row)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialize_only_verifies_the_migrated_schema():
    session = _Session(
        SimpleNamespace(
            table_exists=True,
            vector_type_exists=True,
            embedding_dimensions=1024,
            index_names=sorted(REQUIRED_INDEXES),
        )
    )
    store = PgVectorStore(session_factory=lambda: session)

    await store.initialize()

    sql = str(session.statement).upper()
    assert sql.lstrip().startswith("SELECT")
    assert "CREATE " not in sql
    assert session.params == {
        "qualified_table": "public.document_chunks",
        "table_name": "document_chunks",
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialize_fails_when_migration_has_not_created_the_table():
    session = _Session(
        SimpleNamespace(
            table_exists=False,
            vector_type_exists=True,
            embedding_dimensions=None,
            index_names=[],
        )
    )
    store = PgVectorStore(session_factory=lambda: session)

    with pytest.raises(RuntimeError, match="apply the Alembic database migrations"):
        await store.initialize()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialize_rejects_a_vector_dimension_mismatch():
    session = _Session(
        SimpleNamespace(
            table_exists=True,
            vector_type_exists=True,
            embedding_dimensions=1536,
            index_names=sorted(REQUIRED_INDEXES),
        )
    )
    store = PgVectorStore(session_factory=lambda: session, dimensions=1024)

    with pytest.raises(RuntimeError, match="dimension mismatch"):
        await store.initialize()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_initialize_rejects_missing_search_indexes():
    session = _Session(
        SimpleNamespace(
            table_exists=True,
            vector_type_exists=True,
            embedding_dimensions=1024,
            index_names=["idx_document_chunks_embedding"],
        )
    )
    store = PgVectorStore(session_factory=lambda: session)

    with pytest.raises(RuntimeError, match="missing required indexes"):
        await store.initialize()
