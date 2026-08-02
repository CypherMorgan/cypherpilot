"""Tests for Failure Analysis session export endpoints.

Users register via the auth endpoint; sessions are seeded directly in
the database so the export responses are deterministic.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import cast

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
    output_data: dict,
) -> uuid.UUID:
    """Insert a completed FailureAnalysis session owned by user_id."""
    manager = app.state.db_manager
    session_id = uuid.uuid4()
    async with manager.session() as db:
        db.add(
            AnalysisSession(
                id=session_id,
                user_id=user_id,
                title="Export test",
                analysis_type=AnalysisType.FAILURE_ANALYSIS,
                status=AnalysisStatus.COMPLETED,
                input_source_type="plain_text",
                input_content="Sample failure output.",
                output_data=output_data,
                output_format="json",
            )
        )
        await db.commit()
    return session_id


def _output_data() -> dict:
    """Minimal valid FailureAnalysisResult output data."""
    return {
        "input_summary": "Sample failure.",
        "summary": "A test summary.",
        "root_causes": [
            {
                "id": "RC-001",
                "title": "Token mismatch",
                "description": "Old JWT format expected.",
                "category": "assertion-error",
                "severity": "high",
                "failing_file": "tests/test_auth.py",
                "failing_line": 42,
                "stack_trace": [],
                "error_message": "AssertionError",
            }
        ],
        "suggested_fixes": [
            {
                "id": "FIX-001",
                "root_cause_id": "RC-001",
                "description": "Update assertions.",
                "priority": "high",
                "effort_estimate": "30 minutes",
                "code_example": "",
                "related_files": ["tests/test_auth.py"],
            }
        ],
        "affected_components": [],
        "test_failures": [
            {
                "id": "TF-001",
                "test_name": "tests/test_auth.py::test_login",
                "test_file": "tests/test_auth.py",
                "error_message": "AssertionError",
                "duration_seconds": 1.2,
                "retry_count": 0,
            }
        ],
        "environment_details": ["Python 3.12"],
        "recommendations": ["Run the suite."],
        "related_tests": ["tests/test_session.py"],
    }


class TestExportSessionEndpoint:
    """Tests for GET /api/v1/failures/sessions/{id}/export."""

    async def test_export_requires_auth(self, client):
        """Unauthenticated export should return 401."""
        response = await client.get(
            f"/api/v1/failures/sessions/{uuid.uuid4()}/export"
        )
        assert response.status_code == 401

    async def test_export_markdown(self, client, app, sample_analysis_result):
        """Markdown export should return an attachment document."""
        token, user_id = await _register(client, "exp1", "exp1@example.com")
        session_id = await _seed_session(
            app, user_id, sample_analysis_result.model_dump(mode="json")
        )

        response = await client.get(
            f"/api/v1/failures/sessions/{session_id}/export?format=markdown",
            headers=_headers(token),
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/markdown")
        assert f"attachment; filename=\"failure-analysis-{session_id}.md\"" in response.headers["content-disposition"]
        assert "# Automation Failure Analysis Report" in response.text

    async def test_export_json(self, client, app, sample_analysis_result):
        """JSON export should return the full structured result."""
        token, user_id = await _register(client, "exp2", "exp2@example.com")
        session_id = await _seed_session(
            app, user_id, sample_analysis_result.model_dump(mode="json")
        )

        response = await client.get(
            f"/api/v1/failures/sessions/{session_id}/export?format=json",
            headers=_headers(token),
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert "failure-analysis-" in response.headers["content-disposition"]
        assert ".json" in response.headers["content-disposition"]
        body = response.json()
        assert body["input_summary"] == sample_analysis_result.input_summary

    async def test_export_csv(self, client, app, sample_analysis_result):
        """CSV export should return flattened rows with a BOM."""
        token, user_id = await _register(client, "exp3", "exp3@example.com")
        session_id = await _seed_session(
            app, user_id, sample_analysis_result.model_dump(mode="json")
        )

        response = await client.get(
            f"/api/v1/failures/sessions/{session_id}/export?format=csv",
            headers=_headers(token),
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert ".csv" in response.headers["content-disposition"]
        assert response.content.startswith(b"\xef\xbb\xbf")
        assert b"section,id,title,description" in response.content

    async def test_export_default_format(self, client, app, sample_analysis_result):
        """Default format should be markdown when omitted."""
        token, user_id = await _register(client, "exp4", "exp4@example.com")
        session_id = await _seed_session(
            app, user_id, sample_analysis_result.model_dump(mode="json")
        )

        response = await client.get(
            f"/api/v1/failures/sessions/{session_id}/export",
            headers=_headers(token),
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/markdown")

    async def test_export_unsupported_format(self, client, app, sample_analysis_result):
        """Unsupported format should return 422."""
        token, user_id = await _register(client, "exp5", "exp5@example.com")
        session_id = await _seed_session(
            app, user_id, sample_analysis_result.model_dump(mode="json")
        )

        response = await client.get(
            f"/api/v1/failures/sessions/{session_id}/export?format=pdf",
            headers=_headers(token),
        )
        assert response.status_code == 422

    async def test_export_unknown_session(self, client):
        """Unknown session should return 404."""
        token, _ = await _register(client, "exp6", "exp6@example.com")
        response = await client.get(
            f"/api/v1/failures/sessions/{uuid.uuid4()}/export",
            headers=_headers(token),
        )
        assert response.status_code == 404

    async def test_export_another_users_session(self, client, app, sample_analysis_result):
        """A session owned by another user should be indistinguishable (404)."""
        token_a, user_a = await _register(client, "exp7", "exp7@example.com")
        token_b, _ = await _register(client, "exp8", "exp8@example.com")
        session_id = await _seed_session(
            app, user_a, sample_analysis_result.model_dump(mode="json")
        )

        # Owner can export their own session.
        owner = await client.get(
            f"/api/v1/failures/sessions/{session_id}/export",
            headers=_headers(token_a),
        )
        assert owner.status_code == 200

        # Another user must not be able to read it.
        forbidden = await client.get(
            f"/api/v1/failures/sessions/{session_id}/export",
            headers=_headers(token_b),
        )
        assert forbidden.status_code == 404
