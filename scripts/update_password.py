"""Update the password of the configured existing superuser."""

import asyncio

from passlib.context import CryptContext
from sqlalchemy import or_, select

from src.pharmaviyum.config import settings
from src.pharmaviyum.database import AsyncSessionLocal
from src.pharmaviyum.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def update_password() -> None:
    if not settings.ADMIN_PASSWORD:
        raise RuntimeError(
            "ADMIN_PASSWORD must be explicitly configured before updating an admin password."
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

        if admin is None:
            raise RuntimeError("Configured administrator account was not found.")
        if not admin.is_superuser:
            raise RuntimeError(
                "The configured account is not a superuser; refusing password update."
            )

        admin.hashed_password = pwd_context.hash(settings.ADMIN_PASSWORD)
        await db.commit()
        print("Administrator password updated.")


if __name__ == "__main__":
    asyncio.run(update_password())
