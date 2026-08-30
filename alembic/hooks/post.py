"""Post-migration hooks."""
from sqlalchemy import text


async def post_migration_hook(engine, environment: str = "development"):
    """Execute post-migration cleanup."""
    print("Running post-migration cleanup...")
    await _update_statistics(engine)
    print("Post-migration cleanup complete")


async def _update_statistics(engine):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("ANALYZE"))
        print("  Database statistics updated")
    except Exception as e:
        print(f"  Failed to update statistics: {e}")
