"""Add webhooks tables.

Creates ``webhooks`` and ``webhook_deliveries`` tables for outbound
event delivery (v0.6.0 — Webhooks & Callbacks).

New tables:
- ``webhooks`` — user-owned outgoing webhook endpoints: name, target
  URL, subscribed events (JSON array), HMAC signing secret, active flag.
- ``webhook_deliveries`` — delivery history per event: status, attempt
  count, last HTTP status/error, next retry time.

Revision ID: c1d2e3f40596
Revises: b8c9d0e1f203
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f40596"
down_revision: str | None = "b8c9d0e1f203"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the webhooks tables."""
    op.create_table(
        "webhooks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "url",
            sa.String(500),
            nullable=False,
        ),
        sa.Column(
            "events",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "secret",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "webhook_id",
            sa.Uuid(),
            sa.ForeignKey("webhooks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "event",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column(
            "payload",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "max_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("3"),
        ),
        sa.Column(
            "last_status_code",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "last_error",
            sa.String(500),
            nullable=True,
        ),
        sa.Column(
            "next_retry_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Drop the webhooks tables."""
    op.drop_table("webhook_deliveries")
    op.drop_table("webhooks")
