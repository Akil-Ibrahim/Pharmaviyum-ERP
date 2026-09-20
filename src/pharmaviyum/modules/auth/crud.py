"""
CRUD operations for User model.

Functions:
- get_user_by_email: Find user by email
- get_user_by_id: Find user by ID
- authenticate: Verify email + password (constant-time)
- create_user: Create new user with hashed password
- update_user: Update user details
- delete_user: Delete user
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User
from .schemas import UserCreate, UserUpdate
from .security import get_password_hash, verify_password


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Find a user by email address."""
    statement = select(User).where(User.email == email)
    return (await session.execute(statement)).scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: Any) -> User | None:
    """Find a user by ID."""
    return await session.get(User, user_id)


async def authenticate(session: AsyncSession, email: str, password: str) -> User | None:
    """
    Authenticate user by email and password.

    Returns:
        User if credentials are valid, None otherwise

    Security:
    - verify_password is constant-time internally (passlib)
    - Runs dummy hash check for non-existent users to prevent timing attacks
    """
    user = await get_user_by_email(session=session, email=email)
    if not user:
        # Run hash anyway to prevent timing attacks
        # This makes the response time consistent whether user exists or not
        verify_password(password, get_password_hash("dummy"))
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    """
    Create a new user with hashed password.

    Args:
        session: Database session
        user_create: User data with plain text password

    Returns:
        Created user with hashed password
    """
    # Hash the password before storing
    hashed_password = get_password_hash(user_create.password)

    # Create user object
    db_user = User(
        email=user_create.email,
        full_name=user_create.full_name,
        is_active=user_create.is_active,
        is_superuser=user_create.is_superuser,
        hashed_password=hashed_password,
    )

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return db_user


async def update_user(
    session: AsyncSession, db_user: User, user_in: UserUpdate
) -> User:
    """
    Update user details.

    If password is provided, it will be hashed before storing.
    """
    update_data = user_in.model_dump(exclude_unset=True)

    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]

    # Update user attributes
    for field, value in update_data.items():
        setattr(db_user, field, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    return db_user


async def delete_user(session: AsyncSession, user_id: Any) -> None:
    """Delete a user by ID."""
    user = await session.get(User, user_id)
    if user:
        session.delete(user)
        await session.commit()
