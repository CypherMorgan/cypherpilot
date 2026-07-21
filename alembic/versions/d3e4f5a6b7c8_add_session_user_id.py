"""add_session_user_id

Adds a nullable ``user_id`` foreign key to ``analysis_sessions`` to
link sessions to their owning user.  Existing sessions get
``user_id = NULL`` (visible to all users for backward compatibility).

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d3e4f5a6b7c8"
down_revision: str | None = "c2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add nullable user_id FK to analysis_sessions."""
    op.add_column(
        "analysis_sessions",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_analysis_sessions_user_id",
        "analysis_sessions",
        ["user_id"],
    )


def downgrade() -> None:
    """Remove user_id FK and index from analysis_sessions."""
    op.drop_index("ix_analysis_sessions_user_id", table_name="analysis_sessions")
    op.drop_column("analysis_sessions", "user_id")
