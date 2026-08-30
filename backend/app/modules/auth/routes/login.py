"""
Login and password recovery routes.

Matches ibrahimengpy/full-stack-fastapi-template structure exactly:
- POST /login/access-token: OAuth2 login
- POST /login/test-token: Test current token
- POST /password-recovery/{email}: Request password reset
- POST /reset-password/: Reset password with token
- POST /password-recovery-html-content/{email}: Preview reset email (admin)

Security features:
- Email enumeration protection (same message for existing/non-existing)
- Constant-time authentication (via crud.authenticate)
"""
from datetime import timedelta
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from .. import crud
from ..deps import CurrentUser, SessionDep, get_current_active_superuser
from ..security import create_access_token
from ..schemas import Message, NewPassword, Token, UserPublic
from ..utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)
from ....shared.core.config import settings


router = APIRouter(tags=["login"])


@router.post("/login/access-token", response_model=Token)
def login_access_token(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    OAuth2 compatible token login.
    
    Accepts form data:
    - username (email)
    - password
    
    Returns JWT access token.
    """
    # Authenticate (constant-time internally)
    user = crud.authenticate(
        session=session,
        email=form_data.username,
        password=form_data.password,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires,
    )
    
    return Token(access_token=access_token)


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> UserPublic:
    """
    Test if current access token is valid.
    
    Returns current user info if token is valid.
    """
    return UserPublic.model_validate(current_user)


@router.post("/password-recovery/{email}", response_model=Message)
def recover_password(email: str, session: SessionDep) -> Message:
    """
    Request password recovery email.
    
    SECURITY: Always returns the same message to prevent email enumeration.
    Attacker cannot determine if email exists in the system.
    """
    user = crud.get_user_by_email(session=session, email=email)
    
    # Only send email if user actually exists
    # But ALWAYS return the same message (enumeration protection)
    if user:
        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email,
            email=email,
            token=password_reset_token,
        )
        send_email(
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    
    # Same message for both cases - prevents enumeration
    return Message(
        message="If that email is registered, you will receive a password recovery email"
    )


@router.post("/reset-password/", response_model=Message)
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password using token from recovery email.
    
    SECURITY: Returns same error for invalid token AND non-existing user
    to prevent enumeration.
    """
    # Verify token
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )
    
    # Find user
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        # Don't reveal that user doesn't exist
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",  # Same error as invalid token
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    # Update password
    from ..schemas import UserUpdate
    user_update = UserUpdate(password=body.new_password)
    crud.update_user(session=session, db_user=user, user_in=user_update)
    
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> HTMLResponse:
    """
    Generate HTML content for password recovery email (preview).
    
    Only accessible by superusers for testing email templates.
    """
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this email does not exist",
        )
    
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email,
        email=email,
        token=password_reset_token,
    )
    
    return HTMLResponse(
        content=email_data.html_content,
        headers={"subject": email_data.subject},
    )
