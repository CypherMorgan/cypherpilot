"""Tests for Templates API endpoints.

Uses the full app with a real in-memory database. Users register via
the auth endpoint, and the returned JWT is used for template CRUD.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import cast

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """App fixture: runs lifespan and creates the test schema."""
    app = create_app()

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


def _payload(**overrides: str) -> dict[str, str]:
    base = {
        "name": "CI Log Failure",
        "description": "Common pipeline flake",
        "content": "ERROR: build failed at step 3",
        "source_type": "ci_log",
    }
    base.update(overrides)
    return base


class TestTemplatesAuth:
    """Auth-gating tests for the templates endpoints."""

    async def test_list_requires_auth(self, client):
        response = await client.get("/api/v1/templates")
        assert response.status_code == 401

    async def test_create_requires_auth(self, client):
        response = await client.post("/api/v1/templates", json=_payload())
        assert response.status_code == 401

    async def test_delete_requires_auth(self, client):
        response = await client.delete(
            "/api/v1/templates/00000000-0000-0000-0000-000000000001"
        )
        assert response.status_code == 401


class TestCreateTemplateEndpoint:
    """Tests for POST /api/v1/templates."""

    async def test_create_success(self, client):
        token = await _register(client, "creator1", "creator1@example.com")
        response = await client.post(
            "/api/v1/templates", json=_payload(), headers=_headers(token)
        )

        assert response.status_code == 201, response.text
        data = response.json()
        assert data["name"] == "CI Log Failure"
        assert data["content"] == "ERROR: build failed at step 3"
        assert data["source_type"] == "ci_log"
        assert data["id"]

    async def test_create_invalid_source_type(self, client):
        token = await _register(client, "creator2", "creator2@example.com")
        response = await client.post(
            "/api/v1/templates",
            json=_payload(source_type="bogus"),
            headers=_headers(token),
        )

        assert response.status_code == 422

    async def test_create_short_name_rejected(self, client):
        token = await _register(client, "creator3", "creator3@example.com")
        response = await client.post(
            "/api/v1/templates",
            json=_payload(name="x"),
            headers=_headers(token),
        )

        assert response.status_code == 422


class TestListTemplatesEndpoint:
    """Tests for GET /api/v1/templates."""

    async def test_list_empty(self, client):
        token = await _register(client, "lister1", "lister1@example.com")
        response = await client.get(
            "/api/v1/templates", headers=_headers(token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_own_templates_only(self, client):
        token_a = await _register(client, "lister2", "lister2@example.com")
        token_b = await _register(client, "lister3", "lister3@example.com")
        await client.post(
            "/api/v1/templates", json=_payload(), headers=_headers(token_a)
        )
        await client.post(
            "/api/v1/templates", json=_payload(name="Other"), headers=_headers(token_b)
        )

        response = await client.get(
            "/api/v1/templates", headers=_headers(token_a)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "CI Log Failure"


class TestGetTemplateEndpoint:
    """Tests for GET /api/v1/templates/{id}."""

    async def test_get_own_template(self, client):
        token = await _register(client, "getter1", "getter1@example.com")
        created = (
            await client.post(
                "/api/v1/templates", json=_payload(), headers=_headers(token)
            )
        ).json()

        response = await client.get(
            f"/api/v1/templates/{created['id']}", headers=_headers(token)
        )

        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    async def test_get_missing_returns_404(self, client):
        token = await _register(client, "getter2", "getter2@example.com")
        response = await client.get(
            "/api/v1/templates/00000000-0000-0000-0000-000000000001",
            headers=_headers(token),
        )
        assert response.status_code == 404

    async def test_cannot_get_another_users_template(self, client):
        token_a = await _register(client, "getter3", "getter3@example.com")
        token_b = await _register(client, "getter4", "getter4@example.com")
        created = (
            await client.post(
                "/api/v1/templates", json=_payload(), headers=_headers(token_a)
            )
        ).json()

        response = await client.get(
            f"/api/v1/templates/{created['id']}", headers=_headers(token_b)
        )

        assert response.status_code == 404


class TestUpdateTemplateEndpoint:
    """Tests for PATCH /api/v1/templates/{id}."""

    async def test_update_success(self, client):
        token = await _register(client, "updater1", "updater1@example.com")
        created = (
            await client.post(
                "/api/v1/templates", json=_payload(), headers=_headers(token)
            )
        ).json()

        response = await client.patch(
            f"/api/v1/templates/{created['id']}",
            json={"name": "Renamed"},
            headers=_headers(token),
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Renamed"
        assert data["content"] == "ERROR: build failed at step 3"

    async def test_update_missing_returns_404(self, client):
        token = await _register(client, "updater2", "updater2@example.com")
        response = await client.patch(
            "/api/v1/templates/00000000-0000-0000-0000-000000000001",
            json={"name": "Renamed"},
            headers=_headers(token),
        )
        assert response.status_code == 404

    async def test_cannot_update_another_users_template(self, client):
        token_a = await _register(client, "updater3", "updater3@example.com")
        token_b = await _register(client, "updater4", "updater4@example.com")
        created = (
            await client.post(
                "/api/v1/templates", json=_payload(), headers=_headers(token_a)
            )
        ).json()

        response = await client.patch(
            f"/api/v1/templates/{created['id']}",
            json={"name": "Hijacked"},
            headers=_headers(token_b),
        )

        assert response.status_code == 404


class TestDeleteTemplateEndpoint:
    """Tests for DELETE /api/v1/templates/{id}."""

    async def test_delete_success(self, client):
        token = await _register(client, "deleter1", "deleter1@example.com")
        created = (
            await client.post(
                "/api/v1/templates", json=_payload(), headers=_headers(token)
            )
        ).json()

        response = await client.delete(
            f"/api/v1/templates/{created['id']}", headers=_headers(token)
        )

        assert response.status_code == 204

        get_response = await client.get(
            f"/api/v1/templates/{created['id']}", headers=_headers(token)
        )
        assert get_response.status_code == 404

    async def test_delete_missing_returns_404(self, client):
        token = await _register(client, "deleter2", "deleter2@example.com")
        response = await client.delete(
            "/api/v1/templates/00000000-0000-0000-0000-000000000001",
            headers=_headers(token),
        )
        assert response.status_code == 404
