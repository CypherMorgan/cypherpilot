"""Notification preference Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationPreferenceResponse(BaseModel):
    """Current notification preferences for the authenticated user."""

    id: uuid.UUID
    user_id: uuid.UUID
    email_enabled: bool
    email_analysis_completed: bool
    email_analysis_failed: bool
    email_team_invite: bool
    email_team_removed: bool
    email_team_role_changed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    """Partial update for notification preferences.

    Only provided fields are updated; omitted fields keep their
    current value.
    """

    email_enabled: bool | None = None
    email_analysis_completed: bool | None = None
    email_analysis_failed: bool | None = None
    email_team_invite: bool | None = None
    email_team_removed: bool | None = None
    email_team_role_changed: bool | None = None
