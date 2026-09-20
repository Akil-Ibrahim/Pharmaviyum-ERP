from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.db.session import AsyncSessionLocal


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is not None:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()


@asynccontextmanager
async def uow_scope() -> AsyncIterator[UnitOfWork]:
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        try:
            yield uow
        finally:
            await session.close()
