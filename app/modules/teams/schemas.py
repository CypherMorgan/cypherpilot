"""Pydantic schemas for team request/response bodies."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ── Request schemas ─────────────────────────────────────────────


class CreateTeamRequest(BaseModel):
    """POST /teams"""

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Team name",
    )
    description: str | None = Field(
        None,
        max_length=500,
        description="Optional team description",
    )


class UpdateTeamRequest(BaseModel):
    """PATCH /teams/{team_id}"""

    name: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        description="New team name",
    )
    description: str | None = Field(
        None,
        max_length=500,
        description="New team description",
    )


class InviteMemberRequest(BaseModel):
    """POST /teams/{team_id}/members"""

    username: str = Field(..., description="Username of the user to invite")
    role: str = Field(
        "member",
        description="Role to assign: admin, member, viewer",
    )


class UpdateMemberRoleRequest(BaseModel):
    """PATCH /teams/{team_id}/members/{user_id}"""

    role: str = Field(..., description="New role: admin, member, viewer")


# ── Response schemas ────────────────────────────────────────────


class TeamMemberResponse(BaseModel):
    """A team member with user info."""

    user_id: uuid.UUID
    username: str
    display_name: str | None
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class TeamResponse(BaseModel):
    """Public team representation."""

    id: uuid.UUID
    name: str
    description: str | None
    created_by: uuid.UUID | None
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeamDetailResponse(TeamResponse):
    """Team with member list."""

    members: list[TeamMemberResponse] = []
