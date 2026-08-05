"""Tests for the webhook service — CRUD, event firing, and test pings.

HTTP delivery is exercised through an injected ``httpx.MockTransport`` so
no real network I/O occurs.
"""

from __future__ import annotations

import uuid

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import WebhookConfig
from app.modules.webhooks.schemas import (
    EVENT_ANALYSIS_COMPLETED,
    EVENT_ANALYSIS_FAILED,
    EVENT_TEST_PING,
    SECRET_PREFIX,
    WebhookCreate,
    WebhookUpdate,
)
from app.modules.webhooks.service import WebhookService
from app.modules.webhooks.tests.conftest import create_webhook


def _service(
    db_session: AsyncSession, handler: object
) -> WebhookService:
    return WebhookService(
        session=db_session,
        config=WebhookConfig(
            retry_attempts=3, retry_backoff_base_seconds=0
        ),
        transport=httpx.MockTransport(handler),
    )


def _ok_handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200)


class TestCreateWebhook:
    """Webhook creation must generate/mask secrets correctly."""

    async def test_generates_secret_when_omitted(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        service = WebhookService(session=db_session)
        data = WebhookCreate(
            name="Deploy Hook",
            url="https://hooks.example.com/deploy",
            events=[EVENT_ANALYSIS_COMPLETED],
        )
        response = await service.create_webhook(user_id=test_user.id, data=data)

        assert response.name == "Deploy Hook"
        assert response.events == [EVENT_ANALYSIS_COMPLETED]
        assert response.secret_masked.startswith(SECRET_PREFIX)

    async def test_uses_custom_secret(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        service = WebhookService(session=db_session)
        data = WebhookCreate(
            name="Hook",
            url="https://example.com/hook",
            events=[EVENT_ANALYSIS_FAILED],
            secret="whsec_mysecret1234567890abcd",
        )
        response = await service.create_webhook(user_id=test_user.id, data=data)

        assert response.secret_masked == "whsec_****abcd"


class TestListWebhooks:
    """Listing must be scoped to the owner."""

    async def test_empty_list(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        service = WebhookService(session=db_session)
        result = await service.list_webhooks(user_id=test_user.id)
        assert result.items == []
        assert result.total == 0

    async def test_lists_own_webhooks_only(
        self,
        db_session: AsyncSession,
        test_user: object,
        test_user2: object,
    ) -> None:
        await create_webhook(db_session, test_user.id, name="Mine")
        await create_webhook(db_session, test_user2.id, name="Theirs")

        service = WebhookService(session=db_session)
        result = await service.list_webhooks(user_id=test_user.id)

        assert result.total == 1
        assert result.items[0].name == "Mine"

    async def test_list_includes_latest_delivery(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        await create_webhook(db_session, test_user.id)

        # Record a delivered outcome by firing a real (mocked) event.
        service = _service(db_session, _ok_handler)
        await service.fire_event(
            user_id=test_user.id,
            event=EVENT_ANALYSIS_COMPLETED,
            payload={"event": EVENT_ANALYSIS_COMPLETED},
        )

        result = await service.list_webhooks(user_id=test_user.id)
        assert result.total == 1
        last = result.items[0].last_delivery
        assert last is not None
        assert last.event == EVENT_ANALYSIS_COMPLETED
        assert last.status == "delivered"
        assert last.attempts == 1
        assert last.last_status_code == 200


class TestGetWebhook:
    """Single fetch must enforce ownership."""

    async def test_get_own(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id, name="Hook A")
        service = WebhookService(session=db_session)
        result = await service.get_webhook(webhook.id, test_user.id)
        assert result is not None
        assert result.name == "Hook A"

    async def test_get_foreign_returns_none(
        self,
        db_session: AsyncSession,
        test_user: object,
        test_user2: object,
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        service = WebhookService(session=db_session)
        result = await service.get_webhook(webhook.id, test_user2.id)
        assert result is None


class TestUpdateWebhook:
    """Updates must be partial, ownership-checked, and validate change."""

    async def test_update_fields(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        service = WebhookService(session=db_session)
        result = await service.update_webhook(
            webhook.id,
            test_user.id,
            WebhookUpdate(
                name="Renamed",
                events=[EVENT_ANALYSIS_COMPLETED, EVENT_ANALYSIS_FAILED],
                is_active=False,
            ),
        )
        assert result is not None
        assert result.name == "Renamed"
        assert result.events == [
            EVENT_ANALYSIS_COMPLETED,
            EVENT_ANALYSIS_FAILED,
        ]
        assert result.is_active is False

    async def test_regenerate_secret_changes_masked_suffix(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        webhook = await create_webhook(
            db_session, test_user.id, secret="whsec_oldsecret111111111111"
        )
        service = WebhookService(session=db_session)
        before = (await service.get_webhook(webhook.id, test_user.id))
        assert before is not None

        after = await service.update_webhook(
            webhook.id,
            test_user.id,
            WebhookUpdate(regenerate_secret=True),
        )
        assert after is not None
        assert after.secret_masked != before.secret_masked
        assert after.secret_masked.startswith(SECRET_PREFIX)

    async def test_update_foreign_returns_none(
        self,
        db_session: AsyncSession,
        test_user: object,
        test_user2: object,
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        service = WebhookService(session=db_session)
        result = await service.update_webhook(
            webhook.id, test_user2.id, WebhookUpdate(name="Hijack")
        )
        assert result is None


class TestDeleteWebhook:
    """Deletion must be ownership-checked."""

    async def test_delete_own(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        service = WebhookService(session=db_session)
        assert await service.delete_webhook(webhook.id, test_user.id) is True
        assert await service.get_webhook(webhook.id, test_user.id) is None

    async def test_delete_foreign_returns_false(
        self,
        db_session: AsyncSession,
        test_user: object,
        test_user2: object,
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        service = WebhookService(session=db_session)
        assert await service.delete_webhook(webhook.id, test_user2.id) is False


class TestFireEvent:
    """Event firing must select only matching, active webhooks."""

    async def test_no_matching_webhook_no_delivery(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        await create_webhook(
            db_session, test_user.id, events=[EVENT_ANALYSIS_FAILED]
        )
        service = _service(db_session, _ok_handler)
        await service.fire_event(
            user_id=test_user.id,
            event=EVENT_ANALYSIS_COMPLETED,
            payload={"event": EVENT_ANALYSIS_COMPLETED},
        )
        # No delivery should exist for the non-matching event.
        result = await service.list_webhooks(user_id=test_user.id)
        assert result.items[0].last_delivery is None

    async def test_inactive_webhook_skipped(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        await create_webhook(
            db_session, test_user.id, is_active=False
        )
        service = _service(db_session, _ok_handler)
        await service.fire_event(
            user_id=test_user.id,
            event=EVENT_ANALYSIS_COMPLETED,
            payload={"event": EVENT_ANALYSIS_COMPLETED},
        )
        result = await service.list_webhooks(user_id=test_user.id)
        assert result.items[0].last_delivery is None

    async def test_delivers_to_matching_active_webhook(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        received: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            received.append(request.url)
            return httpx.Response(200)

        service = _service(db_session, handler)
        await service.fire_event(
            user_id=test_user.id,
            event=EVENT_ANALYSIS_COMPLETED,
            payload={"event": EVENT_ANALYSIS_COMPLETED, "session_id": "abc"},
            session_id=uuid.uuid4(),
        )

        assert len(received) == 1
        assert str(received[0]) == webhook.url
        result = await service.list_webhooks(user_id=test_user.id)
        last = result.items[0].last_delivery
        assert last is not None
        assert last.status == "delivered"

    async def test_other_users_webhooks_not_fired(
        self,
        db_session: AsyncSession,
        test_user: object,
        test_user2: object,
    ) -> None:
        await create_webhook(db_session, test_user2.id)
        calls: list[str] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            calls.append(str(request.url))
            return httpx.Response(200)

        service = _service(db_session, handler)
        await service.fire_event(
            user_id=test_user.id,
            event=EVENT_ANALYSIS_COMPLETED,
            payload={"event": EVENT_ANALYSIS_COMPLETED},
        )
        assert calls == []


class TestTestWebhook:
    """Manual test pings must return the delivery outcome."""

    async def test_test_ping_success(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        service = _service(db_session, _ok_handler)
        result = await service.test_webhook(webhook.id, test_user.id)

        assert result is not None
        assert result.event == EVENT_TEST_PING
        assert result.status == "delivered"
        assert result.last_status_code == 200
        assert result.attempts == 1

    async def test_test_ping_failure(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        service = _service(db_session, handler)
        result = await service.test_webhook(webhook.id, test_user.id)

        assert result is not None
        assert result.status == "failed"
        assert result.last_status_code == 500

    async def test_test_ping_foreign_returns_none(
        self,
        db_session: AsyncSession,
        test_user: object,
        test_user2: object,
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        service = _service(db_session, _ok_handler)
        result = await service.test_webhook(webhook.id, test_user2.id)
        assert result is None
