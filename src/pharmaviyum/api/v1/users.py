from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.models.user import User
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser
from src.pharmaviyum.schemas.user_schema import UserCreate, UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/users", tags=["Users"])


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
    email = str(data.email).strip().lower() if data.email else f"{username}@pharmaviyum.local"
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
