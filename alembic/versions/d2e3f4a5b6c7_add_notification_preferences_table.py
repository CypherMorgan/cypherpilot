"""Add notification_preferences table.

Creates ``notification_preferences`` table for per-user email
notification preferences (v0.6.1 — Email Notifications).

New tables:
- ``notification_preferences`` — user-owned email notification toggles:
  master switch (email_enabled), per-event-type toggles for analysis
  completed/failed and team invite/removed/role_changed events.

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f40596
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d2e3f4a5b6c7"
down_revision: str | None = "c1d2e3f40596"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the notification_preferences table."""
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "email_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "email_analysis_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "email_analysis_failed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "email_team_invite",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "email_team_removed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "email_team_role_changed",
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

    # Unique constraint on user_id — one preference row per user
    op.create_unique_constraint(
        "uq_notification_preferences_user_id",
        "notification_preferences",
        ["user_id"],
    )


def downgrade() -> None:
    """Drop the notification_preferences table."""
    op.drop_constraint(
        "uq_notification_preferences_user_id",
        "notification_preferences",
        type_="unique",
    )
    op.drop_table("notification_preferences")
