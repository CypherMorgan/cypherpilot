"""Repository for API Test Generation sessions.

Provides database access for API test generation sessions,
extending the generic ``BaseRepository`` with module-specific
query methods.
"""

from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AnalysisType
from app.infrastructure.models.analysis_session import AnalysisSession
from app.infrastructure.repository import BaseRepository
from app.modules.api_test_generation.models import OpenApiSessionListItem


class ApiTestGenerationRepository(BaseRepository[AnalysisSession]):
    """Repository for API test generation sessions."""

    model_class = AnalysisSession

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_sessions(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: uuid.UUID | None = None,
    ) -> tuple[list[OpenApiSessionListItem], int]:
        """List API test generation sessions with pagination.

        Filters to ``API_TEST_GENERATION`` type and returns lightweight
        summary items sorted by creation date (newest first).

        If ``user_id`` is provided, only sessions owned by that user
        are returned.  Otherwise, all sessions are returned.
        """
        base_filter = AnalysisSession.analysis_type == AnalysisType.API_TEST_GENERATION
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

        # Count total
        count_stmt = (
            select(func.count())
            .select_from(AnalysisSession)
            .where(base_filter)
        )
        count_result = await self._session.execute(count_stmt)
        total: int = count_result.scalar() or 0

        items = [
            OpenApiSessionListItem(
                session_id=s.id,
                title=s.title,
                spec_title=(
                    s.output_data.get("spec_title")
                    if s.output_data and isinstance(s.output_data, dict)
                    else None
                ),
                spec_version=(
                    s.output_data.get("spec_version")
                    if s.output_data and isinstance(s.output_data, dict)
                    else None
                ),
                endpoint_count=(
                    s.output_data.get("endpoint_count", 0)
                    if s.output_data and isinstance(s.output_data, dict)
                    else 0
                ),
                file_count=(
                    len(s.output_data.get("files", []))
                    if s.output_data and isinstance(s.output_data, dict)
                    else 0
                ),
                status=s.status.value if hasattr(s.status, "value") else str(s.status),
                provider=s.provider_used,
                total_tokens=s.total_tokens or 0,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sessions
        ]

        return items, total

    async def get_with_output(self, session_id: UUID) -> AnalysisSession | None:
        """Get a session by ID with output data."""
        return await self.get(session_id)
