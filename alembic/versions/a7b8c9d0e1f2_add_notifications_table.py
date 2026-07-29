"""add_notifications_table

Creates the ``notifications`` table for per-user platform
notifications (analysis completion, team activity, etc.).

New table:
- ``notifications`` — UUID primary key, required user_id FK, type,
  title, message, optional resource_type/resource_id, read flag,
  timestamps.

Revision ID: a7b8c9d0e1f2
Revises: f5a6b7c8d9e0
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: str | None = "f5a6b7c8d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the notifications table."""
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "type",
            sa.String(50),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "title",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "resource_type",
            sa.String(50),
            nullable=True,
        ),
        sa.Column(
            "resource_id",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "read",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
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
    """Drop the notifications table."""
    op.drop_table("notifications")
