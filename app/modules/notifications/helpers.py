"""Notification helper for router handlers.

Provides a non-blocking ``create_notification`` function that can be
called from any service to record a notification.  After persisting
the in-app notification, it also sends an email if the user has
email notifications enabled for the event type.

Errors are swallowed — notifications and emails never break the main flow.
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
    extra: dict[str, Any] | None = None,
) -> None:
    """Create a notification and send email if enabled.

    Non-blocking — errors are swallowed.
    """
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

    # Send email notification (also best-effort, also swallowed)
    try:
        from app.modules.notification_preferences.helpers import (
            send_notification_email,
        )

        await send_notification_email(
            db,
            user_id=user_id,
            type_=type_,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
            extra=extra,
        )
    except Exception:
        pass
