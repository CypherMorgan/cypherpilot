"""Team and TeamMember ORM models.

Schema::

    teams
    ─────
    id              UUID PRIMARY KEY
    name            VARCHAR(100) UNIQUE NOT NULL
    description     VARCHAR(500)
    created_by      UUID FK -> users.id
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()

    team_members
    ────────────
    id              UUID PRIMARY KEY
    team_id         UUID FK -> teams.id ON DELETE CASCADE
    user_id         UUID FK -> users.id ON DELETE CASCADE
    role            VARCHAR(20) NOT NULL DEFAULT 'member'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    UNIQUE(team_id, user_id)
"""

from __future__ import annotations

import uuid as _uuid
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.infrastructure.models.base import TimestampMixin, UUIDMixin


class TeamMemberRole(StrEnum):
    """Role of a user within a team."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Team(Base, UUIDMixin, TimestampMixin):
    """A team of users who can share analysis sessions."""

    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        default=None,
    )

    created_by: Mapped[_uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )


class TeamMember(Base, UUIDMixin, TimestampMixin):
    """Membership record linking a user to a team."""

    __tablename__ = "team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_user"),
    )

    team_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[TeamMemberRole] = mapped_column(
        Enum(
            TeamMemberRole,
            name="team_member_role_enum",
            create_constraint=True,
            values_callable=lambda cls: [m.value for m in cls],
        ),
        nullable=False,
        default=TeamMemberRole.MEMBER,
    )
