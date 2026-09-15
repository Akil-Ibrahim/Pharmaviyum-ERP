"""Authentication, token rotation, logout, and password recovery routes."""

import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from redis import asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)
from ...shared.core.database import get_session
from ..models import User
from ..schemas import Message, NewPassword, RefreshTokenRequest, Token
from ..utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _token_key(prefix: str, token: str) -> str:
    """Build a non-sensitive Redis key from a token digest."""
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"auth:{prefix}:{digest}"


def _redis():
    return aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)


async def _issue_token_pair(user_id: str) -> Token:
    """Issue an access token and a refresh token."""
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
    """Authenticate a user and issue an access/refresh token pair."""
    result = await session.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return await _issue_token_pair(str(user.id))


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    body: RefreshTokenRequest,
    session: SessionDep,
) -> Token:
    """Rotate a refresh token exactly once and revoke the consumed token."""
    payload = decode_refresh_token(body.refresh_token)
    if not payload or not payload.get("sub") or not payload.get("jti"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    redis = _redis()
    try:
        consumed_key = _token_key("refresh-used", payload["jti"])
        consumed = await redis.get(consumed_key)
        if consumed:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")

        user = await session.get(User, payload["sub"])
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        ttl = max(int(payload["exp"]) - int(__import__("time").time()), 1)
        await redis.set(consumed_key, "1", ex=ttl)
        return await _issue_token_pair(str(user.id))
    finally:
        await redis.aclose()


@router.post("/logout", response_model=Message)
async def logout(body: RefreshTokenRequest) -> Message:
    """Revoke a refresh token so it cannot be used again."""
    payload = decode_refresh_token(body.refresh_token)
    if payload and payload.get("jti"):
        redis = _redis()
        try:
            ttl = max(int(payload["exp"]) - int(__import__("time").time()), 1)
            await redis.set(_token_key("refresh-used", payload["jti"]), "1", ex=ttl)
        finally:
            await redis.aclose()
    return Message(message="Logged out")


@router.post("/password-recovery/{email}", response_model=Message)
async def recover_password(email: str, session: SessionDep) -> Message:
    """Issue a short-lived reset token and send it without revealing account existence."""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user and user.is_active:
        token = generate_password_reset_token(user.email)
        email_data = generate_reset_password_email(email, user.email, token)
        if getattr(settings, "EMAILS_ENABLED", False):
            send_email(email, email_data.subject, email_data.html_content)
    return Message(message="If that email is registered, you will receive a recovery email")


@router.post("/reset-password/", response_model=Message)
async def reset_password(body: NewPassword, session: SessionDep) -> Message:
    """Consume a password-reset token exactly once and update the password."""
    email = verify_password_reset_token(body.token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    redis = _redis()
    try:
        used_key = _token_key("password-reset-used", body.token)
        if await redis.get(used_key):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token has already been used")

        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")

        user.hashed_password = get_password_hash(body.new_password)
        session.add(user)
        await session.flush()

        payload = decode_access_token(body.token)
        ttl = 172800
        if payload and payload.get("exp"):
            ttl = max(int(payload["exp"]) - int(__import__("time").time()), 1)
        await redis.set(used_key, "1", ex=ttl)
        return Message(message="Password updated successfully")
    finally:
        await redis.aclose()
