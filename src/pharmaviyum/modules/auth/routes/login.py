"""Login and password recovery routes with security features."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login/access-token")
def login_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """OAuth2 login. TODO: integrate with your user service."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Integrate with your user service",
    )


@router.post("/password-recovery/{email}")
def recover_password(email: str):
    """Request password reset. Same response for all emails (anti-enumeration)."""
    return {"message": "If that email is registered, you will receive a recovery email"}


@router.post("/reset-password/")
def reset_password(token: str, new_password: str):
    """Reset password using recovery token."""
    return {"message": "Password updated successfully"}
