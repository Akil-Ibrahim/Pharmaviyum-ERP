import asyncio
from passlib.context import CryptContext
from sqlalchemy import select
from src.pharmaviyum.config import settings
from src.pharmaviyum.database import AsyncSessionLocal
from src.pharmaviyum.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def update_password():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            print(f"❌ Admin not found: {settings.ADMIN_EMAIL}")
            return

        admin.hashed_password = pwd_context.hash(settings.ADMIN_PASSWORD)
        await db.commit()
        print(f"✅ Password updated for: {settings.ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(update_password())
