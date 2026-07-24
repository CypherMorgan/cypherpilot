"""Audit log API routes.

Endpoints:
  GET /audit  — List audit logs with filtering and pagination
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.modules.audit.service import AuditService
from app.modules.auth.middleware import get_optional_current_user
from app.modules.auth.models import User

router = APIRouter(prefix="/audit", tags=["Audit"])


async def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuditService:
    return AuditService(session=db)


@router.get(
    "",
    summary="List audit logs",
    description="List audit log entries with optional filtering by team, user, or action prefix.",
)
async def list_audit_logs(
    service: Annotated[AuditService, Depends(_get_service)],
    user: Annotated[User | None, Depends(get_optional_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    team_id: uuid.UUID | None = Query(None),
    action_prefix: str | None = Query(None),
) -> dict[str, Any]:
    """List audit logs with optional team/user/action filtering."""
    # Non-admin users can only see their own logs (unless team_id is specified)
    filter_user_id: uuid.UUID | None = None
    if user and user.role.value != "admin":
        filter_user_id = user.id

    result = await service.list_logs(
        page=page,
        page_size=page_size,
        team_id=team_id,
        user_id=filter_user_id,
        action_prefix=action_prefix,
    )

    return {
        "data": result.model_dump(),
        "meta": {},
    }
