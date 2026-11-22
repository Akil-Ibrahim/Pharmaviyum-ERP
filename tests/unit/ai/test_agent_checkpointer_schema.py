"""Tests for read-only verification of the LangGraph checkpoint schema."""

from types import SimpleNamespace

import pytest

from src.pharmaviyum.ai.agents.checkpointer import AgentCheckpointer

REQUIRED_INDEXES = [
    "checkpoints_thread_id_idx",
    "checkpoint_blobs_thread_id_idx",
    "checkpoint_writes_thread_id_idx",
]


class _Cursor:
    def __init__(self, schema_row, version_row):
        self.schema_row = schema_row
        self.version_row = version_row
        self.statements = []
        self._last_statement = ""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def execute(self, statement):
        self._last_statement = str(statement)
        self.statements.append(self._last_statement)

    async def fetchone(self):
        if "SELECT max(v)" in self._last_statement:
            return self.version_row
        return self.schema_row


class _Connection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


class _ConnectionContext:
    def __init__(self, connection):
        self.connection_value = connection

    async def __aenter__(self):
        return self.connection_value

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class _Pool:
    def __init__(self, connection):
        self._connection = connection

    def connection(self):
        return _ConnectionContext(self._connection)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_checkpoint_schema_verification_is_read_only():
    cursor = _Cursor(
        (True, True, True, True, True, True, REQUIRED_INDEXES),
        (9,),
    )
    checkpointer = AgentCheckpointer("postgresql://unused")
    checkpointer._pool = _Pool(_Connection(cursor))
    checkpointer._saver = SimpleNamespace(MIGRATIONS=[None] * 10)

    await checkpointer._verify_schema()

    assert len(cursor.statements) == 2
    assert all(
        statement.lstrip().upper().startswith("SELECT")
        for statement in cursor.statements
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_checkpoint_schema_verification_rejects_missing_tables_or_columns():
    cursor = _Cursor((True, True, False, True, True, True, REQUIRED_INDEXES), (9,))
    checkpointer = AgentCheckpointer("postgresql://unused")
    checkpointer._pool = _Pool(_Connection(cursor))
    checkpointer._saver = SimpleNamespace(MIGRATIONS=[None] * 10)

    with pytest.raises(RuntimeError, match="schema is incomplete"):
        await checkpointer._verify_schema()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_checkpoint_schema_verification_rejects_outdated_migration_version():
    cursor = _Cursor(
        (True, True, True, True, True, True, REQUIRED_INDEXES),
        (8,),
    )
    checkpointer = AgentCheckpointer("postgresql://unused")
    checkpointer._pool = _Pool(_Connection(cursor))
    checkpointer._saver = SimpleNamespace(MIGRATIONS=[None] * 10)

    with pytest.raises(RuntimeError, match="version mismatch"):
        await checkpointer._verify_schema()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_checkpoint_schema_verification_rejects_missing_indexes():
    cursor = _Cursor(
        (True, True, True, True, True, True, ["checkpoints_thread_id_idx"]),
        (9,),
    )
    checkpointer = AgentCheckpointer("postgresql://unused")
    checkpointer._pool = _Pool(_Connection(cursor))
    checkpointer._saver = SimpleNamespace(MIGRATIONS=[None] * 10)

    with pytest.raises(RuntimeError, match="missing indexes"):
        await checkpointer._verify_schema()
