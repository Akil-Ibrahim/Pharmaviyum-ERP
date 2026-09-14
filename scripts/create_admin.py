"""
Script to create admin user in database.
Best Practice: Use password hashing (bcrypt) for security.
"""
import asyncio
import structlog
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.pharmaviyum.config import settings
from src.pharmaviyum.database import AsyncSessionLocal, engine, Base

logger = structlog.get_logger()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_admin():
    """Create admin user if not exists."""
    logger.info("creating_admin_user")
    
    async with AsyncSessionLocal() as db:
        # Check if admin already exists
        # Replace 'User' with your actual model import
        try:
            from src.pharmaviyum.models.user import User
            
            result = await db.execute(
                select(User).where(User.email == settings.ADMIN_EMAIL)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.info("admin_already_exists", email=settings.ADMIN_EMAIL)
                return
            
            # Create new admin
            admin = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=pwd_context.hash(settings.ADMIN_PASSWORD),
                is_active=True,
                is_superuser=True,
                username="Admin",
            )
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
            
            logger.info("admin_created", email=settings.ADMIN_EMAIL)
            print(f"✅ Admin created: {settings.ADMIN_EMAIL}")
            
        except ImportError:
            logger.error("user_model_not_found")
            print("❌ User model not found. Check src/pharmaviyum/models/user.py")
        except Exception as e:
            logger.error("admin_creation_failed", error=str(e))
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_admin())
