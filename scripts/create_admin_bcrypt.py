"""Safely create or update one configured administrator using bcrypt.

This compatibility script never deletes existing users and never prints credentials.
"""

import asyncio

import bcrypt
from sqlalchemy import or_, select

from src.pharmaviyum.config import settings
from src.pharmaviyum.database import AsyncSessionLocal
from src.pharmaviyum.models.user import User


async def recreate() -> None:
    if not settings.ADMIN_PASSWORD:
        raise RuntimeError(
            "ADMIN_PASSWORD must be explicitly configured before bootstrapping an admin."
        )

    password_hash = bcrypt.hashpw(
        settings.ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

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
                hashed_password=password_hash,
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
        else:
            admin.hashed_password = password_hash
            admin.is_active = True

        await db.commit()
        print("Configured administrator account is ready; existing users were preserved.")


if __name__ == "__main__":
    asyncio.run(recreate())
