"""Notification preference service — business logic."""

from __future__ import annotations

import uuid as _uuid

from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.modules.notification_preferences.repository import (
    NotificationPreferenceRepository,
)
from app.modules.notification_preferences.schemas import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)

_logger = get_logger(__name__)


class NotificationPreferenceService:
    """Encapsulates notification preference management logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = NotificationPreferenceRepository(session)

    async def get_preferences(
        self,
        user_id: _uuid.UUID,
    ) -> NotificationPreferenceResponse:
        """Get notification preferences for a user. Creates defaults if none exist."""
        entry = await self._repo.get_or_create(user_id)
        return NotificationPreferenceResponse.model_validate(entry)

    async def update_preferences(
        self,
        user_id: _uuid.UUID,
        update: NotificationPreferenceUpdate,
    ) -> NotificationPreferenceResponse:
        """Update notification preferences for a user."""
        entry = await self._repo.update(
            user_id,
            email_enabled=update.email_enabled,
            email_analysis_completed=update.email_analysis_completed,
            email_analysis_failed=update.email_analysis_failed,
            email_team_invite=update.email_team_invite,
            email_team_removed=update.email_team_removed,
            email_team_role_changed=update.email_team_role_changed,
        )
        if entry is None:
            # Should never happen since get_or_create is called in update
            entry = await self._repo.get_or_create(user_id)

        _logger.info(
            "Notification preferences updated",
            user_id=str(user_id),
        )
        return NotificationPreferenceResponse.model_validate(entry)

    async def should_send_email(
        self,
        user_id: _uuid.UUID,
        event_type: str,
    ) -> bool:
        """Check if an email should be sent for the given event type."""
        return await self._repo.should_send_email(user_id, event_type)
