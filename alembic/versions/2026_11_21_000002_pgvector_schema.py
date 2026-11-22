"""Provision the pgvector schema before application runtime connects."""

from alembic import op

revision = "2026_11_21_000002"
down_revision = "2026_11_21_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the RAG schema and indexes under the migration credential."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.document_chunks (
            id UUID PRIMARY KEY,
            document_id UUID NOT NULL,
            content TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_type VARCHAR(50) NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            token_count INTEGER NOT NULL,
            embedding vector(1024),
            created_at TIMESTAMP DEFAULT NOW(),
            CONSTRAINT unique_chunk UNIQUE (document_id, chunk_index)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
        ON public.document_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata
        ON public.document_chunks USING gin (metadata)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_pharmacy_id
        ON public.document_chunks ((metadata ->> 'pharmacy_id'))
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_content_fts
        ON public.document_chunks USING gin (to_tsvector('english', content))
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_content_fts_simple
        ON public.document_chunks USING gin (to_tsvector('simple', content))
        """
    )
    op.execute(
        """
        DO $$
        DECLARE
            embedding_dimensions integer;
        BEGIN
            SELECT atttypmod
            INTO embedding_dimensions
            FROM pg_attribute
            WHERE attrelid = 'public.document_chunks'::regclass
              AND attname = 'embedding'
              AND NOT attisdropped;

            IF embedding_dimensions IS DISTINCT FROM 1024 THEN
                RAISE EXCEPTION
                    'document_chunks.embedding must be vector(1024); found typmod %',
                    embedding_dimensions;
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    """Retain the RAG schema and indexed content during application rollback.

    Dropping document_chunks would irreversibly delete ingested pharmacy
    knowledge. Schema retirement and data deletion require a separate,
    explicitly approved archival/purge operation.
    """
    # Intentionally non-destructive: keep the extension, table, data, and indexes.
    return
