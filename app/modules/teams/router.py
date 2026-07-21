"""Team management API routes.

Endpoints:
  GET    /teams              — List teams for current user
  POST   /teams              — Create a new team
  GET    /teams/{team_id}    — Get team details with members
  PATCH  /teams/{team_id}    — Update team name/description
  DELETE /teams/{team_id}    — Delete a team
  POST   /teams/{team_id}/members      — Invite a member
  PATCH  /teams/{team_id}/members/{uid} — Update member role
  DELETE /teams/{team_id}/members/{uid} — Remove a member
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.modules.auth.middleware import get_current_user
from app.modules.auth.models import User
from app.modules.teams.schemas import (
    CreateTeamRequest,
    InviteMemberRequest,
    UpdateMemberRoleRequest,
    UpdateTeamRequest,
)
from app.modules.teams.service import TeamService

router = APIRouter(prefix="/teams", tags=["Teams"])


def _get_service(db_session: AsyncSession = Depends(get_db)) -> TeamService:
    return TeamService(session=db_session)


# ── Team CRUD ──────────────────────────────────────────────────


@router.get(
    "",
    summary="List my teams",
    description="List all teams the authenticated user belongs to.",
)
async def list_my_teams(
    user: User = Depends(get_current_user),
    service: TeamService = Depends(_get_service),
) -> dict[str, Any]:
    teams = await service.list_user_teams(user.id)
    return {
        "data": [t.model_dump(mode="json") for t in teams],
        "meta": {},
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a team",
)
async def create_team(
    body: CreateTeamRequest,
    user: User = Depends(get_current_user),
    service: TeamService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        team = await service.create_team(body, creator_id=user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return {"data": team.model_dump(mode="json"), "meta": {}}


@router.get(
    "/{team_id}",
    summary="Get team details",
    description="Get team info with member list.",
)
async def get_team(
    team_id: str,
    user: User = Depends(get_current_user),
    service: TeamService = Depends(_get_service),
) -> dict[str, Any]:
    import uuid
    try:
        tid = uuid.UUID(team_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid team ID") from None

    # Check membership
    if not await service.is_member(tid, user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )

    detail = await service.get_team_detail(tid)
    if detail is None:
        raise HTTPException(status_code=404, detail="Team not found")

    return {"data": detail.model_dump(mode="json"), "meta": {}}


@router.patch(
    "/{team_id}",
    summary="Update team",
)
async def update_team(
    team_id: str,
    body: UpdateTeamRequest,
    user: User = Depends(get_current_user),
    service: TeamService = Depends(_get_service),
) -> dict[str, Any]:
    import uuid
    try:
        tid = uuid.UUID(team_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid team ID") from None

    # Only owners/admins can update
    from app.modules.teams.models import TeamMemberRole
    from app.modules.teams.repository import TeamMemberRepository

    member_repo = TeamMemberRepository(service._session)
    membership = await member_repo.get_membership(tid, user.id)
    if not membership or membership.role not in {
        TeamMemberRole.OWNER, TeamMemberRole.ADMIN
    }:
        raise HTTPException(
            status_code=403, detail="Only team owners and admins can update"
        )

    try:
        team = await service.update_team(tid, body)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")

    return {"data": {"id": str(team.id), "name": team.name, "description": team.description}, "meta": {}}


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete team",
)
async def delete_team(
    team_id: str,
    user: User = Depends(get_current_user),
    service: TeamService = Depends(_get_service),
) -> None:
    import uuid
    try:
        tid = uuid.UUID(team_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid team ID") from None

    from app.modules.teams.models import TeamMemberRole
    from app.modules.teams.repository import TeamMemberRepository

    member_repo = TeamMemberRepository(service._session)
    membership = await member_repo.get_membership(tid, user.id)
    if not membership or membership.role != TeamMemberRole.OWNER:
        raise HTTPException(
            status_code=403, detail="Only the team owner can delete"
        )

    await service.delete_team(tid)


# ── Membership ─────────────────────────────────────────────────


@router.post(
    "/{team_id}/members",
    status_code=status.HTTP_201_CREATED,
    summary="Invite member to team",
)
async def invite_member(
    team_id: str,
    body: InviteMemberRequest,
    user: User = Depends(get_current_user),
    service: TeamService = Depends(_get_service),
) -> dict[str, Any]:
    import uuid
    try:
        tid = uuid.UUID(team_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid team ID") from None

    try:
        member = await service.invite_member(
            tid, body.username, body.role, inviter_id=user.id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return {"data": member.model_dump(mode="json"), "meta": {}}


@router.patch(
    "/{team_id}/members/{user_id}",
    summary="Update member role",
)
async def update_member_role(
    team_id: str,
    user_id: str,
    body: UpdateMemberRoleRequest,
    user: User = Depends(get_current_user),
    service: TeamService = Depends(_get_service),
) -> dict[str, Any]:
    import uuid as uuid_mod
    try:
        tid = uuid_mod.UUID(team_id)
        uid = uuid_mod.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid team or user ID") from None

    try:
        result = await service.update_member_role(
            tid, uid, body.role, requester_id=user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="Member not found")

    return {"data": result.model_dump(mode="json"), "meta": {}}


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member from team",
)
async def remove_member(
    team_id: str,
    user_id: str,
    user: User = Depends(get_current_user),
    service: TeamService = Depends(_get_service),
) -> None:
    import uuid as uuid_mod
    try:
        tid = uuid_mod.UUID(team_id)
        uid = uuid_mod.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid team or user ID") from None

    # Users can remove themselves, or admins/owners can remove others
    from app.modules.teams.models import TeamMemberRole
    from app.modules.teams.repository import TeamMemberRepository

    member_repo = TeamMemberRepository(service._session)

    if uid != user.id:
        # Removing someone else — need admin/owner role
        membership = await member_repo.get_membership(tid, user.id)
        if not membership or membership.role not in {
            TeamMemberRole.OWNER, TeamMemberRole.ADMIN
        }:
            raise HTTPException(
                status_code=403,
                detail="Only team owners and admins can remove members",
            )

        # Can't remove the owner
        target = await member_repo.get_membership(tid, uid)
        if target and target.role == TeamMemberRole.OWNER:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove the team owner",
            )

    removed = await service.remove_member(tid, uid)
    if not removed:
        raise HTTPException(status_code=404, detail="Member not found")
