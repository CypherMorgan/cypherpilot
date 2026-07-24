"""Auth API routes — register, login, profile.

Endpoints:
  POST /auth/register  — Create a new account
  POST /auth/login     — Authenticate and receive JWT
  GET  /auth/me        — Get current user profile (authenticated)
  POST /auth/change-password — Change password (authenticated)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.modules.audit.helpers import log_audit
from app.modules.auth.config import AuthConfig
from app.modules.auth.middleware import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


async def _get_auth_config(request: Request) -> AuthConfig:
    return request.app.state.auth_config  # type: ignore[no-any-return]


async def _get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_config: Annotated[AuthConfig, Depends(_get_auth_config)],
) -> AuthService:
    return AuthService(session=db, config=auth_config)


# ── Public endpoints ────────────────────────────────────────────


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
async def register(
    body: RegisterRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(_get_auth_service)],
) -> TokenResponse:
    """Create a new user account and return a JWT access token."""
    try:
        result = await auth_service.register(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    await log_audit(
        db,
        action="auth.register",
        user_id=result.user.id,
        resource_type="user",
        resource_id=result.user.id,
        metadata={"username": result.user.username},
        request=request,
    )
    return result


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
)
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(_get_auth_service)],
) -> TokenResponse:
    """Authenticate with username/email and password, receive a JWT."""
    try:
        result = await auth_service.login(body.username, body.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    await log_audit(
        db,
        action="auth.login",
        user_id=result.user.id,
        resource_type="user",
        resource_id=result.user.id,
        metadata={"username": result.user.username},
        request=request,
    )
    return result


# ── Authenticated endpoints ─────────────────────────────────────


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def me(
    user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(user)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
)
async def change_password(
    body: ChangePasswordRequest,
    user: Annotated[User, Depends(get_current_user)],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(_get_auth_service)],
) -> None:
    """Change the authenticated user's password."""
    if not AuthService.verify_password(
        body.current_password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    user.hashed_password = AuthService.hash_password(body.new_password)
    await auth_service._session.commit()

    await log_audit(
        db,
        action="auth.change_password",
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        request=request,
    )
