"""API rate limiting middleware.

Enforces per-user and per-team sliding-window rate limits on API
requests (plus a per-IP limit for anonymous callers). Identity is
resolved from the JWT access token when present; team membership is
looked up through the database and cached for the window duration so
the hot path stays cheap.

On violation the middleware short-circuits with ``429 Too Many
Requests`` using the standard CypherPilot error envelope and sets
``Retry-After`` plus ``X-RateLimit-*`` headers on every response.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime

import jwt as pyjwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp
from structlog import get_logger

from app.config import RateLimitConfig
from app.infrastructure.rate_limiter import (
    RateLimitStatus,
    SlidingWindowRateLimiter,
)
from app.modules.auth.config import AuthConfig
from app.modules.teams.repository import TeamMemberRepository

_logger = get_logger(__name__)

# Paths that must never be rate limited: API docs, schema, health probes.
_EXEMPT_PATHS = frozenset(
    {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/v1/health",
    }
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit API requests per user, per team, and per IP."""

    def __init__(
        self,
        app: ASGIApp,
        limiter: SlidingWindowRateLimiter,
        config: RateLimitConfig,
    ) -> None:
        super().__init__(app)
        self._limiter = limiter
        self._cfg = config
        self._auth_config: AuthConfig | None = None  # bound from app.state lazily
        # user_id -> (cached_at_monotonic, [team_id, ...])
        self._team_cache: dict[str, tuple[float, list[str]]] = {}
        self._cache_lock = asyncio.Lock()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if not self._cfg.enabled:
            return await call_next(request)

        # CORS preflight requests carry no user identity — pass through.
        if request.method == "OPTIONS" or request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        user_id, identity = await self._resolve_identity(request)

        statuses: list[RateLimitStatus] = []
        if user_id is not None:
            statuses.append(
                await self._limiter.check(
                    f"user:{user_id}",
                    self._cfg.max_requests_per_user,
                    self._cfg.window_seconds,
                )
            )
            for team_id in await self._get_team_ids(request, user_id):
                statuses.append(
                    await self._limiter.check(
                        f"team:{team_id}",
                        self._cfg.max_requests_per_team,
                        self._cfg.window_seconds,
                    )
                )
        else:
            statuses.append(
                await self._limiter.check(
                    f"ip:{identity}",
                    self._cfg.max_requests_anonymous,
                    self._cfg.window_seconds,
                )
            )

        limited = [s for s in statuses if s.limited]
        if limited:
            retry_after = max(s.reset_after for s in limited)
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": (
                            "Rate limit exceeded. Please slow down and "
                            "retry in a few seconds."
                        ),
                        "detail": {"retry_after": retry_after},
                    },
                    "meta": {
                        "request_id": getattr(request.state, "request_id", ""),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                },
                headers={
                    "Retry-After": str(retry_after),
                    **_rate_limit_headers(statuses),
                },
            )

        response = await call_next(request)
        for name, value in _rate_limit_headers(statuses).items():
            response.headers[name] = value
        return response

    # ── Identity resolution ──────────────────────────────────────

    async def _resolve_identity(
        self, request: Request
    ) -> tuple[str | None, str]:
        """Return ``(user_id, identity)``.

        ``user_id`` is set when a valid Bearer token is present; the
        returned identity is then the user id. Anonymous callers get
        ``(None, client_ip)`` and fall back to the per-IP limit.
        """
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
            if token:
                try:
                    auth_config = self._get_auth_config(request)
                    payload = pyjwt.decode(
                        token,
                        auth_config.secret_key,
                        algorithms=[auth_config.token_algorithm],
                    )
                    sub = payload.get("sub")
                    if sub:
                        uuid.UUID(str(sub))  # reject malformed subjects
                        return str(sub), str(sub)
                except Exception:
                    # Invalid/expired token — treat as anonymous rather
                    # than letting one bad token bypass the limiter.
                    _logger.debug("rate limit: invalid token, falling back to IP")
        return None, self._client_ip(request)

    def _get_auth_config(self, request: Request) -> AuthConfig:
        """Return the app's AuthConfig, caching it on first use."""
        if self._auth_config is None:
            auth_config = getattr(request.app.state, "auth_config", None)
            if auth_config is None:
                raise RuntimeError("auth_config is not initialised")
            self._auth_config = auth_config
        return self._auth_config

    def _client_ip(self, request: Request) -> str:
        if self._cfg.trust_forwarded_for:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
        if request.client is not None:
            return request.client.host
        return "unknown"

    # ── Team membership lookup (cached) ──────────────────────────

    async def _get_team_ids(self, request: Request, user_id: str) -> list[str]:
        """Return the team ids for ``user_id``, cached for one window."""
        now = time.monotonic()
        cached = self._team_cache.get(user_id)
        if cached is not None and now - cached[0] < self._cfg.window_seconds:
            return cached[1]

        team_ids: list[str] = []
        db_manager = getattr(request.app.state, "db_manager", None)
        if db_manager is not None:
            try:
                async with db_manager.session() as session:
                    repo = TeamMemberRepository(session)
                    ids = await repo.get_team_ids_for_user(uuid.UUID(user_id))
                    team_ids = [str(i) for i in ids]
            except Exception:
                # A lookup failure must not block traffic — fall back to
                # user-only limiting for this window.
                _logger.warning(
                    "rate limit: team lookup failed", exc_info=True
                )

        async with self._cache_lock:
            self._team_cache[user_id] = (now, team_ids)
        return team_ids


def _rate_limit_headers(
    statuses: list[RateLimitStatus],
) -> dict[str, str]:
    """Build X-RateLimit-* headers from the most restrictive bucket."""
    worst = min(statuses, key=lambda s: s.remaining)
    return {
        "X-RateLimit-Limit": str(worst.limit),
        "X-RateLimit-Remaining": str(worst.remaining),
        "X-RateLimit-Reset": str(worst.reset_after),
    }
