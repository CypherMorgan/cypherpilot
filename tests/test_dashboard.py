"""Tests for the dashboard & usage analytics endpoint.

Users register via the auth endpoint; sessions are seeded directly in
the database so the aggregate statistics are deterministic.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.domain.models import AnalysisStatus, AnalysisType
from app.infrastructure.models.analysis_session import AnalysisSession
from app.main import create_app

STATS_URL = "/api/v1/dashboard/stats"


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
    *,
    analysis_type: AnalysisType,
    status: AnalysisStatus,
    title: str,
    created_at: datetime,
    tokens: int = 0,
    latency_ms: int = 0,
    error_message: str | None = None,
) -> uuid.UUID:
    """Insert an AnalysisSession owned by ``user_id`` with explicit fields."""
    manager = app.state.db_manager
    session_id = uuid.uuid4()
    async with manager.session() as db:
        db.add(
            AnalysisSession(
                id=session_id,
                user_id=user_id,
                title=title,
                analysis_type=analysis_type,
                status=status,
                input_source_type="plain_text",
                input_content="Sample input.",
                output_format="json",
                total_tokens=tokens,
                latency_ms=latency_ms,
                error_message=error_message,
                created_at=created_at,
            )
        )
        await db.commit()
    return session_id


class TestDashboardStatsEndpoint:
    """Tests for GET /api/v1/dashboard/stats."""

    async def test_stats_requires_auth(self, client) -> None:
        """Unauthenticated requests should return 401."""
        response = await client.get(STATS_URL)
        assert response.status_code == 401

    async def test_empty_stats_for_fresh_user(self, client) -> None:
        """A user with no sessions gets zeroed buckets and a 14-day series."""
        token, _ = await _register(client, "dash1", "dash1@example.com")

        response = await client.get(STATS_URL, headers=_headers(token))
        assert response.status_code == 200, response.text
        data = response.json()["data"]

        assert data["total_sessions"] == 0
        assert all(value == 0 for value in data["sessions_by_type"].values())
        assert all(value == 0 for value in data["sessions_by_status"].values())
        assert data["sessions_by_type"] == {
            "requirement-analysis": 0,
            "api-test-generation": 0,
            "failure-analysis": 0,
        }
        assert data["success_rate"] == 0.0
        assert data["total_tokens"] == 0
        assert data["total_latency_ms"] == 0
        assert data["avg_latency_ms"] == 0.0
        assert data["recent_failures"] == []
        assert len(data["usage_over_time"]) == 14
        assert all(point["sessions"] == 0 for point in data["usage_over_time"])

    async def test_stats_reflect_seeded_sessions(self, client, app) -> None:
        """Buckets, aggregates, and derived metrics match seeded rows."""
        token, user_id = await _register(client, "dash2", "dash2@example.com")
        now = datetime.now(UTC)

        await _seed_session(
            app, user_id,
            analysis_type=AnalysisType.REQUIREMENT_ANALYSIS,
            status=AnalysisStatus.COMPLETED,
            title="RA-1", tokens=100, latency_ms=500, created_at=now,
        )
        await _seed_session(
            app, user_id,
            analysis_type=AnalysisType.REQUIREMENT_ANALYSIS,
            status=AnalysisStatus.FAILED,
            title="RA-2", tokens=50, latency_ms=250, created_at=now,
            error_message="Provider timeout",
        )
        await _seed_session(
            app, user_id,
            analysis_type=AnalysisType.API_TEST_GENERATION,
            status=AnalysisStatus.COMPLETED,
            title="API-1", tokens=200, latency_ms=1000, created_at=now,
        )
        await _seed_session(
            app, user_id,
            analysis_type=AnalysisType.FAILURE_ANALYSIS,
            status=AnalysisStatus.PENDING,
            title="FA-1", created_at=now,
        )
        # Outside the 14-day window: counts toward totals but not usage series.
        await _seed_session(
            app, user_id,
            analysis_type=AnalysisType.REQUIREMENT_ANALYSIS,
            status=AnalysisStatus.COMPLETED,
            title="RA-old", tokens=10, latency_ms=100,
            created_at=now - timedelta(days=20),
        )

        response = await client.get(STATS_URL, headers=_headers(token))
        assert response.status_code == 200, response.text
        data = response.json()["data"]

        assert data["total_sessions"] == 5
        assert data["sessions_by_type"] == {
            "requirement-analysis": 3,
            "api-test-generation": 1,
            "failure-analysis": 1,
        }
        assert data["sessions_by_status"] == {
            "pending": 1,
            "processing": 0,
            "completed": 3,
            "failed": 1,
        }
        assert data["success_rate"] == 0.75
        assert data["total_tokens"] == 360
        assert data["total_latency_ms"] == 1850
        assert data["avg_latency_ms"] == 370.0

        # Only the 4 sessions within the window appear in the usage series.
        assert len(data["usage_over_time"]) == 14
        assert sum(point["sessions"] for point in data["usage_over_time"]) == 4

        assert len(data["recent_failures"]) == 1
        failure = data["recent_failures"][0]
        assert failure["title"] == "RA-2"
        assert failure["analysis_type"] == "requirement-analysis"
        assert failure["error_message"] == "Provider timeout"

    async def test_recent_failures_limited_and_newest_first(self, client, app) -> None:
        """Only the 5 newest failures are returned, ordered by recency."""
        token, user_id = await _register(client, "dash3", "dash3@example.com")
        now = datetime.now(UTC)

        for index in range(7):
            await _seed_session(
                app, user_id,
                analysis_type=AnalysisType.FAILURE_ANALYSIS,
                status=AnalysisStatus.FAILED,
                title=f"Fail-{index}",
                error_message=f"err-{index}",
                created_at=now - timedelta(hours=index),
            )

        response = await client.get(STATS_URL, headers=_headers(token))
        assert response.status_code == 200, response.text
        failures = response.json()["data"]["recent_failures"]

        assert len(failures) == 5
        assert [failure["title"] for failure in failures] == [
            "Fail-0",
            "Fail-1",
            "Fail-2",
            "Fail-3",
            "Fail-4",
        ]

    async def test_stats_are_user_scoped(self, client, app) -> None:
        """One user's sessions never leak into another user's stats."""
        token_a, user_a = await _register(client, "dash4", "dash4@example.com")
        token_b, user_b = await _register(client, "dash5", "dash5@example.com")
        now = datetime.now(UTC)

        await _seed_session(
            app, user_a,
            analysis_type=AnalysisType.REQUIREMENT_ANALYSIS,
            status=AnalysisStatus.COMPLETED,
            title="A-session", created_at=now,
        )
        await _seed_session(
            app, user_b,
            analysis_type=AnalysisType.API_TEST_GENERATION,
            status=AnalysisStatus.COMPLETED,
            title="B-session", tokens=999, latency_ms=999, created_at=now,
        )

        response_a = await client.get(STATS_URL, headers=_headers(token_a))
        assert response_a.status_code == 200, response_a.text
        data_a = response_a.json()["data"]
        assert data_a["total_sessions"] == 1
        assert data_a["sessions_by_type"]["requirement-analysis"] == 1
        assert data_a["sessions_by_type"]["api-test-generation"] == 0
        assert data_a["total_tokens"] == 0

        response_b = await client.get(STATS_URL, headers=_headers(token_b))
        assert response_b.status_code == 200, response_b.text
        data_b = response_b.json()["data"]
        assert data_b["total_sessions"] == 1
        assert data_b["sessions_by_type"]["api-test-generation"] == 1
        assert data_b["total_tokens"] == 999
