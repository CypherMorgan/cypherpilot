"""Notification repository — database operations for notifications."""

from __future__ import annotations

import uuid as _uuid

from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.notification import Notification


class NotificationRepository:
    """Repository for notification CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: _uuid.UUID,
        type_: str,
        title: str,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> Notification:
        """Create and persist a new notification."""
        entry = Notification(
            user_id=user_id,
            type=type_,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_notifications(
        self,
        *,
        user_id: _uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> tuple[list[Notification], int, int]:
        """List notifications for a user with pagination.

        Returns:
            Tuple of (items, total_count, unread_count).
        """
        base = select(Notification).where(Notification.user_id == user_id)
        base_count = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
        )

        if unread_only:
            base = base.where(Notification.read == False)  # noqa: E712
            base_count = base_count.where(
                Notification.read == False,  # noqa: E712
            )

        # Total count
        total_result = await self._session.execute(base_count)
        total = total_result.scalar() or 0

        # Unread count (always)
        unread_result = await self._session.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.read == False,  # noqa: E712
            ),
        )
        unread_count = unread_result.scalar() or 0

        # Paginate
        query = (
            base.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(query)
        items = list(result.scalars().all())

        return items, total, unread_count

    async def mark_read(self, notification_id: _uuid.UUID) -> Notification | None:
        """Mark a single notification as read. Returns updated notification or None."""
        entry = await self._session.get(Notification, notification_id)
        if entry is None:
            return None
        entry.read = True
        await self._session.flush()
        return entry

    async def mark_all_read(self, user_id: _uuid.UUID) -> int:
        """Mark all of a user's notifications as read. Returns count affected."""
        # Count unread first
        count_result = await self._session.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.read == False,  # noqa: E712
            ),
        )
        count: int = count_result.scalar() or 0

        if count == 0:
            return 0

        # Mark all as read
        await self._session.execute(
            sa_update(Notification)
            .where(Notification.user_id == user_id, Notification.read == False)  # noqa: E712
            .values(read=True),
        )
        await self._session.flush()
        return count

    async def delete(self, notification_id: _uuid.UUID) -> bool:
        """Delete a notification. Returns True if deleted."""
        entry = await self._session.get(Notification, notification_id)
        if entry is None:
            return False
        await self._session.delete(entry)
        await self._session.flush()
        return True
