"""Notification helper for router handlers.

Provides a non-blocking ``create_notification`` function that can be
called from any service to record a notification.  Errors are swallowed
— notifications never break the main flow.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.service import NotificationService


async def create_notification(
    db: AsyncSession,
    *,
    user_id: Any,
    type_: str,
    title: str,
    message: str,
    resource_type: str | None = None,
    resource_id: Any = None,
) -> None:
    """Create a notification. Non-blocking — errors are swallowed."""
    try:
        service = NotificationService(session=db)
        await service.create_notification(
            user_id=user_id,
            type_=type_,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
        )
    except Exception:
        # Notifications are best-effort — never fail the main request
        pass
