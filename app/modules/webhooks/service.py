"""Webhook service — CRUD, event firing, and test pings."""

from __future__ import annotations

import secrets
import uuid
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.config import WebhookConfig
from app.modules.webhooks.delivery import (
    deliver_webhook,
    new_test_payload,
)
from app.modules.webhooks.models import Webhook
from app.modules.webhooks.repository import (
    WebhookDeliveryRepository,
    WebhookRepository,
)
from app.modules.webhooks.schemas import (
    EVENT_TEST_PING,
    SECRET_PREFIX,
    DeliverySummary,
    WebhookCreate,
    WebhookListResponse,
    WebhookResponse,
    WebhookTestResult,
    WebhookUpdate,
    mask_secret,
)

_logger = get_logger(__name__)


def _generate_secret() -> str:
    """Generate a cryptographically random webhook secret."""
    return f"{SECRET_PREFIX}{secrets.token_urlsafe(32)}"


class WebhookService:
    """Encapsulates webhook management and delivery logic."""

    def __init__(
        self,
        session: AsyncSession,
        config: WebhookConfig | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._session = session
        self._config = config or WebhookConfig()
        self._transport = transport
        self._webhooks = WebhookRepository(session)
        self._deliveries = WebhookDeliveryRepository(session)

    # ── Read ────────────────────────────────────────────────────

    async def list_webhooks(self, user_id: uuid.UUID) -> WebhookListResponse:
        """List the user's webhooks with their latest delivery outcome."""
        webhooks = await self._webhooks.list_by_user(user_id)
        latest = await self._deliveries.latest_for_webhooks(
            [webhook.id for webhook in webhooks]
        )
        return WebhookListResponse(
            items=[
                self._to_response(webhook, latest.get(webhook.id))
                for webhook in webhooks
            ],
            total=len(webhooks),
        )

    async def get_webhook(
        self, webhook_id: uuid.UUID, user_id: uuid.UUID
    ) -> WebhookResponse | None:
        """Return one webhook if it belongs to the user."""
        webhook = await self._webhooks.get_for_user(webhook_id, user_id)
        if webhook is None:
            return None
        latest = (await self._deliveries.latest_for_webhooks([webhook.id])).get(
            webhook.id
        )
        return self._to_response(webhook, latest)

    # ── Write ────────────────────────────────────────────────────

    async def create_webhook(
        self, user_id: uuid.UUID, data: WebhookCreate
    ) -> WebhookResponse:
        """Create a webhook (generating a secret when not supplied)."""
        webhook = await self._webhooks.create(
            Webhook(
                user_id=user_id,
                name=data.name.strip(),
                url=data.url,
                events=data.events,
                secret=data.secret or _generate_secret(),
                is_active=True,
            )
        )
        _logger.info(
            "Webhook created",
            user_id=str(user_id),
            webhook_id=str(webhook.id),
            events=webhook.events,
        )
        return self._to_response(webhook, None)

    async def update_webhook(
        self,
        webhook_id: uuid.UUID,
        user_id: uuid.UUID,
        data: WebhookUpdate,
    ) -> WebhookResponse | None:
        """Partially update a webhook (ownership-checked)."""
        webhook = await self._webhooks.get_for_user(webhook_id, user_id)
        if webhook is None:
            return None

        updates: dict[str, Any] = {}
        if data.name is not None:
            updates["name"] = data.name.strip()
        if data.url is not None:
            updates["url"] = data.url
        if data.events is not None:
            updates["events"] = data.events
        if data.is_active is not None:
            updates["is_active"] = data.is_active
        if data.regenerate_secret:
            updates["secret"] = _generate_secret()

        webhook = await self._webhooks.update(webhook_id, updates)
        if webhook is None:
            return None
        latest = (await self._deliveries.latest_for_webhooks([webhook.id])).get(
            webhook.id
        )
        return self._to_response(webhook, latest)

    async def delete_webhook(self, webhook_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a webhook (ownership-checked)."""
        webhook = await self._webhooks.get_for_user(webhook_id, user_id)
        if webhook is None:
            return False
        return await self._webhooks.delete(webhook.id)

    # ── Delivery ─────────────────────────────────────────────────

    async def fire_event(
        self,
        *,
        user_id: uuid.UUID,
        event: str,
        payload: dict[str, Any],
        session_id: uuid.UUID | None = None,
    ) -> None:
        """Deliver ``event`` to every matching active webhook of the user."""
        webhooks = await self._webhooks.list_active_for_events(user_id, [event])
        if not webhooks:
            return
        for webhook in webhooks:
            delivery = await self._deliveries.create_delivery(
                webhook_id=webhook.id,
                event=event,
                session_id=session_id,
                payload=payload,
                max_attempts=self._config.retry_attempts,
            )
            await deliver_webhook(
                self._session,
                delivery,
                webhook,
                config=self._config,
                transport=self._transport,
            )

    async def test_webhook(
        self, webhook_id: uuid.UUID, user_id: uuid.UUID
    ) -> WebhookTestResult | None:
        """Send a single-request test ping and return the outcome."""
        webhook = await self._webhooks.get_for_user(webhook_id, user_id)
        if webhook is None:
            return None

        payload = new_test_payload()
        delivery = await self._deliveries.create_delivery(
            webhook_id=webhook.id,
            event=EVENT_TEST_PING,
            session_id=None,
            payload=payload,
            max_attempts=1,
        )
        await deliver_webhook(
            self._session,
            delivery,
            webhook,
            config=self._config,
            transport=self._transport,
        )
        return WebhookTestResult(
            delivery_id=delivery.id,
            event=EVENT_TEST_PING,
            status=delivery.status,
            attempts=delivery.attempts,
            last_status_code=delivery.last_status_code,
            last_error=delivery.last_error,
        )

    # ── Helpers ─────────────────────────────────────────────────

    def _to_response(
        self,
        webhook: Webhook,
        latest: Any | None,
    ) -> WebhookResponse:
        """Map a Webhook ORM row to its response schema."""
        last_delivery: DeliverySummary | None = None
        if latest is not None:
            last_delivery = DeliverySummary(
                delivery_id=latest.id,
                event=latest.event,
                status=latest.status,
                attempts=latest.attempts,
                last_status_code=latest.last_status_code,
                last_error=latest.last_error,
                created_at=latest.created_at,
            )
        return WebhookResponse(
            id=webhook.id,
            name=webhook.name,
            url=webhook.url,
            events=list(webhook.events),
            secret_masked=mask_secret(webhook.secret),
            is_active=webhook.is_active,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
            last_delivery=last_delivery,
        )
