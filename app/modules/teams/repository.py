"""Team and TeamMember repository — data access layer."""

from __future__ import annotations

import uuid

from sqlalchemy import and_, func, select

from app.infrastructure.repository import BaseRepository
from app.modules.teams.models import Team, TeamMember


class TeamRepository(BaseRepository[Team]):
    """Repository for Team CRUD operations."""

    model_class = Team

    async def get_by_name(self, name: str) -> Team | None:
        """Find a team by name."""
        stmt = select(Team).where(Team.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def name_exists(self, name: str) -> bool:
        """Check if a team name is already taken."""
        stmt = select(func.count()).where(Team.name == name)
        count = await self._session.scalar(stmt)
        return (count or 0) > 0


class TeamMemberRepository(BaseRepository[TeamMember]):
    """Repository for TeamMember operations."""

    model_class = TeamMember

    async def get_membership(
        self, team_id: uuid.UUID, user_id: uuid.UUID
    ) -> TeamMember | None:
        """Get a specific membership record."""
        stmt = select(TeamMember).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_team_members(
        self, team_id: uuid.UUID
    ) -> list[TeamMember]:
        """Get all members of a team."""
        stmt = (
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .order_by(TeamMember.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_teams(
        self, user_id: uuid.UUID
    ) -> list[TeamMember]:
        """Get all teams a user belongs to."""
        stmt = (
            select(TeamMember)
            .where(TeamMember.user_id == user_id)
            .order_by(TeamMember.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_team_members(self, team_id: uuid.UUID) -> int:
        """Count members in a team."""
        stmt = select(func.count()).where(TeamMember.team_id == team_id)
        count = await self._session.scalar(stmt)
        return count or 0

    async def is_member(self, team_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check if a user is a member of the team."""
        stmt = select(func.count()).where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
        )
        count = await self._session.scalar(stmt)
        return (count or 0) > 0

    async def remove_member(
        self, team_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Remove a user from a team. Returns True if removed."""
        membership = await self.get_membership(team_id, user_id)
        if membership is None:
            return False
        await self._session.delete(membership)
        await self._session.commit()
        return True

    async def get_team_ids_for_user(
        self, user_id: uuid.UUID
    ) -> list[uuid.UUID]:
        """Return list of team IDs the user belongs to."""
        stmt = select(TeamMember.team_id).where(TeamMember.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
