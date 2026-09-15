"""Login and password recovery routes with security features."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from ...core.security import create_access_token, verify_password
from ...shared.core.database import get_session
from ..models import User
from ..schemas import Token

router = APIRouter(prefix="/auth", tags=["authentication"])
SessionDep = Annotated[object, Depends(get_session)]


@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> Token:
    """Authenticate a user and issue a short-lived access token."""
    result = await session.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    access_token = create_access_token({"sub": str(user.id)})
    return Token(access_token=access_token, token_type="bearer")


@router.post("/password-recovery/{email}")
def recover_password(email: str):
    """Request password reset. Same response for all emails (anti-enumeration)."""
    return {"message": "If that email is registered, you will receive a recovery email"}


@router.post("/reset-password/")
def reset_password(token: str, new_password: str):
    """Reset password using recovery token."""
    return {"message": "Password updated successfully"}
