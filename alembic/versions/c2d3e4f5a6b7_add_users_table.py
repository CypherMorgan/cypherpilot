"""add_users_table

Creates the ``users`` table for multi-user authentication and RBAC.

New table:

- ``users`` — UUID primary key, unique username/email, hashed password,
  role enum (admin/user/viewer), is_active flag, timestamps.

Revision ID: c2d3e4f5a6b7
Revises: a1b2c3d4e5f6
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the users table and user_role_enum type."""
    # Create the enum type first (idempotent)
    op.execute(
        """\
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role_enum') THEN
                CREATE TYPE user_role_enum AS ENUM ('admin', 'user', 'viewer');
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "username",
            sa.String(50),
            unique=True,
            nullable=False,
            index=True,
        ),
        sa.Column(
            "email",
            sa.String(255),
            unique=True,
            nullable=False,
            index=True,
        ),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Text(),
            nullable=False,
            server_default="user",
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


def downgrade() -> None:
    """Drop the users table and user_role_enum type."""
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS user_role_enum;")
