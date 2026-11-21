"""Integration checks for the pgvector schema created by Alembic."""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


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
            result = await connection.execute(
                text(
                    """
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
                    """
                )
            )
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
