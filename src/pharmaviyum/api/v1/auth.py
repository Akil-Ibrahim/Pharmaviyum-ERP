"""
Authentication endpoints for user login, registration, and token generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.config import settings
from src.pharmaviyum.core.oauth2 import create_access_token
from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegistrationRequest(BaseModel):
    email: str
    password: str


async def _get_user_by_username_or_email(db: AsyncSession, username_or_email: str):
    if "@" in username_or_email:
        local_part = username_or_email.split("@", 1)[0]
        result = await db.execute(
            select(User).where(
                or_(
                    User.username == username_or_email,
                    User.email == username_or_email,
                    User.username == local_part,
                )
            )
        )
    else:
        result = await db.execute(
            select(User).where(User.username == username_or_email)
        )
    return result.scalar_one_or_none()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegistrationRequest,
    db: AsyncSession = Depends(get_db),
):
    email = payload.email.strip().lower()
    password = payload.password

    if "@" not in email or len(email) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A valid email address is required",
        )
    if len(password) < 7:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 7 characters long",
        )

    username = email.split("@", 1)[0]
    existing = await db.execute(
        select(User).where(or_(User.email == email, User.username == username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    password_to_hash = password[:72]
    user = User(
        email=email,
        username=username,
        hashed_password=pwd_context.hash(password_to_hash),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.commit()

    return {"message": "Account created", "username": username, "email": email}


@router.post("/token")
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    username_or_email = form_data.username.strip()
    user = None

    try:
        user = await _get_user_by_username_or_email(db, username_or_email)
    except Exception:
        # Staging/demo fallback keeps the configured admin available if the DB
        # is temporarily unavailable.
        pass

    if user:
        password_to_check = (
            form_data.password[:72]
            if len(form_data.password) > 72
            else form_data.password
        )
        if not pwd_context.verify(password_to_check, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        subject = user.username
    else:
        admin_user = getattr(settings, "ADMIN_USER", "admin")
        admin_pass = settings.ADMIN_PASSWORD
        local_username = username_or_email.split("@", 1)[0]

        if not (
            admin_pass
            and local_username.casefold() == admin_user.casefold()
            and form_data.password == admin_pass
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Bootstrap the configured admin into the canonical users table on
        # first successful login. The password is never stored in plaintext.
        admin_result = await db.execute(
            select(User).where(User.username == admin_user)
        )
        admin = admin_result.scalar_one_or_none()
        if admin is None:
            admin_email = f"{admin_user}@pharmaviyum.local"
            admin = User(
                email=admin_email,
                username=admin_user,
                hashed_password=pwd_context.hash(admin_pass[:72]),
                is_active=True,
                is_superuser=True,
            )
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
        elif not admin.is_superuser:
            admin.is_superuser = True
            await db.commit()

        subject = admin.username

    access_token = create_access_token(subject=subject)
    return {"access_token": access_token, "token_type": "bearer"}
