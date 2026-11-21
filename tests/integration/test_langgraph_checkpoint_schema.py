"""Integration checks for Alembic-managed LangGraph checkpoint tables."""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.integration
@pytest.mark.asyncio
async def test_alembic_provisions_langgraph_checkpoint_schema():
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
                        to_regclass('public.checkpoint_migrations') IS NOT NULL,
                        to_regclass('public.checkpoints') IS NOT NULL,
                        to_regclass('public.checkpoint_blobs') IS NOT NULL,
                        to_regclass('public.checkpoint_writes') IS NOT NULL,
                        EXISTS (
                            SELECT 1
                            FROM pg_attribute
                            WHERE attrelid = to_regclass('public.checkpoint_writes')
                              AND attname = 'task_path'
                              AND NOT attisdropped
                        ),
                        EXISTS (
                            SELECT 1
                            FROM pg_attribute
                            WHERE attrelid = to_regclass('public.checkpoint_blobs')
                              AND attname = 'blob'
                              AND NOT attisdropped
                              AND NOT attnotnull
                        ),
                        COALESCE(
                            (
                                SELECT array_agg(indexname)
                                FROM pg_indexes
                                WHERE schemaname = 'public'
                                  AND indexname IN (
                                      'checkpoints_thread_id_idx',
                                      'checkpoint_blobs_thread_id_idx',
                                      'checkpoint_writes_thread_id_idx'
                                  )
                            ),
                            ARRAY[]::text[]
                        )
                    """))
            schema = result.one()
            version_result = await connection.execute(
                text("SELECT max(v) FROM public.checkpoint_migrations")
            )
            migration_version = version_result.scalar_one()
    finally:
        await engine.dispose()

    assert all(schema[:6])
    assert {
        "checkpoints_thread_id_idx",
        "checkpoint_blobs_thread_id_idx",
        "checkpoint_writes_thread_id_idx",
    }.issubset(set(schema[6] or ()))
    assert migration_version == 9
