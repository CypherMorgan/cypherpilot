"""Session cleanup routes.

Provides an endpoint to purge expired analysis sessions based on
the configured retention policy.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.domain.models import ResponseMeta
from app.infrastructure.database import get_db
from app.infrastructure.models.analysis_session import AnalysisSession

router = APIRouter(
    prefix="/cleanup",
    tags=["Session Cleanup"],
)
_logger = get_logger(__name__)


@router.delete(
    "/expired",
    response_model=dict,
    summary="Delete expired sessions",
    description=(
        "Remove all analysis sessions older than the configured "
        "retention period. The retention period is set via the "
        "``RETENTION__RETENTION_DAYS`` environment variable (default 90)."
    ),
)
async def delete_expired_sessions(
    request: Request,
    db_session: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """Delete all analysis sessions past the retention period."""
    retention_days = request.app.state.config.retention.retention_days

    if retention_days <= 0:
        return {
            "data": {"deleted": 0, "retention_days": 0},
            "meta": ResponseMeta().model_dump(),
        }

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)  # noqa: UP017

    # Count matching sessions first
    count_stmt = select(AnalysisSession.id).where(
        AnalysisSession.created_at < cutoff,
    )
    count_result = await db_session.execute(count_stmt)
    expired_ids = list(count_result.scalars().all())
    total_expired = len(expired_ids)

    if total_expired == 0:
        return {
            "data": {"deleted": 0, "retention_days": retention_days},
            "meta": ResponseMeta().model_dump(),
        }

    # Delete in bulk
    delete_stmt = delete(AnalysisSession).where(
        AnalysisSession.created_at < cutoff,
    )
    await db_session.execute(delete_stmt)
    await db_session.commit()

    _logger.info(
        "Expired sessions deleted",
        count=total_expired,
        retention_days=retention_days,
        cutoff=cutoff.isoformat(),
    )

    return {
        "data": {
            "deleted": total_expired,
            "retention_days": retention_days,
        },
        "meta": ResponseMeta().model_dump(),
    }
