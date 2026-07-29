"""Notification Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """A single notification."""

    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    message: str
    resource_type: str | None = None
    resource_id: str | None = None
    read: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""

    items: list[NotificationResponse]
    total: int
    unread_count: int
