"""Team management service — business logic for teams and membership."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.modules.auth.repository import UserRepository
from app.modules.teams.models import Team, TeamMember, TeamMemberRole
from app.modules.teams.repository import TeamMemberRepository, TeamRepository
from app.modules.teams.schemas import (
    CreateTeamRequest,
    TeamDetailResponse,
    TeamMemberResponse,
    TeamResponse,
    UpdateTeamRequest,
)

_logger = get_logger(__name__)

# Roles allowed for invitation (not owner — owner is set at creation)
_INVITABLE_ROLES = {TeamMemberRole.ADMIN, TeamMemberRole.MEMBER, TeamMemberRole.VIEWER}


class TeamService:
    """Encapsulates team management logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._team_repo = TeamRepository(session)
        self._member_repo = TeamMemberRepository(session)
        self._user_repo = UserRepository(session)

    # ── Team CRUD ────────────────────────────────────────────────

    async def create_team(
        self, data: CreateTeamRequest, creator_id: uuid.UUID
    ) -> TeamResponse:
        """Create a new team and add the creator as owner."""
        if await self._team_repo.name_exists(data.name):
            raise ValueError(f"Team name '{data.name}' is already taken")

        team = Team(
            name=data.name,
            description=data.description,
            created_by=creator_id,
        )
        team = await self._team_repo.create(team)

        # Add creator as owner
        member = TeamMember(
            team_id=team.id,
            user_id=creator_id,
            role=TeamMemberRole.OWNER,
        )
        await self._member_repo.create(member)

        _logger.info(
            "Team created",
            team_id=str(team.id),
            name=team.name,
            creator_id=str(creator_id),
        )

        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            created_by=team.created_by,
            member_count=1,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

    async def get_team(self, team_id: uuid.UUID) -> Team | None:
        """Retrieve a team by ID."""
        return await self._team_repo.get(team_id)

    async def update_team(
        self, team_id: uuid.UUID, data: UpdateTeamRequest
    ) -> Team | None:
        """Update team name/description."""
        update_fields: dict = {}
        if data.name is not None:
            # Check uniqueness if changing name
            existing = await self._team_repo.get_by_name(data.name)
            if existing and existing.id != team_id:
                raise ValueError(f"Team name '{data.name}' is already taken")
            update_fields["name"] = data.name
        if data.description is not None:
            update_fields["description"] = data.description

        if not update_fields:
            return await self._team_repo.get(team_id)

        return await self._team_repo.update(team_id, update_fields)

    async def delete_team(self, team_id: uuid.UUID) -> bool:
        """Delete a team and all its memberships."""
        return await self._team_repo.delete(team_id)

    # ── Membership ───────────────────────────────────────────────

    async def invite_member(
        self,
        team_id: uuid.UUID,
        username: str,
        role: str,
        inviter_id: uuid.UUID,
    ) -> TeamMemberResponse:
        """Invite (or add) a user to the team with the given role."""
        # Validate role
        try:
            member_role = TeamMemberRole(role)
        except ValueError:
            raise ValueError(
                f"Invalid role '{role}'. Must be one of: admin, member, viewer"
            ) from None
        if member_role == TeamMemberRole.OWNER:
            raise ValueError("Cannot invite a user as owner")

        # Check inviter has permission (must be owner or admin)
        inviter_membership = await self._member_repo.get_membership(
            team_id, inviter_id
        )
        if inviter_membership is None or inviter_membership.role not in {
            TeamMemberRole.OWNER,
            TeamMemberRole.ADMIN,
        }:
            raise PermissionError(
                "Only team owners and admins can invite members"
            )

        # Find user to invite
        user = await self._user_repo.get_by_username(username)
        if user is None:
            raise ValueError(f"User '{username}' not found")

        # Check if already a member
        existing = await self._member_repo.get_membership(team_id, user.id)
        if existing is not None:
            # Update role if different
            if existing.role != member_role:
                await self._member_repo.update(
                    existing.id, {"role": member_role}
                )
                _logger.info(
                    "Team member role updated",
                    team_id=str(team_id),
                    user_id=str(user.id),
                    new_role=role,
                )
            return TeamMemberResponse(
                user_id=user.id,
                username=user.username,
                display_name=user.display_name,
                role=member_role.value,
                joined_at=existing.created_at,
            )

        # Add new member
        member = TeamMember(
            team_id=team_id,
            user_id=user.id,
            role=member_role,
        )
        member = await self._member_repo.create(member)

        _logger.info(
            "Team member added",
            team_id=str(team_id),
            user_id=str(user.id),
            role=role,
        )

        return TeamMemberResponse(
            user_id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=member_role.value,
            joined_at=member.created_at,
        )

    async def remove_member(
        self, team_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Remove a user from the team."""
        return await self._member_repo.remove_member(team_id, user_id)

    async def update_member_role(
        self,
        team_id: uuid.UUID,
        user_id: uuid.UUID,
        new_role: str,
        requester_id: uuid.UUID,
    ) -> TeamMemberResponse | None:
        """Update a member's role within the team."""
        try:
            role = TeamMemberRole(new_role)
        except ValueError:
            raise ValueError(f"Invalid role '{new_role}'") from None

        if role == TeamMemberRole.OWNER:
            raise ValueError("Cannot assign owner role via this endpoint")

        # Check requester is owner or admin
        requester_membership = await self._member_repo.get_membership(
            team_id, requester_id
        )
        if requester_membership is None or requester_membership.role not in {
            TeamMemberRole.OWNER,
            TeamMemberRole.ADMIN,
        }:
            raise PermissionError("Only team owners and admins can change roles")

        membership = await self._member_repo.get_membership(team_id, user_id)
        if membership is None:
            return None

        await self._member_repo.update(membership.id, {"role": role})

        user = await self._user_repo.get(user_id)
        return TeamMemberResponse(
            user_id=user_id,
            username=user.username if user else "unknown",
            display_name=user.display_name if user else None,
            role=role.value,
            joined_at=membership.created_at,
        )

    async def get_team_detail(
        self, team_id: uuid.UUID
    ) -> TeamDetailResponse | None:
        """Get team info with member list."""
        team = await self._team_repo.get(team_id)
        if team is None:
            return None

        memberships = await self._member_repo.get_team_members(team_id)
        members: list[TeamMemberResponse] = []
        for m in memberships:
            user = await self._user_repo.get(m.user_id)
            members.append(
                TeamMemberResponse(
                    user_id=m.user_id,
                    username=user.username if user else "unknown",
                    display_name=user.display_name if user else None,
                    role=m.role.value,
                    joined_at=m.created_at,
                )
            )

        return TeamDetailResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            created_by=team.created_by,
            member_count=len(members),
            created_at=team.created_at,
            updated_at=team.updated_at,
            members=members,
        )

    async def list_user_teams(
        self, user_id: uuid.UUID
    ) -> list[TeamResponse]:
        """List all teams a user belongs to."""
        memberships = await self._member_repo.get_user_teams(user_id)
        teams: list[TeamResponse] = []
        for m in memberships:
            team = await self._team_repo.get(m.team_id)
            if team:
                count = await self._member_repo.count_team_members(team.id)
                teams.append(
                    TeamResponse(
                        id=team.id,
                        name=team.name,
                        description=team.description,
                        created_by=team.created_by,
                        member_count=count,
                        created_at=team.created_at,
                        updated_at=team.updated_at,
                    )
                )
        return teams

    async def is_member(
        self, team_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Check if a user is a member of the team."""
        return await self._member_repo.is_member(team_id, user_id)

    async def get_team_ids_for_user(
        self, user_id: uuid.UUID
    ) -> list[uuid.UUID]:
        """Get all team IDs the user belongs to."""
        return await self._member_repo.get_team_ids_for_user(user_id)
