"""Notification preference repository — database operations."""

from __future__ import annotations

import uuid as _uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.notification_preference import (
    NotificationPreference,
)


class NotificationPreferenceRepository:
    """Repository for notification preference CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, user_id: _uuid.UUID) -> NotificationPreference:
        """Get existing preferences or create default ones for the user."""
        result = await self._session.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
            ),
        )
        entry = result.scalar_one_or_none()

        if entry is not None:
            return entry

        # Create default preferences
        entry = NotificationPreference(
            user_id=user_id,
            email_enabled=True,
            email_analysis_completed=True,
            email_analysis_failed=True,
            email_team_invite=True,
            email_team_removed=True,
            email_team_role_changed=True,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get(self, user_id: _uuid.UUID) -> NotificationPreference | None:
        """Get preferences for a user. Returns None if not found."""
        result = await self._session.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
            ),
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        user_id: _uuid.UUID,
        *,
        email_enabled: bool | None = None,
        email_analysis_completed: bool | None = None,
        email_analysis_failed: bool | None = None,
        email_team_invite: bool | None = None,
        email_team_removed: bool | None = None,
        email_team_role_changed: bool | None = None,
    ) -> NotificationPreference | None:
        """Update notification preferences. Returns updated entry or None."""
        entry = await self.get_or_create(user_id)

        if email_enabled is not None:
            entry.email_enabled = email_enabled
        if email_analysis_completed is not None:
            entry.email_analysis_completed = email_analysis_completed
        if email_analysis_failed is not None:
            entry.email_analysis_failed = email_analysis_failed
        if email_team_invite is not None:
            entry.email_team_invite = email_team_invite
        if email_team_removed is not None:
            entry.email_team_removed = email_team_removed
        if email_team_role_changed is not None:
            entry.email_team_role_changed = email_team_role_changed

        await self._session.flush()
        return entry

    async def should_send_email(
        self,
        user_id: _uuid.UUID,
        event_type: str,
    ) -> bool:
        """Check if an email should be sent for the given event type.

        Returns True if:
        1. Email is globally enabled (email_enabled = True)
        2. The specific event type toggle is True
        3. Preferences exist (creates defaults if not)
        """
        entry = await self.get_or_create(user_id)

        if not entry.email_enabled:
            return False

        # Map event types to preference fields
        field_map = {
            "analysis.completed": entry.email_analysis_completed,
            "analysis.failed": entry.email_analysis_failed,
            "team.invite": entry.email_team_invite,
            "team.removed": entry.email_team_removed,
            "team.role_changed": entry.email_team_role_changed,
        }

        return field_map.get(event_type, False)
