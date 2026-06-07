from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from src.pharmaviyum.db.session import get_db
from src.pharmaviyum.core.oauth2 import create_access_token
from src.pharmaviyum.models.user import User
from src.pharmaviyum.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def _get_user_by_username(db: AsyncSession, username: str):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


@router.post('/token')
async def token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Issue a JWT access token for valid credentials.

    The endpoint supports a fallback admin credential defined via environment
    variables when no user record exists in the database.
    """
    user = await _get_user_by_username(db, form_data.username)

    # Verify password against DB user if present
    if user:
        verified = pwd_context.verify(form_data.password, user.hashed_password)
        if not verified:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    else:
        # Fallback to environment admin credentials
        admin_user = settings.ADMIN_USER
        admin_pass = settings.ADMIN_PASSWORD
        if not (admin_pass and form_data.username == admin_user and form_data.password == admin_pass):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(subject=form_data.username)
    return {"access_token": access_token, "token_type": "bearer"}
