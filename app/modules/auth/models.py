"""User ORM model.

Stores user credentials, role, and profile information.

Schema::

    users
    ─────
    id              UUID PRIMARY KEY
    username        VARCHAR(50) UNIQUE NOT NULL
    email           VARCHAR(255) UNIQUE NOT NULL
    display_name    VARCHAR(100)
    hashed_password VARCHAR(255) NOT NULL
    role            VARCHAR(20) NOT NULL DEFAULT 'user'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
"""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models.base import TimestampMixin, UUIDMixin


class UserRole(StrEnum):
    """User role for RBAC."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class User(Base, UUIDMixin, TimestampMixin):
    """A registered user of CypherPilot."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role_enum",
            create_constraint=True,
            values_callable=lambda cls: [m.value for m in cls],
        ),
        nullable=False,
        default=UserRole.USER,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean(),
        nullable=False,
        default=True,
    )
