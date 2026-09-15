import structlog
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase

from src.pharmaviyum.config import settings

logger = structlog.get_logger()


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_db_and_tables():
    logger.info("creating_database_tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")
