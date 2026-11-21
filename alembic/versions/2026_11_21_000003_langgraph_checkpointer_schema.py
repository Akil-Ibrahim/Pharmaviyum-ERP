"""Provision LangGraph PostgreSQL checkpoint tables through Alembic."""

from alembic import op

revision = "2026_11_21_000003"
down_revision = "2026_11_21_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the checkpoint schema and match langgraph-checkpoint-postgres 3.1.3."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.checkpoint_migrations (
            v INTEGER PRIMARY KEY
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.checkpoints (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            checkpoint_id TEXT NOT NULL,
            parent_checkpoint_id TEXT,
            type TEXT,
            checkpoint JSONB NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}',
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.checkpoint_blobs (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            channel TEXT NOT NULL,
            version TEXT NOT NULL,
            type TEXT NOT NULL,
            blob BYTEA,
            PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.checkpoint_writes (
            thread_id TEXT NOT NULL,
            checkpoint_ns TEXT NOT NULL DEFAULT '',
            checkpoint_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            idx INTEGER NOT NULL,
            channel TEXT NOT NULL,
            type TEXT,
            blob BYTEA NOT NULL,
            task_path TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
        )
        """
    )
    op.execute(
        "ALTER TABLE public.checkpoint_blobs ALTER COLUMN blob DROP NOT NULL"
    )
    op.execute(
        """
        ALTER TABLE public.checkpoint_writes
        ADD COLUMN IF NOT EXISTS task_path TEXT NOT NULL DEFAULT ''
        """
    )

    # LangGraph's upstream migrations create these indexes CONCURRENTLY.
    # Keep that behavior for existing checkpoint tables with live data.
    with op.get_context().autocommit_block():
        op.execute(
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS checkpoints_thread_id_idx
            ON public.checkpoints(thread_id)
            """
        )
        op.execute(
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS checkpoint_blobs_thread_id_idx
            ON public.checkpoint_blobs(thread_id)
            """
        )
        op.execute(
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS checkpoint_writes_thread_id_idx
            ON public.checkpoint_writes(thread_id)
            """
        )

    # Version numbers mirror the 10-entry MIGRATIONS list in the pinned
    # langgraph-checkpoint-postgres 3.1.3 package (0 through 9).
    op.execute(
        """
        INSERT INTO public.checkpoint_migrations (v)
        VALUES (0), (1), (2), (3), (4), (5), (6), (7), (8), (9)
        ON CONFLICT (v) DO NOTHING
        """
    )


def downgrade() -> None:
    """Preserve agent history; checkpoint data is not safe to delete on rollback."""
    # Intentionally non-destructive. Explicit retention/purge is a separate
    # operational action with backup and approval requirements.
    return
