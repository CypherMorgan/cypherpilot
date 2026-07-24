"""AuditLog ORM model.

Tracks user actions across the platform for accountability and
team visibility.  Every significant event (login, session create,
team invite, etc.) is recorded as an audit log entry.

Schema::

    audit_logs
    ──────────
    id              UUID PRIMARY KEY
    user_id         UUID FK → users.id (nullable for anonymous actions)
    team_id         UUID FK → teams.id (nullable for non-team actions)
    action          VARCHAR(100) NOT NULL  — e.g. 'session.create', 'team.invite'
    resource_type   VARCHAR(50)   — e.g. 'session', 'team', 'user'
    resource_id     VARCHAR(100)  — UUID of the affected resource
    metadata        JSONB         — additional context (title, provider, etc.)
    ip_address      VARCHAR(45)   — client IP (supports IPv6)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models.base import TimestampMixin, UUIDMixin


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """An audit log entry recording a user action."""

    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    team_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
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

    extra_data: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSON(),
        nullable=True,
        default=None,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        default=None,
    )
