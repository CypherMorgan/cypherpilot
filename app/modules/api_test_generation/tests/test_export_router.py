"""Tests for API Test Generation session export endpoints.

Users register via the auth endpoint; sessions are seeded directly in
the database so the export responses are deterministic.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any, cast

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.domain.models import AnalysisStatus, AnalysisType
from app.infrastructure.models.analysis_session import AnalysisSession
from app.main import create_app


@pytest.fixture
async def app() -> AsyncGenerator[FastAPI, None]:
    """App fixture: runs lifespan and creates the test schema."""
    application = create_app()

    async with LifespanManager(application):
        db_manager = getattr(application.state, "db_manager", None)
        if db_manager is not None:
            await db_manager.create_all()
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Client fixture: ASGI transport over the test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _register(
    client: AsyncClient, username: str, email: str
) -> tuple[str, uuid.UUID]:
    """Register a user and return (access_token, user_id)."""
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
    body = response.json()
    return cast(str, body["access_token"]), uuid.UUID(body["user"]["id"])


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _seed_session(
    app: FastAPI,
    user_id: uuid.UUID,
    output_data: dict[str, Any],
) -> uuid.UUID:
    """Insert a completed API test generation session owned by user_id."""
    manager = app.state.db_manager
    session_id = uuid.uuid4()
    async with manager.session() as db:
        db.add(
            AnalysisSession(
                id=session_id,
                user_id=user_id,
                title="Export test",
                analysis_type=AnalysisType.API_TEST_GENERATION,
                status=AnalysisStatus.COMPLETED,
                input_source_type="spec",
                input_content="openapi: 3.0.0",
                output_data=output_data,
                output_format="json",
            )
        )
        await db.commit()
    return session_id


def _output_data() -> dict[str, Any]:
    """Stored session output data for a generated test suite."""
    return {
        "spec_title": "Pet Store API",
        "spec_version": "1.0.0",
        "endpoint_count": 2,
        "files": [
            {"filename": "test_pets.py", "content": "import pytest"},
            {"filename": "conftest.py", "content": "import asyncio"},
        ],
        "endpoints": [
            {"method": "get", "path": "/pets", "tests_generated": 2},
            {"method": "post", "path": "/pets", "tests_generated": 1},
        ],
        "zip_content": "UEsDBBQACAgIAAAAAAAAAAAAAAA=",
    }


class TestExportSessionEndpoint:
    """Tests for GET /api/v1/openapi/sessions/{id}/export."""

    async def test_export_requires_auth(self, client):
        """Unauthenticated export should return 401."""
        response = await client.get(
            f"/api/v1/openapi/sessions/{uuid.uuid4()}/export"
        )
        assert response.status_code == 401

    async def test_export_markdown(self, client, app):
        """Markdown export should return an attachment document."""
        token, user_id = await _register(client, "apiexp1", "apiexp1@example.com")
        session_id = await _seed_session(app, user_id, _output_data())

        response = await client.get(
            f"/api/v1/openapi/sessions/{session_id}/export?format=markdown",
            headers=_headers(token),
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/markdown")
        assert f"attachment; filename=\"api-test-generation-{session_id}.md\"" in response.headers["content-disposition"]
        assert "# Pet Store API" in response.text
        assert "## Endpoints" in response.text
        assert "## Generated Files" in response.text

    async def test_export_json(self, client, app):
        """JSON export should exclude the ZIP payload."""
        token, user_id = await _register(client, "apiexp2", "apiexp2@example.com")
        session_id = await _seed_session(app, user_id, _output_data())

        response = await client.get(
            f"/api/v1/openapi/sessions/{session_id}/export?format=json",
            headers=_headers(token),
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert ".json" in response.headers["content-disposition"]
        body = response.json()
        assert body["spec_title"] == "Pet Store API"
        assert "zip_content" not in body
        assert len(body["endpoints"]) == 2

    async def test_export_csv(self, client, app):
        """CSV export should return endpoint rows with a BOM."""
        token, user_id = await _register(client, "apiexp3", "apiexp3@example.com")
        session_id = await _seed_session(app, user_id, _output_data())

        response = await client.get(
            f"/api/v1/openapi/sessions/{session_id}/export?format=csv",
            headers=_headers(token),
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert ".csv" in response.headers["content-disposition"]
        assert response.content.startswith(b"\xef\xbb\xbf")
        assert b"method,path,tests_generated" in response.content
        assert b"get,/pets,2" in response.content

    async def test_export_unsupported_format(self, client, app):
        """Unsupported format should return 422."""
        token, user_id = await _register(client, "apiexp4", "apiexp4@example.com")
        session_id = await _seed_session(app, user_id, _output_data())

        response = await client.get(
            f"/api/v1/openapi/sessions/{session_id}/export?format=pdf",
            headers=_headers(token),
        )
        assert response.status_code == 422

    async def test_export_unknown_session(self, client):
        """Unknown session should return 404."""
        token, _ = await _register(client, "apiexp5", "apiexp5@example.com")
        response = await client.get(
            f"/api/v1/openapi/sessions/{uuid.uuid4()}/export",
            headers=_headers(token),
        )
        assert response.status_code == 404

    async def test_export_another_users_session(self, client, app):
        """A session owned by another user should be indistinguishable (404)."""
        token_a, user_a = await _register(client, "apiexp6", "apiexp6@example.com")
        token_b, _ = await _register(client, "apiexp7", "apiexp7@example.com")
        session_id = await _seed_session(app, user_a, _output_data())

        owner = await client.get(
            f"/api/v1/openapi/sessions/{session_id}/export",
            headers=_headers(token_a),
        )
        assert owner.status_code == 200

        forbidden = await client.get(
            f"/api/v1/openapi/sessions/{session_id}/export",
            headers=_headers(token_b),
        )
        assert forbidden.status_code == 404
