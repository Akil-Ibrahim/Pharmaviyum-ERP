"""Pre-migration hooks."""

import shutil
from sqlalchemy import text


async def pre_migration_hook(engine, environment: str = "development"):
    """Execute pre-migration checks."""
    print("Running pre-migration checks...")
    await _check_database_connection(engine)
    _check_disk_space()
    print("Pre-migration checks passed")


async def _check_database_connection(engine):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("  Database connection verified")
    except Exception as e:
        raise RuntimeError(f"Cannot connect to database: {e}")


def _check_disk_space(min_free_gb: float = 1.0):
    total, used, free = shutil.disk_usage("/")
    free_gb = free / (1024**3)

    if free_gb < min_free_gb:
        raise RuntimeError(f"Insufficient disk space: {free_gb:.2f}GB")
    print(f"  Disk space: {free_gb:.2f}GB free")
