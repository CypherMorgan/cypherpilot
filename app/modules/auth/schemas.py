"""Pydantic schemas for auth request/response bodies."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ── Request schemas ─────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """POST /auth/register"""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username (alphanumeric, hyphens, underscores)",
    )
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 characters)",
    )
    display_name: str | None = Field(
        None,
        max_length=100,
        description="Optional display name",
    )


class LoginRequest(BaseModel):
    """POST /auth/login"""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class ChangePasswordRequest(BaseModel):
    """POST /auth/change-password"""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (min 8 characters)",
    )


# ── Response schemas ────────────────────────────────────────────


class UserResponse(BaseModel):
    """Public user representation (never includes password hash)."""

    id: uuid.UUID
    username: str
    email: str
    display_name: str | None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """POST /auth/login or POST /auth/register response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
