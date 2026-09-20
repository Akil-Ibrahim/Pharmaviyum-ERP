#!/usr/bin/env python3
"""
Create a superuser account.

Usage:
    python scripts/create_superuser.py
"""

import asyncio
from getpass import getpass
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


async def create_superuser():
    """Create a superuser interactively."""
    print("👑 Creating superuser account...")

    # Get user input
    email = input("Email: ").strip()
    full_name = input("Full name: ").strip()
    password = getpass("Password (min 8 chars): ")

    # Validate
    if len(password) < 8:
        print("❌ Password must be at least 8 characters")
        return

    from app.modules.auth.models import User
    from app.modules.auth.security import get_password_hash
    from app.shared.core.database import async_session_factory

    async with async_session_factory() as session:
        # Check if user exists
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"❌ User with email {email} already exists")
            return

        # Create superuser
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            is_active=True,
            is_superuser=True,
        )

        session.add(user)
        await session.commit()

        print(f"✅ Superuser created: {email}")
        print(f"   You can now login at /api/v1/login/access-token")


if __name__ == "__main__":
    asyncio.run(create_superuser())
