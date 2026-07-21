"""Failure Analysis API routes.

Provides endpoints for analyzing automation failures, retrieving
session results, and listing past sessions.
"""

from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.domain.models import PaginationMeta, ResponseMeta
from app.infrastructure.database import get_db
from app.modules.auth.middleware import get_optional_current_user
from app.modules.auth.models import User
from app.modules.failure_analysis.models import (
    AnalysisRequest,
    InputSourceType,
)
from app.modules.failure_analysis.service import (
    FailureAnalysisService,
)

router = APIRouter(
    prefix="/failures",
    tags=["Failure Analysis"],
)
_logger = get_logger(__name__)


def _get_service(
    request: Request,
    db_session: AsyncSession = Depends(get_db),
) -> FailureAnalysisService:
    """FastAPI dependency that creates a FailureAnalysisService.

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
    return FailureAnalysisService(
        db_session=db_session,
        provider_registry=registry,
        prompt_manager=request.app.state.prompt_manager,
        active_provider=active_provider,
        artifacts_dir=config.storage.artifacts_dir,
        max_upload_size=config.storage.max_upload_size_mb * 1024 * 1024,
    )


@router.post(
    "/analyze",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Analyze automation failure",
    description=(
        "Submit CI/CD logs, stack traces, or error output for "
        "AI-powered failure analysis. Returns structured analysis "
        "with root cause, suggested fixes, and affected components."
    ),
)
async def analyze_failure(
    request: AnalysisRequest,
    service: FailureAnalysisService = Depends(_get_service),
    user: User | None = Depends(get_optional_current_user),
    http_request: Request = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Analyze the given automation failure input."""
    _logger.info(
        "Failure analysis requested",
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


@router.post(
    "/analyze-with-artifacts",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Analyze failure with artifacts",
    description=(
        "Submit failure text plus optional file artifacts (screenshots, page source, "
        "JSON logs, etc.) for AI-powered failure analysis. Supports multipart form data "
        "with text fields and file uploads."
    ),
)
async def analyze_failure_with_artifacts(
    content: str = Form(default="", max_length=100_000),
    source_type: str = Form(default="plain_text"),
    title: str | None = Form(default=None),
    context: str | None = Form(default=None),
    output_format: str = Form(default="json"),
    artifacts: list[UploadFile] = File(default=[]),
    service: FailureAnalysisService = Depends(_get_service),
    user: User | None = Depends(get_optional_current_user),
    http_request: Request = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Analyze a failure with optional uploaded artifact files."""
    # If content is empty, build a placeholder from filenames so Pydantic
    # validation (min_length=1) still passes.
    effective_content = content
    if not content.strip():
        if not artifacts:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Either 'content' or at least one 'artifacts' file is required.",
            )
        filenames = [f.filename or "unnamed" for f in artifacts if f.filename]
        effective_content = f"[Artifact-only submission — files: {', '.join(filenames)}]"

    request = AnalysisRequest(
        content=effective_content,
        source_type=InputSourceType(source_type),
        title=title,
        context=context,
        output_format=output_format,
    )

    _logger.info(
        "Multi-artifact failure analysis requested",
        source_type=request.source_type.value,
        content_length=len(request.content),
        file_count=len([f for f in artifacts if f.filename]),
    )

    result = await service.analyze_with_artifacts(
        request=request,
        files=artifacts,
        user_id=uuid.UUID(str(user.id)) if user else None,
    )

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
    description="Retrieve a completed failure analysis session by ID.",
)
async def get_analysis_session(
    session_id: UUID,
    service: FailureAnalysisService = Depends(_get_service),
    http_request: Request = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Get the result of a previous failure analysis."""
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
    description="List past failure analysis sessions with pagination.",
)
async def list_analysis_sessions(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page."),
    service: FailureAnalysisService = Depends(_get_service),
    user: User | None = Depends(get_optional_current_user),
    http_request: Request = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """List past failure analysis sessions."""
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
    description="Delete a failure analysis session by ID.",
)
async def delete_analysis_session(
    session_id: UUID,
    service: FailureAnalysisService = Depends(_get_service),
) -> None:
    """Delete a failure analysis session."""
    await service.delete_session(session_id)
