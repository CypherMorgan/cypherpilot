"""Notification preference API routes.

Endpoints:
  GET  /notification-preferences       — Get current preferences
  PATCH /notification-preferences      — Update preferences
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.modules.auth.middleware import get_current_user
from app.modules.auth.models import User
from app.modules.notification_preferences.schemas import (
    NotificationPreferenceUpdate,
)
from app.modules.notification_preferences.service import (
    NotificationPreferenceService,
)

router = APIRouter(
    prefix="/notification-preferences",
    tags=["Notification Preferences"],
)


async def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationPreferenceService:
    return NotificationPreferenceService(session=db)


@router.get(
    "",
    summary="Get notification preferences",
    description="Get email notification preferences for the current user.",
)
async def get_preferences(
    service: Annotated[NotificationPreferenceService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get notification preferences for the authenticated user."""
    result = await service.get_preferences(user_id=user.id)
    return {"data": result.model_dump(mode="json")}


@router.patch(
    "",
    summary="Update notification preferences",
    description="Update email notification preferences for the current user.",
)
async def update_preferences(
    update: NotificationPreferenceUpdate,
    service: Annotated[NotificationPreferenceService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Update notification preferences for the authenticated user."""
    result = await service.update_preferences(
        user_id=user.id,
        update=update,
    )
    return {"data": result.model_dump(mode="json")}
