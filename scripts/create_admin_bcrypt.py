import asyncio
import bcrypt
from sqlalchemy import delete, select
from src.pharmaviyum.config import settings
from src.pharmaviyum.database import AsyncSessionLocal
from src.pharmaviyum.models.user import User


async def recreate():
    async with AsyncSessionLocal() as db:
        await db.execute(delete(User))
        await db.commit()
        print("️ Deleted all users")

        # Хешируем через bcrypt напрямую
        hashed = bcrypt.hashpw(
            settings.ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        print(f"🔐 Hash: {hashed[:30]}...")

        admin = User(
            email=settings.ADMIN_EMAIL,
            username=settings.ADMIN_EMAIL,
            hashed_password=hashed,
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)
        await db.commit()

        result = await db.execute(select(User))
        user = result.scalar()
        print(f"✅ Admin created!")
        print(f"   Login: {user.email}")
        print(f"   Password: {settings.ADMIN_PASSWORD}")


asyncio.run(recreate())
