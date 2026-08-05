"""Dashboard & usage analytics API routes.

Provides aggregate statistics over the authenticated user's analysis
sessions: totals, counts by module and status, success rate, token and
latency aggregates, recent failures, and usage over the last 14 days.

All queries are user-scoped and DB-agnostic (no dialect-specific SQL);
the 14-day usage series is bucketed in Python from stored timestamps.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AnalysisStatus, AnalysisType, ResponseMeta
from app.infrastructure.database import get_db
from app.infrastructure.models.analysis_session import AnalysisSession
from app.modules.auth.middleware import get_current_user
from app.modules.auth.models import User

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)

RECENT_FAILURES_LIMIT = 5
USAGE_WINDOW_DAYS = 14


# ── Response models ──────────────────────────────────────────────


class RecentFailureItem(BaseModel):
    """A recently failed analysis session (truncated for the dashboard)."""

    session_id: uuid.UUID
    title: str | None = None
    analysis_type: AnalysisType
    error_message: str | None = None
    created_at: datetime


class UsagePoint(BaseModel):
    """Session count for a single day."""

    date: date
    sessions: int = 0


class DashboardStats(BaseModel):
    """Aggregate usage statistics for one user."""

    total_sessions: int = 0
    sessions_by_type: dict[str, int] = Field(default_factory=dict)
    sessions_by_status: dict[str, int] = Field(default_factory=dict)
    success_rate: float = 0.0
    total_tokens: int = 0
    total_latency_ms: int = 0
    avg_latency_ms: float = 0.0
    recent_failures: list[RecentFailureItem] = Field(default_factory=list)
    usage_over_time: list[UsagePoint] = Field(default_factory=list)


# ── Stats collection ─────────────────────────────────────────────


def _empty_buckets() -> tuple[dict[str, int], dict[str, int]]:
    """Buckets with every known type/status present at zero.

    Keeps the payload shape stable for consumers even when the user has
    no sessions in a given bucket.
    """
    types = {t.value: 0 for t in AnalysisType}
    statuses = {s.value: 0 for s in AnalysisStatus}
    return types, statuses


def _as_utc(value: datetime) -> datetime:
    """Normalize a possibly-naive timestamp to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


async def collect_stats(db: AsyncSession, user_id: uuid.UUID) -> DashboardStats:
    """Compute dashboard stats for ``user_id``."""
    types_buckets, status_buckets = _empty_buckets()

    # ── Counts by analysis type ────────────────────────────────
    by_type = await db.execute(
        select(AnalysisSession.analysis_type, func.count())
        .where(AnalysisSession.user_id == user_id)
        .group_by(AnalysisSession.analysis_type)
    )
    total_sessions = 0
    for analysis_type, count in by_type.all():
        types_buckets[analysis_type.value] = count
        total_sessions += count

    # ── Counts by status ───────────────────────────────────────
    by_status = await db.execute(
        select(AnalysisSession.status, func.count())
        .where(AnalysisSession.user_id == user_id)
        .group_by(AnalysisSession.status)
    )
    completed = 0
    failed = 0
    for status_value, count in by_status.all():
        status_buckets[status_value.value] = count
        if status_value == AnalysisStatus.COMPLETED:
            completed = count
        elif status_value == AnalysisStatus.FAILED:
            failed = count

    # ── Token / latency aggregates ─────────────────────────────
    aggregates = (
        await db.execute(
            select(
                func.coalesce(func.sum(AnalysisSession.total_tokens), 0),
                func.coalesce(func.sum(AnalysisSession.latency_ms), 0),
                func.count(AnalysisSession.id),
            ).where(AnalysisSession.user_id == user_id)
        )
    ).one()
    total_tokens = int(aggregates[0])
    total_latency_ms = int(aggregates[1])
    session_count = int(aggregates[2])

    # ── Recent failures ────────────────────────────────────────
    failures_result = await db.execute(
        select(
            AnalysisSession.id,
            AnalysisSession.title,
            AnalysisSession.analysis_type,
            AnalysisSession.error_message,
            AnalysisSession.created_at,
        )
        .where(
            AnalysisSession.user_id == user_id,
            AnalysisSession.status == AnalysisStatus.FAILED,
        )
        .order_by(AnalysisSession.created_at.desc())
        .limit(RECENT_FAILURES_LIMIT)
    )
    recent_failures = [
        RecentFailureItem(
            session_id=row[0],
            title=row[1],
            analysis_type=row[2],
            error_message=row[3],
            created_at=row[4],
        )
        for row in failures_result.all()
    ]

    # ── Usage over the last 14 days (bucketed in Python) ───────
    now = datetime.now(UTC)
    today = now.date()
    start_of_window = today - timedelta(days=USAGE_WINDOW_DAYS - 1)
    usage_rows = await db.execute(
        select(AnalysisSession.created_at).where(
            AnalysisSession.user_id == user_id
        )
    )
    day_counts: dict[date, int] = {}
    for (created_at,) in usage_rows.all():
        day = _as_utc(created_at).date()
        if start_of_window <= day <= today:
            day_counts[day] = day_counts.get(day, 0) + 1
    usage_over_time = [
        UsagePoint(
            date=start_of_window + timedelta(days=offset),
            sessions=day_counts.get(start_of_window + timedelta(days=offset), 0),
        )
        for offset in range(USAGE_WINDOW_DAYS)
    ]

    # ── Derived metrics ────────────────────────────────────────
    success_rate = 0.0
    terminal = completed + failed
    if terminal > 0:
        success_rate = round(completed / terminal, 3)

    avg_latency_ms = 0.0
    if session_count > 0:
        avg_latency_ms = round(total_latency_ms / session_count, 1)

    return DashboardStats(
        total_sessions=total_sessions,
        sessions_by_type=types_buckets,
        sessions_by_status=status_buckets,
        success_rate=success_rate,
        total_tokens=total_tokens,
        total_latency_ms=total_latency_ms,
        avg_latency_ms=avg_latency_ms,
        recent_failures=recent_failures,
        usage_over_time=usage_over_time,
    )


# ── Routes ───────────────────────────────────────────────────────


@router.get(
    "/stats",
    response_model=dict,
    summary="Get dashboard stats",
    description=(
        "Aggregate usage analytics for the authenticated user: session "
        "counts by module and status, success rate, token/latency totals, "
        "recent failures, and a 14-day usage series."
    ),
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    user: User = Depends(get_current_user),  # noqa: B008
    http_request: Request = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Return personal usage analytics for the current user."""
    stats = await collect_stats(db, user_id=user.id)

    response = {
        "data": stats.model_dump(mode="json"),
        "meta": ResponseMeta(
            request_id=getattr(http_request.state, "request_id", "") if http_request else "",
        ).model_dump(),
    }
    return response
