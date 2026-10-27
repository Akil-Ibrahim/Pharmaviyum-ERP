"""Transaction-boundary tests for the generic async repository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.pharmaviyum.db.repository import AsyncRepository

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_add_flushes_without_committing_the_caller_transaction() -> None:
    session = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    obj = MagicMock()
    repository = AsyncRepository(model=object, session=session)

    result = await repository.add(obj)

    assert result is obj
    session.add.assert_called_once_with(obj)
    session.flush.assert_awaited_once_with()
    session.refresh.assert_awaited_once_with(obj)
    session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_delete_flushes_without_committing_the_caller_transaction() -> None:
    session = MagicMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    obj = MagicMock()
    repository = AsyncRepository(model=object, session=session)

    await repository.delete(obj)

    session.delete.assert_awaited_once_with(obj)
    session.flush.assert_awaited_once_with()
    session.commit.assert_not_called()
