"""Integration tests for the rate-limiting middleware.

Builds the full app with tiny rate limits (via environment variables)
so limits can be exhausted in a handful of requests, then exercises
per-user, per-IP, and per-team buckets plus exempt paths.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import create_app


async def _make_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    per_user: int,
    per_team: int,
    anonymous: int,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an app + client with the given (tiny) rate limits."""
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS_PER_USER", str(per_user))
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS_PER_TEAM", str(per_team))
    monkeypatch.setenv("RATE_LIMIT_MAX_REQUESTS_ANONYMOUS", str(anonymous))
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    app = create_app()
    async with LifespanManager(app):
        db_manager = getattr(app.state, "db_manager", None)
        if db_manager is not None:
            await db_manager.create_all()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.fixture
async def user_limited_client(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[AsyncClient, None]:
    """User limit 4, team limit 3, anonymous limit 2."""
    async for c in _make_client(
        monkeypatch, per_user=4, per_team=3, anonymous=2
    ):
        yield c


@pytest.fixture
async def team_limited_client(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[AsyncClient, None]:
    """Team limit tight (3) while the user limit is loose (10)."""
    async for c in _make_client(
        monkeypatch, per_user=10, per_team=3, anonymous=10
    ):
        yield c


@pytest.fixture
async def disabled_client(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[AsyncClient, None]:
    """Rate limiting switched off entirely."""
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    app = create_app()
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


async def _register(client: AsyncClient, username: str, email: str) -> str:
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
    return str(response.json()["access_token"])


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestPerUserLimit:
    async def test_blocks_after_user_limit(
        self, user_limited_client: AsyncGenerator[AsyncClient, None]
    ) -> None:
        token = await _register(
            user_limited_client, "rluser1", "rluser1@example.com"
        )
        headers = _headers(token)

        codes = []
        for _ in range(4):
            response = await user_limited_client.get(
                "/api/v1/templates", headers=headers
            )
            codes.append(response.status_code)
        assert codes == [200, 200, 200, 200]

        blocked = await user_limited_client.get(
            "/api/v1/templates", headers=headers
        )
        assert blocked.status_code == 429
        body = blocked.json()
        assert body["error"]["code"] == "RATE_LIMITED"
        assert "retry_after" in body["error"]["detail"]
        assert int(blocked.headers["Retry-After"]) >= 1
        assert blocked.headers["X-RateLimit-Limit"] == "4"
        assert blocked.headers["X-RateLimit-Remaining"] == "0"

    async def test_success_responses_carry_headers(
        self, user_limited_client: AsyncGenerator[AsyncClient, None]
    ) -> None:
        token = await _register(
            user_limited_client, "rluser2", "rluser2@example.com"
        )
        response = await user_limited_client.get(
            "/api/v1/templates", headers=_headers(token)
        )
        assert response.status_code == 200
        assert response.headers["X-RateLimit-Limit"] == "4"
        assert response.headers["X-RateLimit-Remaining"] == "3"
        assert int(response.headers["X-RateLimit-Reset"]) >= 1

    async def test_buckets_are_per_user(
        self, user_limited_client: AsyncGenerator[AsyncClient, None]
    ) -> None:
        token_a = await _register(
            user_limited_client, "rluser3", "rluser3@example.com"
        )
        token_b = await _register(
            user_limited_client, "rluser4", "rluser4@example.com"
        )
        # User A exhausts their own limit...
        for _ in range(4):
            await user_limited_client.get(
                "/api/v1/templates", headers=_headers(token_a)
            )
        blocked = await user_limited_client.get(
            "/api/v1/templates", headers=_headers(token_a)
        )
        assert blocked.status_code == 429
        # ...but user B is unaffected.
        response = await user_limited_client.get(
            "/api/v1/templates", headers=_headers(token_b)
        )
        assert response.status_code == 200


class TestAnonymousLimit:
    async def test_anonymous_blocked_by_ip(
        self, user_limited_client: AsyncGenerator[AsyncClient, None]
    ) -> None:
        # No token: the requests reach the router (401) but still count.
        first = await user_limited_client.get("/api/v1/templates")
        second = await user_limited_client.get("/api/v1/templates")
        assert first.status_code == 401
        assert second.status_code == 401
        blocked = await user_limited_client.get("/api/v1/templates")
        assert blocked.status_code == 429
        body = blocked.json()
        assert body["error"]["code"] == "RATE_LIMITED"
        assert blocked.headers["X-RateLimit-Limit"] == "2"

    async def test_invalid_token_counts_as_anonymous(
        self, user_limited_client: AsyncGenerator[AsyncClient, None]
    ) -> None:
        headers = _headers("not-a-valid-jwt")
        for _ in range(2):
            response = await user_limited_client.get(
                "/api/v1/templates", headers=headers
            )
            assert response.status_code == 401
        blocked = await user_limited_client.get(
            "/api/v1/templates", headers=headers
        )
        assert blocked.status_code == 429


class TestTeamLimit:
    async def test_team_bucket_limits_members(
        self, team_limited_client: AsyncGenerator[AsyncClient, None]
    ) -> None:
        token = await _register(
            team_limited_client, "rlteam1", "rlteam1@example.com"
        )
        headers = _headers(token)

        # Seed a team membership directly in the database.
        app = team_limited_client._transport.app
        db_manager = app.state.db_manager
        async with db_manager.session() as session:
            from sqlalchemy import select

            from app.modules.auth.models import User
            from app.modules.teams.models import Team, TeamMember

            user = (
                await session.execute(
                    select(User).where(User.username == "rlteam1")
                )
            ).scalar_one()
            team = Team(name="RL Team", description="", created_by=user.id)
            session.add(team)
            await session.flush()
            session.add(TeamMember(team_id=team.id, user_id=user.id))
            await session.commit()

        codes = []
        for _ in range(3):
            response = await team_limited_client.get(
                "/api/v1/templates", headers=headers
            )
            codes.append(response.status_code)
        assert codes == [200, 200, 200]

        blocked = await team_limited_client.get(
            "/api/v1/templates", headers=headers
        )
        assert blocked.status_code == 429
        # The tight team bucket (3) is what tripped, not the user bucket (10).
        assert blocked.headers["X-RateLimit-Limit"] == "3"
        assert int(blocked.headers["Retry-After"]) >= 1


class TestExemptPaths:
    async def test_health_never_limited(
        self, user_limited_client: AsyncGenerator[AsyncClient, None]
    ) -> None:
        for _ in range(10):
            response = await user_limited_client.get("/api/v1/health")
            assert response.status_code == 200

    async def test_docs_never_limited(
        self, user_limited_client: AsyncGenerator[AsyncClient, None]
    ) -> None:
        response = await user_limited_client.get("/docs")
        assert response.status_code == 200
        response = await user_limited_client.get("/openapi.json")
        assert response.status_code == 200

    async def test_options_preflight_never_limited(
        self, user_limited_client: AsyncGenerator[AsyncClient, None]
    ) -> None:
        response = await user_limited_client.options("/api/v1/templates")
        # Either CORS answers the preflight or the router returns 405 —
        # in no case may it be rate limited.
        assert response.status_code in (200, 405)


class TestDisabledConfig:
    async def test_no_limiting_when_disabled(
        self, disabled_client: AsyncGenerator[AsyncClient, None]
    ) -> None:
        for _ in range(10):
            response = await disabled_client.get("/api/v1/templates")
            assert response.status_code == 401  # never 429
