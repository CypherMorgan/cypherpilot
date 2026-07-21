"""Auth middleware — FastAPI dependencies for JWT-based authentication.

Provides:
  ``get_current_user`` — required authentication (raises 401 if missing).
  ``get_optional_current_user`` — optional authentication (returns None
    if no token is present, raises 401 if token is invalid).

Usage in route handlers::

    from app.modules.auth.middleware import get_current_user, get_optional_current_user
    from app.modules.auth.models import User

    @router.get("/protected")
    async def protected_route(user: User = Depends(get_current_user)):
        return {"user_id": user.id}

    @router.get("/maybe-protected")
    async def maybe_route(user: User | None = Depends(get_optional_current_user)):
        if user:
            return {"hello": user.username}
        return {"hello": "anonymous"}
"""

from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.modules.auth.config import AuthConfig
from app.modules.auth.models import User
from app.modules.auth.service import AuthService


async def _get_auth_config(request: Request) -> AuthConfig:
    """Extract AuthConfig from app state (populated during lifespan)."""
    return request.app.state.auth_config


async def _get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_config: Annotated[AuthConfig, Depends(_get_auth_config)],
) -> AuthService:
    """Create an AuthService instance for the current request."""
    return AuthService(session=db, config=auth_config)


# ── Required authentication ─────────────────────────────────────


async def get_current_user(
    auth_service: Annotated[AuthService, Depends(_get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """FastAPI dependency: extract and validate JWT, return the User.

    Use this as a dependency on any route that requires authentication::

        @router.get("/me")
        async def me(user: User = Depends(get_current_user)):
            return user

    Raises:
        401 Unauthorized — missing, expired, or invalid token.
        401 Unauthorized — user not found or deactivated.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format (expected 'Bearer <token>')",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    try:
        payload = auth_service.decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = await auth_service.get_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# ── Optional authentication ──────────────────────────────────────


async def get_optional_current_user(
    auth_service: Annotated[AuthService, Depends(_get_auth_service)],
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    """FastAPI dependency: optionally extract and validate JWT.

    Returns the authenticated ``User`` if a valid token is present,
    or ``None`` if no Authorization header is provided.

    Raises 401 if a token IS present but is invalid/expired.
    Use this for endpoints that behave differently for authenticated
    vs. anonymous users (e.g. session scoping).
    """
    if not authorization:
        return None

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]

    try:
        payload = auth_service.decode_access_token(token)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        return None

    user = await auth_service.get_user(user_id)
    if user is None or not user.is_active:
        return None

    return user
