"""Notification API routes.

Endpoints:
  GET    /notifications        — List notifications with pagination
  GET    /notifications/unread — Get unread count
  PATCH  /notifications/{id}/read — Mark one as read
  PATCH  /notifications/read-all  — Mark all as read
  DELETE /notifications/{id}      — Delete a notification
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.modules.auth.middleware import get_current_user
from app.modules.auth.models import User
from app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


async def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationService:
    return NotificationService(session=db)


@router.get(
    "",
    summary="List notifications",
    description="List notifications for the current user with pagination.",
)
async def list_notifications(
    service: Annotated[NotificationService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
) -> dict[str, Any]:
    """List notifications for the authenticated user."""
    result = await service.list_notifications(
        user_id=user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )
    return {"data": result.model_dump(mode="json")}


@router.get(
    "/unread",
    summary="Get unread count",
    description="Get the number of unread notifications for the current user.",
)
async def get_unread_count(
    service: Annotated[NotificationService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get unread notification count."""
    count = await service.get_unread_count(user_id=user.id)
    return {"data": {"count": count}}


@router.patch(
    "/{notification_id}/read",
    summary="Mark notification as read",
    description="Mark a single notification as read.",
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    service: Annotated[NotificationService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Mark a notification as read."""
    _ = user  # authenticated user required for access control
    result = await service.mark_read(notification_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"data": result.model_dump(mode="json")}


@router.patch(
    "/read-all",
    summary="Mark all as read",
    description="Mark all notifications as read for the current user.",
)
async def mark_all_read(
    service: Annotated[NotificationService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Mark all notifications as read."""
    count = await service.mark_all_read(user_id=user.id)
    return {"data": {"count": count}}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete notification",
    description="Delete a single notification.",
)
async def delete_notification(
    notification_id: uuid.UUID,
    service: Annotated[NotificationService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a notification."""
    _ = user  # authenticated user required for access control
    deleted = await service.delete_notification(notification_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
