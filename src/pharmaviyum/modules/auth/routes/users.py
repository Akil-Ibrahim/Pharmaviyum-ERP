"""
User management routes.

Matches ibrahimengpy/full-stack-fastapi-template structure exactly:
- GET /users/: List users (superuser only)
- POST /users/: Create user (superuser only, with welcome email)
- GET /users/me: Get current user
- PATCH /users/me: Update own profile
- PATCH /users/me/password: Change own password
- DELETE /users/me: Delete own account
- GET /users/{id}: Get user by ID
- PATCH /users/{id}: Update user (superuser)
- DELETE /users/{id}: Delete user (superuser)
- POST /users/signup: PUBLIC REGISTRATION (no auth required)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from src.pharmaviyum.core.config import settings
from .. import crud
from ..deps import CurrentUser, SessionDep, get_current_active_superuser
from ..schemas import (
    Message,
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from ..security import get_password_hash, verify_password
from ..utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
async def read_users(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> UsersPublic:
    """Retrieve all users (superuser only)."""
    # Count total
    count_statement = select(func.count()).select_from(crud.User)
    count = (await session.execute(count_statement)).scalar_one()

    # Get paginated users
    statement = (
        select(crud.User)
        .order_by(crud.User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    users = (await session.execute(statement)).scalars().all()

    users_public = [UserPublic.model_validate(user) for user in users]

    return UsersPublic(data=users_public, count=count)


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def create_user(session: SessionDep, user_in: UserCreate) -> UserPublic:
    """
    Create new user (superuser only).

    Sends welcome email with password if emails are enabled.
    """
    # Check email uniqueness
    existing = await crud.get_user_by_email(session=session, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system",
        )

    # Create user
    user = await crud.create_user(session=session, user_create=user_in)

    # Send welcome email
    if settings.EMAILS_ENABLED and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email,
            username=user_in.email,
            password=user_in.password,
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )

    return UserPublic.model_validate(user)


@router.patch("/me", response_model=UserPublic)
async def update_user_me(
    session: SessionDep,
    user_in: UserUpdateMe,
    current_user: CurrentUser,
) -> UserPublic:
    """Update own user profile."""
    # Check email uniqueness if changing email
    if user_in.email:
        existing = await crud.get_user_by_email(session=session, email=user_in.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

    # Update user
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)

    return UserPublic.model_validate(current_user)


@router.patch("/me/password", response_model=Message)
async def update_password_me(
    session: SessionDep,
    body: UpdatePassword,
    current_user: CurrentUser,
) -> Message:
    """Change own password."""
    # Verify current password
    verified = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )

    # Prevent same password
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current one",
        )

    # Update password
    current_user.hashed_password = get_password_hash(body.new_password)
    session.add(current_user)
    await session.commit()

    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> UserPublic:
    """Get current user."""
    return UserPublic.model_validate(current_user)


@router.delete("/me", response_model=Message)
async def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Message:
    """
    Delete own account.

    SECURITY: Superusers cannot delete themselves (prevents accidental lockout).
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super users are not allowed to delete themselves",
        )

    await session.delete(current_user)
    await session.commit()

    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
async def register_user(session: SessionDep, user_in: UserRegister) -> UserPublic:
    """
    PUBLIC REGISTRATION endpoint (no authentication required).

    Users can create their own accounts.
    New users are NOT superusers (security).
    """
    # Check email uniqueness
    existing = await crud.get_user_by_email(session=session, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system",
        )

    # Create user (is_superuser always False for public signup)
    user_create = UserCreate.model_validate(user_in)
    user = await crud.create_user(session=session, user_create=user_create)

    return UserPublic.model_validate(user)


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> UserPublic:
    """Get a specific user by ID."""
    user = await session.get(crud.User, user_id)

    # Allow users to read their own profile
    if user == current_user:
        return UserPublic.model_validate(user)

    # Others require superuser privileges
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserPublic.model_validate(user)


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def update_user(
    session: SessionDep,
    user_id: int,
    user_in: UserUpdate,
) -> UserPublic:
    """Update a user (superuser only)."""
    db_user = await session.get(crud.User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )

    # Check email uniqueness
    if user_in.email:
        existing = await crud.get_user_by_email(session=session, email=user_in.email)
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

    # Update user
    db_user = await crud.update_user(session=session, db_user=db_user, user_in=user_in)

    return UserPublic.model_validate(db_user)


@router.delete(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
)
async def delete_user(
    session: SessionDep,
    current_user: CurrentUser,
    user_id: int,
) -> Message:
    """Delete a user (superuser only)."""
    user = await session.get(crud.User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent superusers from deleting themselves
    if user == current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super users are not allowed to delete themselves",
        )

    await session.delete(user)
    await session.commit()

    return Message(message="User deleted successfully")
