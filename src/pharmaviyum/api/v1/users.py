from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.models.user import User
from src.pharmaviyum.models.user_avatar import UserAvatar
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser, CurrentUser
from src.pharmaviyum.services.profile_avatar import get_profile_avatar_content_type
from src.pharmaviyum.schemas.user_schema import UserCreate, UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_AVATAR_BYTES = 2 * 1024 * 1024
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/avatar", response_class=Response)
async def get_my_avatar(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Return the authenticated user's own profile photo."""
    result = await db.execute(
        select(UserAvatar).where(UserAvatar.user_id == current_user.id)
    )
    avatar = result.scalar_one_or_none()
    if avatar is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile photo not found",
        )

    return Response(
        content=avatar.avatar_data,
        media_type=avatar.content_type,
        headers={
            "Cache-Control": "private, max-age=300",
            "Vary": "Authorization",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.put("/me/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def upload_my_avatar(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Validate and persist the authenticated user's profile photo."""
    contents = await file.read(MAX_AVATAR_BYTES + 1)
    if len(contents) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Profile photo must be 2 MB or smaller",
        )

    try:
        content_type = get_profile_avatar_content_type(contents)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    result = await db.execute(
        select(UserAvatar).where(UserAvatar.user_id == current_user.id)
    )
    avatar = result.scalar_one_or_none()
    if avatar is None:
        avatar = UserAvatar(
            user_id=current_user.id,
            avatar_data=contents,
            content_type=content_type,
        )
    else:
        avatar.avatar_data = contents
        avatar.content_type = content_type
    db.add(avatar)
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_avatar(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Remove the authenticated user's profile photo from PostgreSQL."""
    result = await db.execute(
        select(UserAvatar).where(UserAvatar.user_id == current_user.id)
    )
    avatar = result.scalar_one_or_none()
    if avatar is not None:
        await db.delete(avatar)
        await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/", response_model=List[UserResponse])
async def list_users(
    _: CurrentSuperuser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.id).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    _: CurrentSuperuser,
    db: AsyncSession = Depends(get_db),
):
    username = data.username.strip()
    email = (
        str(data.email).strip().lower()
        if data.email
        else f"{username}@pharmaviyum.local"
    )
    result = await db.execute(
        select(User).where((User.username == username) | (User.email == email))
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = User(
        username=username,
        email=email,
        hashed_password=pwd_context.hash(data.password[:72]),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    _: CurrentSuperuser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
