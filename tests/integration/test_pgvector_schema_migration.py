"""Integration checks for the pgvector schema created by Alembic."""

import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.pharmaviyum.ai.mortarium_rag.vector_store import PgVectorStore


@pytest.mark.integration
@pytest.mark.asyncio
async def test_alembic_provisions_pgvector_table_and_search_indexes():
    migration_url = os.environ.get("MIGRATION_TEST_DATABASE_URL")
    if not migration_url:
        pytest.skip(
            "MIGRATION_TEST_DATABASE_URL is required for migration schema checks"
        )

    engine = create_async_engine(migration_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("""
                    SELECT
                        to_regclass('public.document_chunks') IS NOT NULL AS table_exists,
                        to_regtype('vector') IS NOT NULL AS vector_type_exists,
                        (
                            SELECT attribute.atttypmod
                            FROM pg_attribute AS attribute
                            WHERE attribute.attrelid = to_regclass('public.document_chunks')
                              AND attribute.attname = 'embedding'
                              AND NOT attribute.attisdropped
                        ) AS embedding_dimensions,
                        COALESCE(
                            (
                                SELECT array_agg(indexname)
                                FROM pg_indexes
                                WHERE schemaname = 'public'
                                  AND tablename = 'document_chunks'
                            ),
                            ARRAY[]::text[]
                        ) AS index_names
                    """))
            schema = result.one()
    finally:
        await engine.dispose()

    assert schema.table_exists
    assert schema.vector_type_exists
    assert schema.embedding_dimensions == 1024
    assert {
        "idx_document_chunks_embedding",
        "idx_document_chunks_metadata",
        "idx_document_chunks_pharmacy_id",
        "idx_document_chunks_content_fts",
        "idx_document_chunks_content_fts_simple",
    }.issubset(set(schema.index_names or ()))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vector_store_verifies_tables_in_the_active_search_path():
    migration_url = os.environ.get("MIGRATION_TEST_DATABASE_URL")
    if not migration_url:
        pytest.skip(
            "MIGRATION_TEST_DATABASE_URL is required for migration schema checks"
        )

    schema_name = f"rag_verify_{uuid4().hex}"
    admin_engine = create_async_engine(migration_url, pool_pre_ping=True)
    scoped_engine = None
    try:
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
            await connection.execute(
                text(
                    f"""
                    CREATE TABLE "{schema_name}".evaluation_chunks (
                        id UUID PRIMARY KEY,
                        document_id UUID NOT NULL,
                        content TEXT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        chunk_type VARCHAR(50) NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        token_count INTEGER NOT NULL,
                        embedding vector(3),
                        created_at TIMESTAMP DEFAULT NOW(),
                        CONSTRAINT unique_chunk UNIQUE (document_id, chunk_index)
                    )
                    """
                )
            )
            await connection.execute(
                text(
                    f"""
                    CREATE INDEX idx_evaluation_chunks_embedding
                    ON "{schema_name}".evaluation_chunks
                    USING hnsw (embedding vector_cosine_ops)
                    """
                )
            )
            await connection.execute(
                text(
                    f"""
                    CREATE INDEX idx_evaluation_chunks_metadata
                    ON "{schema_name}".evaluation_chunks USING gin (metadata)
                    """
                )
            )
            await connection.execute(
                text(
                    f"""
                    CREATE INDEX idx_evaluation_chunks_pharmacy_id
                    ON "{schema_name}".evaluation_chunks ((metadata ->> 'pharmacy_id'))
                    """
                )
            )
            await connection.execute(
                text(
                    f"""
                    CREATE INDEX idx_evaluation_chunks_content_fts
                    ON "{schema_name}".evaluation_chunks
                    USING gin (to_tsvector('english', content))
                    """
                )
            )
            await connection.execute(
                text(
                    f"""
                    CREATE INDEX idx_evaluation_chunks_content_fts_simple
                    ON "{schema_name}".evaluation_chunks
                    USING gin (to_tsvector('simple', content))
                    """
                )
            )

        scoped_engine = create_async_engine(
            migration_url,
            pool_pre_ping=True,
            connect_args={"server_settings": {"search_path": f"{schema_name},public"}},
        )
        store = PgVectorStore(
            session_factory=async_sessionmaker(scoped_engine, expire_on_commit=False),
            table_name="evaluation_chunks",
            dimensions=3,
        )
        await store.initialize()
    finally:
        if scoped_engine is not None:
            await scoped_engine.dispose()
        async with admin_engine.begin() as connection:
            await connection.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            )
        await admin_engine.dispose()
