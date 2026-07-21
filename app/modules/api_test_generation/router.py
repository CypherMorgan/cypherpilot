"""API Test Generation routes.

Provides endpoints for generating PyTest API test suites from
OpenAPI specs, retrieving session results, listing past sessions,
and downloading generated test files.
"""

from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.domain.models import PaginationMeta, ResponseMeta
from app.infrastructure.database import get_db
from app.modules.api_test_generation.models import (
    OpenApiGenerateRequest,
)
from app.modules.api_test_generation.service import (
    ApiTestGenerationService,
)
from app.modules.auth.middleware import get_optional_current_user
from app.modules.auth.models import User

router = APIRouter(
    prefix="/openapi",
    tags=["API Test Generation"],
)
_logger = get_logger(__name__)


def _get_service(
    request: Request,
    db_session: AsyncSession = Depends(get_db),
) -> ApiTestGenerationService:
    """FastAPI dependency that creates an ApiTestGenerationService.

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
    return ApiTestGenerationService(
        db_session=db_session,
        provider_registry=registry,
        prompt_manager=request.app.state.prompt_manager,
        active_provider=active_provider,
    )


@router.post(
    "/analyze",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Generate API tests from an OpenAPI spec",
    description=(
        "Submit an OpenAPI 3.x specification (JSON or YAML) to generate "
        "a production-quality PyTest API test suite. Returns session "
        "metadata and a download URL for the generated test files."
    ),
)
async def generate_api_tests(
    request: OpenApiGenerateRequest,
    service: ApiTestGenerationService = Depends(_get_service),
    user: User | None = Depends(get_optional_current_user),
    http_request: Request = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Generate API tests from the given OpenAPI specification."""
    _logger.info(
        "API test generation requested",
        spec_format=request.spec_format,
        spec_length=len(request.spec),
        path_filter=request.paths is not None,
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
    summary="Get generation session",
    description="Retrieve a completed API test generation session by ID.",
)
async def get_generation_session(
    session_id: UUID,
    service: ApiTestGenerationService = Depends(_get_service),
    http_request: Request = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Get the result of a previous API test generation."""
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
    summary="List generation sessions",
    description="List past API test generation sessions with pagination.",
)
async def list_generation_sessions(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page."),
    service: ApiTestGenerationService = Depends(_get_service),
    user: User | None = Depends(get_optional_current_user),
    http_request: Request = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """List past API test generation sessions."""
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


@router.get(
    "/sessions/{session_id}/download",
    summary="Download generated test files",
    description="Download a ZIP archive of the generated test files.",
)
async def download_generated_tests(
    session_id: UUID,
    service: ApiTestGenerationService = Depends(_get_service),
) -> Response:
    """Download generated test files as a ZIP archive."""
    zip_bytes = await service.download_zip(session_id)

    if zip_bytes is None:
        from app.exceptions import NotFoundError
        raise NotFoundError(
            f"Download not available for session {session_id}",
            detail={"session_id": str(session_id)},
        )

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="generated-tests-{session_id}.zip"',
        },
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete generation session",
    description="Delete an API test generation session by ID.",
)
async def delete_generation_session(
    session_id: UUID,
    service: ApiTestGenerationService = Depends(_get_service),
) -> None:
    """Delete an API test generation session."""
    await service.delete_session(session_id)
