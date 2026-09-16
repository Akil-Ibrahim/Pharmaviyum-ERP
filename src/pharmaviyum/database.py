"""Database engine, session factory, and PostgreSQL observability."""

from __future__ import annotations

import time

import structlog
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.pharmaviyum.ai.observability.metrics import (
    DB_CONNECTION_HOLD_DURATION,
    DB_POOL_CHECKED_OUT,
    DB_POOL_MAX_OVERFLOW,
    DB_POOL_OVERFLOW,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUTS_TOTAL,
    DB_QUERY_DURATION,
    DB_QUERY_ERRORS_TOTAL,
    DB_QUERY_TOTAL,
)
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


def _pool_metrics() -> None:
    pool = engine.sync_engine.pool
    try:
        DB_POOL_SIZE.set(pool.size())
        DB_POOL_MAX_OVERFLOW.set(getattr(pool, "_max_overflow", settings.DB_MAX_OVERFLOW))
        DB_POOL_CHECKED_OUT.set(pool.checkedout())
        DB_POOL_OVERFLOW.set(pool.overflow())
    except Exception:
        logger.debug("database_pool_metrics_unavailable", exc_info=True)


def _classify_operation(statement: str) -> str:
    first = statement.lstrip().split(None, 1)
    operation = first[0].lower() if first else "other"
    return operation if operation in {"select", "insert", "update", "delete", "merge", "call"} else "other"


@event.listens_for(engine.sync_engine, "connect")
def _on_connect(dbapi_connection, connection_record) -> None:
    _pool_metrics()


@event.listens_for(engine.sync_engine, "checkout")
def _on_checkout(dbapi_connection, connection_record, connection_proxy) -> None:
    connection_record.info["checkout_started_at"] = time.perf_counter()
    _pool_metrics()


@event.listens_for(engine.sync_engine, "checkin")
def _on_checkin(dbapi_connection, connection_record) -> None:
    started = connection_record.info.pop("checkout_started_at", None)
    if started is not None:
        DB_CONNECTION_HOLD_DURATION.observe(time.perf_counter() - started)
    _pool_metrics()


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany) -> None:
    context._pharmaviyum_query_started_at = time.perf_counter()


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany) -> None:
    started = getattr(context, "_pharmaviyum_query_started_at", None)
    if started is None:
        return
    operation = _classify_operation(statement)
    DB_QUERY_DURATION.labels(operation=operation).observe(time.perf_counter() - started)
    DB_QUERY_TOTAL.labels(operation=operation, status="success").inc()


@event.listens_for(engine.sync_engine, "handle_error")
def _handle_db_error(exception_context) -> None:
    operation = _classify_operation(exception_context.statement or "")
    DB_QUERY_TOTAL.labels(operation=operation, status="error").inc()
    DB_QUERY_ERRORS_TOTAL.labels(operation=operation).inc()
    if exception_context.original_exception.__class__.__name__ == "TimeoutError":
        DB_POOL_TIMEOUTS_TOTAL.inc()
    _pool_metrics()


DB_POOL_SIZE.set(settings.DB_POOL_SIZE)
DB_POOL_MAX_OVERFLOW.set(settings.DB_MAX_OVERFLOW)

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
