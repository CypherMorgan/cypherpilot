"""add teams and team_members tables

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-07-21
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create team_member_role_enum (idempotent)
    op.execute(
        """\
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'team_member_role_enum') THEN
                CREATE TYPE team_member_role_enum AS ENUM ('owner', 'admin', 'member', 'viewer');
            END IF;
        END
        $$;
        """
    )

    # ── teams table ─────────────────────────────────────────────
    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column(
            "created_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
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
    op.create_index("ix_teams_name", "teams", ["name"])
    op.create_index("ix_teams_created_by", "teams", ["created_by"])

    # ── team_members table ──────────────────────────────────────
    op.create_table(
        "team_members",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "team_id",
            sa.Uuid(),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Text(),
            nullable=False,
            server_default="member",
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
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_user"),
    )
    op.create_index("ix_team_members_team_id", "team_members", ["team_id"])
    op.create_index("ix_team_members_user_id", "team_members", ["user_id"])

    # ── Add team_id to analysis_sessions ────────────────────────
    op.add_column(
        "analysis_sessions",
        sa.Column(
            "team_id",
            sa.Uuid(),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_analysis_sessions_team_id", "analysis_sessions", ["team_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_analysis_sessions_team_id", table_name="analysis_sessions")
    op.drop_column("analysis_sessions", "team_id")

    op.drop_index("ix_team_members_user_id", table_name="team_members")
    op.drop_index("ix_team_members_team_id", table_name="team_members")
    op.drop_table("team_members")

    op.drop_index("ix_teams_created_by", table_name="teams")
    op.drop_index("ix_teams_name", table_name="teams")
    op.drop_table("teams")

    sa.Enum(name="team_member_role_enum").drop(op.get_bind(), checkfirst=True)
