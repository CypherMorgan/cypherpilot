"""Webhook repositories — persistence for webhooks and deliveries."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select

from app.infrastructure.repository import BaseRepository
from app.modules.webhooks.models import Webhook, WebhookDelivery


class WebhookRepository(BaseRepository[Webhook]):
    """Persistence for webhook endpoints."""

    model_class = Webhook

    async def list_by_user(self, user_id: uuid.UUID) -> list[Webhook]:
        """Return all webhooks owned by ``user_id`` (newest first)."""
        stmt = (
            select(self.model_class)
            .where(self.model_class.user_id == user_id)
            .order_by(self.model_class.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_active_for_events(
        self, user_id: uuid.UUID, events: list[str]
    ) -> list[Webhook]:
        """Return active webhooks owned by ``user_id`` subscribed to any of ``events``.

        Matching happens in Python on the JSON ``events`` column to stay
        database-agnostic (SQLite JSON filters differ from PostgreSQL).
        """
        stmt = select(self.model_class).where(
            self.model_class.user_id == user_id,
            self.model_class.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        subscribed = {
            webhook.id
            for webhook in result.scalars().all()
            if any(event in webhook.events for event in events)
        }
        if not subscribed:
            return []
        stmt = select(self.model_class).where(self.model_class.id.in_(subscribed))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(
        self, webhook_id: uuid.UUID, user_id: uuid.UUID
    ) -> Webhook | None:
        """Return a webhook only if it belongs to ``user_id``."""
        stmt = select(self.model_class).where(
            self.model_class.id == webhook_id,
            self.model_class.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class WebhookDeliveryRepository(BaseRepository[WebhookDelivery]):
    """Persistence for webhook delivery history."""

    model_class = WebhookDelivery

    async def create_delivery(
        self,
        *,
        webhook_id: uuid.UUID,
        event: str,
        session_id: uuid.UUID | None,
        payload: dict[str, Any] | None,
        max_attempts: int,
    ) -> WebhookDelivery:
        """Create a new pending delivery record."""
        return await self.create(
            WebhookDelivery(
                webhook_id=webhook_id,
                event=event,
                session_id=session_id,
                payload=payload,
                status="pending",
                attempts=0,
                max_attempts=max_attempts,
            )
        )

    async def record_attempt(
        self,
        delivery: WebhookDelivery,
        *,
        attempts: int,
        status: str,
        last_status_code: int | None = None,
        last_error: str | None = None,
    ) -> None:
        """Persist the outcome of a delivery attempt."""
        delivery.attempts = attempts
        delivery.status = status
        delivery.last_status_code = last_status_code
        delivery.last_error = last_error
        await self._session.commit()
        await self._session.refresh(delivery)

    async def latest_for_webhooks(
        self, webhook_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, WebhookDelivery]:
        """Return the most recent delivery per webhook id (empty if none)."""
        if not webhook_ids:
            return {}
        stmt = (
            select(self.model_class)
            .where(self.model_class.webhook_id.in_(webhook_ids))
            .order_by(self.model_class.created_at.desc())
        )
        result = await self._session.execute(stmt)
        latest: dict[uuid.UUID, WebhookDelivery] = {}
        for delivery in result.scalars().all():
            latest.setdefault(delivery.webhook_id, delivery)
        return latest
