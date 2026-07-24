"""add_audit_logs_table

Creates the ``audit_logs`` table for tracking user actions across
the platform.

New table:

- ``audit_logs`` — UUID primary key, optional user_id/team_id FKs,
  action string, resource_type, resource_id, JSONB metadata, IP address,
  timestamps.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5a6b7c8d9e0"
down_revision: str | None = "e4f5a6b7c8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the audit_logs table."""
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "team_id",
            sa.Uuid(),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "action",
            sa.String(100),
            nullable=False,
            index=True,
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
            "metadata",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "ip_address",
            sa.String(45),
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
    """Drop the audit_logs table."""
    op.drop_table("audit_logs")
