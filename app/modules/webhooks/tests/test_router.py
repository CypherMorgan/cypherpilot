"""Tests for Webhooks API endpoints.

Uses the full app with a real in-memory database. Users register via the
auth endpoint and the returned JWT authorizes webhook CRUD. The webhook
retry config is overridden to a single attempt so test pings complete
immediately (the target URL is unreachable, which is the point — the
delivery must be recorded as failed without hanging).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import cast

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient, Response

from app.config import WebhookConfig
from app.main import create_app
from app.modules.webhooks.router import _get_webhook_config

EVENT_COMPLETED = "analysis.completed"
EVENT_FAILED = "analysis.failed"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """App fixture: runs lifespan, creates schema, fast webhook retries."""
    app = create_app()
    app.dependency_overrides[_get_webhook_config] = lambda: WebhookConfig(
        retry_attempts=1,
        retry_backoff_base_seconds=0,
        request_timeout_seconds=2,
    )

    async with LifespanManager(app):
        db_manager = getattr(app.state, "db_manager", None)
        if db_manager is not None:
            await db_manager.create_all()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def _register(client: AsyncClient, username: str, email: str) -> str:
    """Register a user and return their access token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
            "display_name": username.title(),
        },
    )
    assert response.status_code == 201, response.text
    return cast(str, response.json()["access_token"])


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _body(response: Response) -> dict[str, object]:
    """Unwrap the standard ``{"data": ...}`` envelope."""
    return cast(dict[str, object], response.json()["data"])


def _payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "name": "CI Notifier",
        "url": "http://127.0.0.1:1/hook",
        "events": [EVENT_COMPLETED],
    }
    base.update(overrides)
    return base


class TestWebhooksAuth:
    """Auth gating for the webhook endpoints."""

    async def test_list_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/webhooks")
        assert response.status_code == 401

    async def test_create_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/webhooks", json=_payload())
        assert response.status_code == 401

    async def test_test_ping_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/webhooks/00000000-0000-0000-0000-000000000001/test"
        )
        assert response.status_code == 401


class TestCreateWebhookEndpoint:
    """POST /api/v1/webhooks."""

    async def test_create_success(self, client: AsyncClient) -> None:
        token = await _register(client, "whcr1", "whcr1@example.com")
        response = await client.post(
            "/api/v1/webhooks", json=_payload(), headers=_headers(token)
        )

        assert response.status_code == 201, response.text
        data = _body(response)
        assert data["name"] == "CI Notifier"
        assert data["events"] == [EVENT_COMPLETED]
        assert data["secret_masked"].startswith("whsec_****")
        assert data["is_active"] is True
        assert data["id"]

    async def test_create_normalizes_events(self, client: AsyncClient) -> None:
        token = await _register(client, "whcr2", "whcr2@example.com")
        response = await client.post(
            "/api/v1/webhooks",
            json=_payload(events=[EVENT_FAILED, EVENT_COMPLETED]),
            headers=_headers(token),
        )

        assert response.status_code == 201
        assert _body(response)["events"] == [EVENT_COMPLETED, EVENT_FAILED]

    async def test_create_rejects_bad_url(self, client: AsyncClient) -> None:
        token = await _register(client, "whcr3", "whcr3@example.com")
        response = await client.post(
            "/api/v1/webhooks",
            json=_payload(url="not-a-url"),
            headers=_headers(token),
        )
        assert response.status_code == 422

    async def test_create_rejects_unsupported_event(
        self, client: AsyncClient
    ) -> None:
        token = await _register(client, "whcr4", "whcr4@example.com")
        response = await client.post(
            "/api/v1/webhooks",
            json=_payload(events=["foo.bar"]),
            headers=_headers(token),
        )
        assert response.status_code == 422


class TestListWebhooksEndpoint:
    """GET /api/v1/webhooks."""

    async def test_list_empty(self, client: AsyncClient) -> None:
        token = await _register(client, "whls1", "whls1@example.com")
        response = await client.get(
            "/api/v1/webhooks", headers=_headers(token)
        )

        assert response.status_code == 200
        data = _body(response)
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_own_webhooks_only(self, client: AsyncClient) -> None:
        token_a = await _register(client, "whls2", "whls2@example.com")
        token_b = await _register(client, "whls3", "whls3@example.com")
        await client.post(
            "/api/v1/webhooks",
            json=_payload(name="Mine"),
            headers=_headers(token_a),
        )
        await client.post(
            "/api/v1/webhooks",
            json=_payload(name="Theirs"),
            headers=_headers(token_b),
        )

        response = await client.get(
            "/api/v1/webhooks", headers=_headers(token_a)
        )

        assert response.status_code == 200
        data = _body(response)
        items = cast(list[dict[str, object]], data["items"])
        assert data["total"] == 1
        assert items[0]["name"] == "Mine"


class TestGetWebhookEndpoint:
    """GET /api/v1/webhooks/{id}."""

    async def test_get_own(self, client: AsyncClient) -> None:
        token = await _register(client, "whgt1", "whgt1@example.com")
        created = _body(
            await client.post(
                "/api/v1/webhooks", json=_payload(), headers=_headers(token)
            )
        )

        response = await client.get(
            f"/api/v1/webhooks/{created['id']}", headers=_headers(token)
        )

        assert response.status_code == 200
        assert _body(response)["id"] == created["id"]

    async def test_get_missing_returns_404(self, client: AsyncClient) -> None:
        token = await _register(client, "whgt2", "whgt2@example.com")
        response = await client.get(
            "/api/v1/webhooks/00000000-0000-0000-0000-000000000001",
            headers=_headers(token),
        )
        assert response.status_code == 404

    async def test_cannot_get_another_users_webhook(
        self, client: AsyncClient
    ) -> None:
        token_a = await _register(client, "whgt3", "whgt3@example.com")
        token_b = await _register(client, "whgt4", "whgt4@example.com")
        created = _body(
            await client.post(
                "/api/v1/webhooks", json=_payload(), headers=_headers(token_a)
            )
        )

        response = await client.get(
            f"/api/v1/webhooks/{created['id']}", headers=_headers(token_b)
        )

        assert response.status_code == 404


class TestUpdateWebhookEndpoint:
    """PATCH /api/v1/webhooks/{id}."""

    async def test_update_success(self, client: AsyncClient) -> None:
        token = await _register(client, "whup1", "whup1@example.com")
        created = _body(
            await client.post(
                "/api/v1/webhooks", json=_payload(), headers=_headers(token)
            )
        )

        response = await client.patch(
            f"/api/v1/webhooks/{created['id']}",
            json={"name": "Renamed", "is_active": False},
            headers=_headers(token),
        )

        assert response.status_code == 200
        data = _body(response)
        assert data["name"] == "Renamed"
        assert data["is_active"] is False
        assert data["url"] == "http://127.0.0.1:1/hook"

    async def test_update_missing_returns_404(self, client: AsyncClient) -> None:
        token = await _register(client, "whup2", "whup2@example.com")
        response = await client.patch(
            "/api/v1/webhooks/00000000-0000-0000-0000-000000000001",
            json={"name": "Renamed"},
            headers=_headers(token),
        )
        assert response.status_code == 404

    async def test_cannot_update_another_users_webhook(
        self, client: AsyncClient
    ) -> None:
        token_a = await _register(client, "whup3", "whup3@example.com")
        token_b = await _register(client, "whup4", "whup4@example.com")
        created = _body(
            await client.post(
                "/api/v1/webhooks", json=_payload(), headers=_headers(token_a)
            )
        )

        response = await client.patch(
            f"/api/v1/webhooks/{created['id']}",
            json={"name": "Hijacked"},
            headers=_headers(token_b),
        )

        assert response.status_code == 404

    async def test_update_without_fields_returns_422(
        self, client: AsyncClient
    ) -> None:
        token = await _register(client, "whup5", "whup5@example.com")
        created = _body(
            await client.post(
                "/api/v1/webhooks", json=_payload(), headers=_headers(token)
            )
        )

        response = await client.patch(
            f"/api/v1/webhooks/{created['id']}",
            json={},
            headers=_headers(token),
        )

        assert response.status_code == 422


class TestDeleteWebhookEndpoint:
    """DELETE /api/v1/webhooks/{id}."""

    async def test_delete_success(self, client: AsyncClient) -> None:
        token = await _register(client, "whdl1", "whdl1@example.com")
        created = _body(
            await client.post(
                "/api/v1/webhooks", json=_payload(), headers=_headers(token)
            )
        )

        response = await client.delete(
            f"/api/v1/webhooks/{created['id']}", headers=_headers(token)
        )

        assert response.status_code == 204

        get_response = await client.get(
            f"/api/v1/webhooks/{created['id']}", headers=_headers(token)
        )
        assert get_response.status_code == 404

    async def test_delete_missing_returns_404(self, client: AsyncClient) -> None:
        token = await _register(client, "whdl2", "whdl2@example.com")
        response = await client.delete(
            "/api/v1/webhooks/00000000-0000-0000-0000-000000000001",
            headers=_headers(token),
        )
        assert response.status_code == 404

    async def test_cannot_delete_another_users_webhook(
        self, client: AsyncClient
    ) -> None:
        token_a = await _register(client, "whdl3", "whdl3@example.com")
        token_b = await _register(client, "whdl4", "whdl4@example.com")
        created = _body(
            await client.post(
                "/api/v1/webhooks", json=_payload(), headers=_headers(token_a)
            )
        )

        response = await client.delete(
            f"/api/v1/webhooks/{created['id']}", headers=_headers(token_b)
        )

        assert response.status_code == 404


class TestTestWebhookEndpoint:
    """POST /api/v1/webhooks/{id}/test."""

    async def test_test_ping_returns_outcome(self, client: AsyncClient) -> None:
        token = await _register(client, "whts1", "whts1@example.com")
        created = _body(
            await client.post(
                "/api/v1/webhooks", json=_payload(), headers=_headers(token)
            )
        )

        response = await client.post(
            f"/api/v1/webhooks/{created['id']}/test", headers=_headers(token)
        )

        assert response.status_code == 200
        data = _body(response)
        assert data["event"] == "test.ping"
        # Target is unreachable: delivery must be recorded as failed.
        assert data["status"] == "failed"
        assert data["attempts"] == 1
        assert data["delivery_id"]

    async def test_test_ping_missing_returns_404(
        self, client: AsyncClient
    ) -> None:
        token = await _register(client, "whts2", "whts2@example.com")
        response = await client.post(
            "/api/v1/webhooks/00000000-0000-0000-0000-000000000001/test",
            headers=_headers(token),
        )
        assert response.status_code == 404
