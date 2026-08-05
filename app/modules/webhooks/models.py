"""Webhook ORM models.

Stores user-owned outgoing webhook endpoints and their delivery history.

Schema::

    webhooks
    ─────────
    id              UUID PRIMARY KEY
    user_id         UUID FK → users.id NOT NULL (CASCADE)
    name            VARCHAR(100) NOT NULL
    url             VARCHAR(500) NOT NULL      — target endpoint
    events          JSON NOT NULL              — subscribed event names
    secret          VARCHAR(255) NOT NULL      — HMAC signing secret
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()

    webhook_deliveries
    ───────────────────
    id              UUID PRIMARY KEY
    webhook_id      UUID FK → webhooks.id NOT NULL (CASCADE)
    event           VARCHAR(100) NOT NULL
    session_id      UUID                       — related analysis session
    payload         JSON                       — exact body that was sent
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    — pending | delivered | failed
    attempts        INTEGER NOT NULL DEFAULT 0
    max_attempts    INTEGER NOT NULL DEFAULT 3
    last_status_code INTEGER
    last_error      VARCHAR(500)
    next_retry_at   TIMESTAMPTZ
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models.base import TimestampMixin, UUIDMixin


class Webhook(Base, UUIDMixin, TimestampMixin):
    """An outgoing webhook endpoint owned by a user."""

    __tablename__ = "webhooks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    events: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )

    secret: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


class WebhookDelivery(Base, UUIDMixin, TimestampMixin):
    """A single delivery attempt history record for a webhook event."""

    __tablename__ = "webhook_deliveries"

    webhook_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(),
        nullable=True,
        default=None,
    )

    payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )

    last_status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )

    last_error: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )

    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
