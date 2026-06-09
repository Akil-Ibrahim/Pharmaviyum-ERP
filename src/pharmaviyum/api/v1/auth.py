from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from passlib.context import CryptContext
from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.core.oauth2 import create_access_token
from src.pharmaviyum.models.user import User
from src.pharmaviyum.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
        return result.scalar_one_or_none()

    result = await db.execute(select(User).where(User.username == username_or_email))
    return result.scalar_one_or_none()


@router.post('/token')
async def token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Issue a JWT access token for valid credentials.

    The endpoint supports login by username, email, or fallback admin credentials.
    """
    username_or_email = form_data.username.strip()
    user = None
    
    # Try to get user from database, but don't fail if DB is unavailable
    try:
        user = await _get_user_by_username_or_email(db, username_or_email)
    except Exception:
        # If DB is unavailable, proceed to fallback admin check
        pass

    # Verify password against DB user if present
    if user:
        verified = pwd_context.verify(form_data.password, user.hashed_password)
        if not verified:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        subject = user.username
    else:
        # Fallback to environment admin credentials
        admin_user = settings.ADMIN_USER
        admin_pass = settings.ADMIN_PASSWORD
        local_username = username_or_email.split("@", 1)[0]
        if not (admin_pass and local_username == admin_user and form_data.password == admin_pass):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        subject = admin_user

    access_token = create_access_token(subject=subject)
    return {"access_token": access_token, "token_type": "bearer"}
