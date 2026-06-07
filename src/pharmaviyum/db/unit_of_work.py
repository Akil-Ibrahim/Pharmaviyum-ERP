from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from src.pharmaviyum.db.session import AsyncSessionLocal


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()


@asynccontextmanager
async def uow_scope():
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        try:
            yield uow
        finally:
            await session.close()
