"""Requirement Analysis API routes.

Provides endpoints for analyzing requirements, retrieving session
results, and listing past sessions.
"""

from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.domain.models import PaginationMeta, ResponseMeta
from app.infrastructure.database import get_db
from app.modules.auth.middleware import get_optional_current_user
from app.modules.auth.models import User
from app.modules.requirement_analysis.models import (
    AnalysisRequest,
)
from app.modules.requirement_analysis.service import (
    RequirementAnalysisService,
)

router = APIRouter(
    prefix="/requirements",
    tags=["Requirement Analysis"],
)
_logger = get_logger(__name__)


def _get_service(
    request: Request,
    db_session: AsyncSession = Depends(get_db),
) -> RequirementAnalysisService:
    """FastAPI dependency that creates a RequirementAnalysisService.

    Reads the provider registry and active provider from application
    state (set during the lifespan startup).
    """
    registry = request.app.state.provider_registry
    config = request.app.state.config
    active_provider = config.ai.provider
    if not active_provider:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail=(
                "No AI provider is configured. "
                "Set AI__PROVIDER in your .env file (e.g. AI__PROVIDER=ollama)."
            ),
        )
    return RequirementAnalysisService(
        db_session=db_session,
        provider_registry=registry,
        prompt_manager=request.app.state.prompt_manager,
        active_provider=active_provider,
    )


@router.post(
    "/analyze",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Analyze requirements",
    description=(
        "Submit requirements text (plain text, Markdown, or acceptance criteria) "
        "for AI-powered analysis. Returns a structured report with test cases, "
        "risks, edge cases, and priority assessment."
    ),
)
async def analyze_requirements(
    request: AnalysisRequest,
    service: RequirementAnalysisService = Depends(_get_service),
    user: User | None = Depends(get_optional_current_user),
    http_request: Request = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Analyze the given requirements text."""
    _logger.info(
        "Requirement analysis requested",
        source_type=request.source_type.value,
        content_length=len(request.content),
    )

    user_id = uuid.UUID(str(user.id)) if user else None
    result = await service.analyze(request, user_id=user_id)

    response = {
        "data": result.model_dump(mode="json"),
        "meta": ResponseMeta(
            request_id=getattr(http_request.state, "request_id", "") if http_request else "",
        ).model_dump(),
    }
    return response


@router.get(
    "/sessions/{session_id}",
    response_model=dict,
    summary="Get analysis session",
    description="Retrieve a completed requirement analysis session by ID.",
)
async def get_analysis_session(
    session_id: UUID,
    service: RequirementAnalysisService = Depends(_get_service),
    http_request: Request = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Get the result of a previous requirement analysis."""
    result = await service.get_session(session_id)

    response = {
        "data": result.model_dump(mode="json"),
        "meta": ResponseMeta(
            request_id=getattr(http_request.state, "request_id", "") if http_request else "",
        ).model_dump(),
    }
    return response


@router.get(
    "/sessions",
    response_model=dict,
    summary="List analysis sessions",
    description="List past requirement analysis sessions with pagination.",
)
async def list_analysis_sessions(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page."),
    service: RequirementAnalysisService = Depends(_get_service),
    user: User | None = Depends(get_optional_current_user),
    http_request: Request = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """List past requirement analysis sessions."""
    user_id = uuid.UUID(str(user.id)) if user else None
    items, total = await service.list_sessions(
        page=page, page_size=page_size, user_id=user_id,
    )

    has_more = (page * page_size) < total

    response = {
        "data": [item.model_dump(mode="json") for item in items],
        "meta": ResponseMeta(
            request_id=getattr(http_request.state, "request_id", "") if http_request else "",
            pagination=PaginationMeta(
                page=page,
                page_size=page_size,
                total=total,
                has_more=has_more,
            ),
        ).model_dump(),
    }
    return response


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete analysis session",
    description="Delete a requirement analysis session by ID.",
)
async def delete_analysis_session(
    session_id: UUID,
    service: RequirementAnalysisService = Depends(_get_service),
) -> None:
    """Delete a requirement analysis session."""
    await service.delete_session(session_id)
