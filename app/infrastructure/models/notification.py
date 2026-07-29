"""Notification ORM model.

Stores per-user notifications for analysis completion, team activity,
and other platform events.

Schema::

    notifications
    ─────────────
    id              UUID PRIMARY KEY
    user_id         UUID FK → users.id NOT NULL (always target a user)
    type            VARCHAR(50) NOT NULL  — e.g. 'analysis.completed', 'team.invite'
    title           VARCHAR(255) NOT NULL
    message         TEXT NOT NULL
    resource_type   VARCHAR(50)   — e.g. 'session', 'team'
    resource_id     VARCHAR(100)  — UUID of the related resource
    read            BOOLEAN NOT NULL DEFAULT FALSE
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models.base import TimestampMixin, UUIDMixin


class Notification(Base, UUIDMixin, TimestampMixin):
    """A per-user notification for a platform event."""

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    resource_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    resource_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )

    read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )
