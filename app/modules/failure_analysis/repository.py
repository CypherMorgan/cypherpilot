"""Failure Analysis repository.

Provides database access for failure analysis sessions,
extending the generic ``BaseRepository`` with failure-specific
query methods.
"""

from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.analysis_session import AnalysisSession
from app.infrastructure.repository import BaseRepository
from app.modules.failure_analysis.models import AnalysisSessionListItem


class FailureAnalysisRepository(BaseRepository[AnalysisSession]):
    """Repository for failure analysis sessions.

    Inherits create, get, list, update, delete from ``BaseRepository``.
    Adds failure-specific query methods below.
    """

    model_class = AnalysisSession

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_sessions(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: uuid.UUID | None = None,
    ) -> tuple[list[AnalysisSessionListItem], int]:
        """List failure analysis sessions with pagination.

        Filters to ``FAILURE_ANALYSIS`` type and returns lightweight
        summary items sorted by creation date (newest first).

        If ``user_id`` is provided, only sessions owned by that user
        are returned.  Otherwise, all sessions are returned.
        """
        from app.domain.models import AnalysisType

        base_filter = AnalysisSession.analysis_type == AnalysisType.FAILURE_ANALYSIS
        if user_id is not None:
            base_filter = base_filter & (AnalysisSession.user_id == user_id)

        stmt = (
            select(AnalysisSession)
            .where(base_filter)
            .order_by(AnalysisSession.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        sessions = list(result.scalars().all())

        # Also get total count
        count_stmt = (
            select(func.count())
            .select_from(AnalysisSession)
            .where(base_filter)
        )
        count_result = await self._session.execute(count_stmt)
        total: int = count_result.scalar() or 0

        items = [
            AnalysisSessionListItem(
                session_id=s.id,
                title=s.title,
                source_type=s.input_source_type,
                status=s.status.value if hasattr(s.status, "value") else str(s.status),
                provider=s.provider_used,
                total_tokens=s.total_tokens or 0,
                created_at=s.created_at,
                updated_at=s.updated_at,
                input_summary=(
                    s.output_data.get("input_summary")
                    if s.output_data and isinstance(s.output_data, dict)
                    else None
                ),
            )
            for s in sessions
        ]

        return items, total

    async def get_with_output(self, session_id: UUID) -> AnalysisSession | None:
        """Get a session by ID with eager-loaded output data.

        This is an alias for ``get()`` currently, but provides a
        clear extension point if lazy loading or select-inload is
        needed in the future.
        """
        return await self.get(session_id)
