"""Notification preference ORM model.

Stores per-user email notification preferences for each event type.
When a notification is created, the system checks this table to decide
whether to also send an email.

Schema::

    notification_preferences
    ────────────────────────
    id              UUID PRIMARY KEY
    user_id         UUID FK → users.id NOT NULL (unique constraint)
    email_analysis_completed BOOLEAN NOT NULL DEFAULT TRUE
    email_analysis_failed    BOOLEAN NOT NULL DEFAULT TRUE
    email_team_invite        BOOLEAN NOT NULL DEFAULT TRUE
    email_team_removed       BOOLEAN NOT NULL DEFAULT TRUE
    email_team_role_changed  BOOLEAN NOT NULL DEFAULT TRUE
    email_enabled            BOOLEAN NOT NULL DEFAULT TRUE
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models.base import TimestampMixin, UUIDMixin


class NotificationPreference(Base, UUIDMixin, TimestampMixin):
    """Per-user notification preferences — controls email delivery."""

    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_notification_preferences_user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Master switch — when False, no emails are sent regardless of per-type settings
    email_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Per-event-type email toggles
    email_analysis_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    email_analysis_failed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    email_team_invite: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    email_team_removed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    email_team_role_changed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
