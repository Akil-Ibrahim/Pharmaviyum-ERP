"""Database readiness checker with bounded retries for transient failures."""

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)


def _is_transient_database_error(exc: BaseException) -> bool:
    """Retry operational failures and DBAPI errors that invalidate the connection.

    Programming, integrity, and other permanent SQLAlchemy failures must fail
    readiness immediately rather than being retried for several minutes.
    """
    return isinstance(exc, OperationalError) or (
        isinstance(exc, DBAPIError) and exc.connection_invalidated
    )


@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception(_is_transient_database_error),
    reraise=True,
)
async def wait_for_database(engine) -> bool:
    """Wait for database with retries: 2s, 4s, 8s, 16s, 30s..."""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        result.scalar()
        print("✅ Database is ready")
        return True


async def check_database_health(engine) -> dict:
    """Check database health status for /health endpoint."""
    try:
        async with engine.connect() as conn:
            version_result = await conn.execute(text("SELECT version()"))
            version = version_result.scalar()
            pool = engine.pool
            return {
                "status": "healthy",
                "version": version,
                "pool": {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                },
            }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
