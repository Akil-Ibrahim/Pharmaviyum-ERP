import asyncio
import os

from src.pharmaviyum.db.base import Base
from src.pharmaviyum.db.session import engine

# Import all models so SQLAlchemy metadata is fully populated.
import src.pharmaviyum.models.order  # noqa: F401
import src.pharmaviyum.models.patients  # noqa: F401
import src.pharmaviyum.models.product  # noqa: F401
import src.pharmaviyum.models.user  # noqa: F401


async def init_db() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set to initialize the database")

    print(f"Initializing database at {database_url}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database schema created successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
