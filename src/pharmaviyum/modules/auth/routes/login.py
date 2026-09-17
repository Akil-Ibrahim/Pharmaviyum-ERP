"""Authentication, token rotation, logout, and password recovery routes."""

import hashlib
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.core.config import settings
from src.pharmaviyum.core.security import (
    create_access_token,
    create_refresh_token,
    decode_password_reset_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from src.pharmaviyum.redis_client import get_redis
from src.pharmaviyum.shared.core.database import get_session

from ..models import User
from ..schemas import Message, NewPassword, RefreshTokenRequest, Token
from ..utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _token_key(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"auth:{prefix}:{digest}"


def _ttl(exp: int) -> int:
    return max(exp - int(time.time()), 1)


async def _issue_token_pair(user_id: str) -> Token:
    return Token(
        access_token=create_access_token({"sub": user_id}),
        refresh_token=create_refresh_token(user_id),
        token_type="bearer",
    )


@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> Token:
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
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return await _issue_token_pair(str(user.id))


@router.post("/refresh", response_model=Token)
async def refresh_access_token(body: RefreshTokenRequest, session: SessionDep) -> Token:
    payload = decode_refresh_token(body.refresh_token)
    if not payload or not payload.get("sub") or not payload.get("jti"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    redis = await get_redis()
    claimed = await redis.set(
        _token_key("refresh-used", payload["jti"]),
        "1",
        ex=_ttl(int(payload["exp"])),
        nx=True,
    )
    if not claimed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )
    user = await session.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    return await _issue_token_pair(str(user.id))


@router.post("/logout", response_model=Message)
async def logout(body: RefreshTokenRequest) -> Message:
    payload = decode_refresh_token(body.refresh_token)
    if payload and payload.get("jti"):
        redis = await get_redis()
        await redis.set(
            _token_key("refresh-used", payload["jti"]),
            "1",
            ex=_ttl(int(payload["exp"])),
            nx=True,
        )
    return Message(message="Logged out")


@router.post("/password-recovery/{email}", response_model=Message)
async def recover_password(email: str, session: SessionDep) -> Message:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user and user.is_active:
        token = generate_password_reset_token(user.email)
        email_data = generate_reset_password_email(email, user.email, token)
        if getattr(settings, "EMAILS_ENABLED", False):
            send_email(email, email_data.subject, email_data.html_content)
    return Message(
        message="If that email is registered, you will receive a recovery email"
    )


@router.post("/reset-password/", response_model=Message)
async def reset_password(body: NewPassword, session: SessionDep) -> Message:
    payload = decode_password_reset_token(body.token)
    if not payload or not payload.get("sub") or not payload.get("jti"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    redis = await get_redis()
    used_key = _token_key("password-reset-used", payload["jti"])
    claimed = await redis.set(used_key, "1", ex=_ttl(int(payload["exp"])), nx=True)
    if not claimed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used",
        )
    result = await session.execute(select(User).where(User.email == payload["sub"]))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        await redis.delete(used_key)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
        )
    try:
        user.hashed_password = get_password_hash(body.new_password)
        session.add(user)
        await session.flush()
    except Exception:
        await redis.delete(used_key)
        raise
    return Message(message="Password updated successfully")
