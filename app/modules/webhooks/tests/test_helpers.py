"""Tests for the ``fire_webhooks`` helper — best-effort semantics."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.webhooks.helpers import fire_webhooks
from app.modules.webhooks.tests.conftest import create_webhook


class TestFireWebhooks:
    """Firing must be a no-op without a user and must never raise."""

    async def test_no_user_is_noop(
        self, db_session: AsyncSession, test_user: object
    ) -> None:
        await create_webhook(db_session, test_user.id)
        # Should return without constructing the service or touching the db.
        await fire_webhooks(
            db_session,
            user_id=None,
            event="analysis.completed",
            payload={"event": "analysis.completed"},
        )
        await fire_webhooks(
            db_session,
            user_id="",
            event="analysis.completed",
            payload={"event": "analysis.completed"},
        )

    async def test_swallows_service_errors(
        self,
        db_session: AsyncSession,
        test_user: object,
        monkeypatch: object,
    ) -> None:
        class Boom:
            def __init__(self, **kwargs: object) -> None:
                pass

            async def fire_event(self, **kwargs: object) -> None:
                raise RuntimeError("delivery backend exploded")

        monkeypatch.setattr(
            "app.modules.webhooks.helpers.WebhookService", Boom
        )
        # Must not raise despite the backend error.
        await fire_webhooks(
            db_session,
            user_id=test_user.id,
            event="analysis.completed",
            payload={"event": "analysis.completed"},
        )
