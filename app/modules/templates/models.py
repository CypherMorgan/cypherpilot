"""Template ORM model.

Stores reusable analysis templates owned by individual users. A template
captures a common failure pattern (CI log, stack trace, plain text)
that can be loaded into the Failure Analysis page for quick analysis.

Schema::

    templates
    ─────────
    id              UUID PRIMARY KEY
    user_id         UUID FK → users.id NOT NULL (CASCADE) — owner
    name            VARCHAR(100) NOT NULL
    description     VARCHAR(500)          — optional note
    content         TEXT NOT NULL         — the failure output text
    source_type     VARCHAR(20) NOT NULL DEFAULT 'plain_text'
                    — plain_text | markdown | ci_log | stack_trace
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models.base import TimestampMixin, UUIDMixin


class Template(Base, UUIDMixin, TimestampMixin):
    """A reusable analysis template owned by a user."""

    __tablename__ = "templates"

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

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="plain_text",
    )
