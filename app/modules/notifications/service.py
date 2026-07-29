"""Notification service — business logic for notifications."""

from __future__ import annotations

import uuid as _uuid

from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationResponse,
)

_logger = get_logger(__name__)


class NotificationService:
    """Encapsulates notification management logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = NotificationRepository(session)

    async def create_notification(
        self,
        *,
        user_id: _uuid.UUID,
        type_: str,
        title: str,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> NotificationResponse:
        """Create a new notification for a user."""
        entry = await self._repo.create(
            user_id=user_id,
            type_=type_,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        _logger.info(
            "Notification created",
            user_id=str(user_id),
            type=type_,
        )
        return NotificationResponse.model_validate(entry)

    async def list_notifications(
        self,
        *,
        user_id: _uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> NotificationListResponse:
        """List notifications for a user."""
        items, total, unread_count = await self._repo.list_notifications(
            user_id=user_id,
            page=page,
            page_size=page_size,
            unread_only=unread_only,
        )
        return NotificationListResponse(
            items=[NotificationResponse.model_validate(n) for n in items],
            total=total,
            unread_count=unread_count,
        )

    async def mark_read(self, notification_id: _uuid.UUID) -> NotificationResponse | None:
        """Mark a notification as read."""
        entry = await self._repo.mark_read(notification_id)
        if entry is None:
            return None
        return NotificationResponse.model_validate(entry)

    async def mark_all_read(self, user_id: _uuid.UUID) -> int:
        """Mark all notifications as read for a user."""
        return await self._repo.mark_all_read(user_id)

    async def delete_notification(self, notification_id: _uuid.UUID) -> bool:
        """Delete a notification."""
        return await self._repo.delete(notification_id)

    async def get_unread_count(self, user_id: _uuid.UUID) -> int:
        """Get unread notification count for a user."""
        _, _, unread = await self._repo.list_notifications(
            user_id=user_id,
            page=1,
            page_size=1,
        )
        return unread
