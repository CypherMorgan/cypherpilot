"""Tests for TeamService."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.teams.schemas import (
    CreateTeamRequest,
    UpdateTeamRequest,
)
from app.modules.teams.service import TeamService


class TestTeamCRUD:
    """Tests for team create/update/delete."""

    async def test_create_team(self, db_session: AsyncSession, test_user: User) -> None:
        svc = TeamService(db_session)
        data = CreateTeamRequest(name="My Team", description="A test team")
        team = await svc.create_team(data, creator_id=test_user.id)

        assert team.name == "My Team"
        assert team.description == "A test team"
        assert team.member_count == 1  # creator is owner
        assert team.created_by == test_user.id

    async def test_create_duplicate_name(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        svc = TeamService(db_session)
        data = CreateTeamRequest(name="Unique Team")
        await svc.create_team(data, creator_id=test_user.id)

        with pytest.raises(ValueError, match="already taken"):
            await svc.create_team(data, creator_id=test_user.id)

    async def test_update_team(self, db_session: AsyncSession, test_user: User) -> None:
        svc = TeamService(db_session)
        team = await svc.create_team(
            CreateTeamRequest(name="Old Name"), creator_id=test_user.id
        )

        updated = await svc.update_team(
            team.id, UpdateTeamRequest(name="New Name", description="Updated")
        )
        assert updated is not None
        assert updated.name == "New Name"
        assert updated.description == "Updated"

    async def test_delete_team(self, db_session: AsyncSession, test_user: User) -> None:
        svc = TeamService(db_session)
        team = await svc.create_team(
            CreateTeamRequest(name="Delete Me"), creator_id=test_user.id
        )
        deleted = await svc.delete_team(team.id)
        assert deleted is True

        detail = await svc.get_team_detail(team.id)
        assert detail is None


class TestMembership:
    """Tests for team membership operations."""

    async def test_invite_member(
        self, db_session: AsyncSession, test_user: User, test_user2: User
    ) -> None:
        svc = TeamService(db_session)
        team = await svc.create_team(
            CreateTeamRequest(name="Team A"), creator_id=test_user.id
        )

        member = await svc.invite_member(
            team.id, "testuser2", "member", inviter_id=test_user.id
        )
        assert member.username == "testuser2"
        assert member.role == "member"

    async def test_invite_owner_fails(
        self, db_session: AsyncSession, test_user: User, test_user2: User
    ) -> None:
        svc = TeamService(db_session)
        team = await svc.create_team(
            CreateTeamRequest(name="Team B"), creator_id=test_user.id
        )

        with pytest.raises(ValueError, match="Cannot invite"):
            await svc.invite_member(
                team.id, "testuser2", "owner", inviter_id=test_user.id
            )

    async def test_invite_non_admin_fails(
        self, db_session: AsyncSession, test_user: User, test_user2: User
    ) -> None:
        svc = TeamService(db_session)
        team = await svc.create_team(
            CreateTeamRequest(name="Team C"), creator_id=test_user.id
        )

        # Add test_user2 as viewer (non-admin)
        await svc.invite_member(
            team.id, "testuser2", "viewer", inviter_id=test_user.id
        )

        # test_user2 tries to invite — should fail
        with pytest.raises(PermissionError):
            await svc.invite_member(
                team.id, "testuser", "member", inviter_id=test_user2.id
            )

    async def test_remove_member(
        self, db_session: AsyncSession, test_user: User, test_user2: User
    ) -> None:
        svc = TeamService(db_session)
        team = await svc.create_team(
            CreateTeamRequest(name="Team D"), creator_id=test_user.id
        )
        await svc.invite_member(
            team.id, "testuser2", "member", inviter_id=test_user.id
        )

        removed = await svc.remove_member(team.id, test_user2.id)
        assert removed is True

        is_member = await svc.is_member(team.id, test_user2.id)
        assert is_member is False

    async def test_update_member_role(
        self, db_session: AsyncSession, test_user: User, test_user2: User
    ) -> None:
        svc = TeamService(db_session)
        team = await svc.create_team(
            CreateTeamRequest(name="Team E"), creator_id=test_user.id
        )
        await svc.invite_member(
            team.id, "testuser2", "member", inviter_id=test_user.id
        )

        result = await svc.update_member_role(
            team.id, test_user2.id, "admin", requester_id=test_user.id
        )
        assert result is not None
        assert result.role == "admin"

    async def test_list_user_teams(
        self, db_session: AsyncSession, test_user: User
    ) -> None:
        svc = TeamService(db_session)
        await svc.create_team(
            CreateTeamRequest(name="Team 1"), creator_id=test_user.id
        )
        await svc.create_team(
            CreateTeamRequest(name="Team 2"), creator_id=test_user.id
        )

        teams = await svc.list_user_teams(test_user.id)
        assert len(teams) == 2

    async def test_get_team_detail(
        self, db_session: AsyncSession, test_user: User, test_user2: User
    ) -> None:
        svc = TeamService(db_session)
        team = await svc.create_team(
            CreateTeamRequest(name="Detail Team"), creator_id=test_user.id
        )
        await svc.invite_member(
            team.id, "testuser2", "member", inviter_id=test_user.id
        )

        detail = await svc.get_team_detail(team.id)
        assert detail is not None
        assert detail.member_count == 2
        assert len(detail.members) == 2
