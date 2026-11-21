"""Create or synchronize the configured superuser without unsafe defaults."""

import asyncio

from passlib.context import CryptContext
from sqlalchemy import or_, select

from src.pharmaviyum.config import settings
from src.pharmaviyum.database import AsyncSessionLocal
from src.pharmaviyum.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_admin() -> None:
    """Create or update only the configured admin account."""
    if not settings.ADMIN_PASSWORD:
        raise RuntimeError(
            "ADMIN_PASSWORD must be explicitly configured before bootstrapping an admin."
        )

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(
                or_(
                    User.email == settings.ADMIN_EMAIL,
                    User.username == settings.ADMIN_USER,
                )
            )
        )
        admin = result.scalar_one_or_none()

        if admin is not None and not admin.is_superuser:
            raise RuntimeError(
                "The configured admin identity belongs to a non-superuser; "
                "refusing to elevate it automatically."
            )

        if admin is None:
            admin = User(
                email=settings.ADMIN_EMAIL,
                username=settings.ADMIN_USER,
                hashed_password=pwd_context.hash(settings.ADMIN_PASSWORD),
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
        else:
            admin.hashed_password = pwd_context.hash(settings.ADMIN_PASSWORD)
            admin.is_active = True

        await db.commit()
        print("Configured administrator account is ready.")


if __name__ == "__main__":
    asyncio.run(create_admin())
