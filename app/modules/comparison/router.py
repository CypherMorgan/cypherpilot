"""Comparison API routes.

Endpoints:
  POST /compare          — Compare two analysis sessions
  GET  /compare/sessions — List sessions available for comparison (filtered by type)
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.models.analysis_session import AnalysisSession
from app.modules.auth.middleware import get_optional_current_user
from app.modules.auth.models import User
from app.modules.comparison.schemas import CompareRequest
from app.modules.comparison.service import compare_sessions

router = APIRouter(prefix="/compare", tags=["Comparison"])


@router.post(
    "",
    response_model=dict,
    summary="Compare two analysis sessions",
)
async def compare(
    body: CompareRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User | None, Depends(get_optional_current_user)],
) -> dict[str, Any]:
    """Compare two completed analysis sessions of the same type.

    Returns a structured diff showing metadata differences,
    section-by-section item diffs (added/removed/changed/unchanged),
    and the raw output data for both sessions.
    """
    import uuid as _uuid

    # Validate UUIDs
    try:
        id_a = _uuid.UUID(body.session_id_a)
        id_b = _uuid.UUID(body.session_id_b)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        ) from None

    if id_a == id_b:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare a session with itself",
        ) from None

    # Fetch both sessions
    session_a = await db.get(AnalysisSession, id_a)
    session_b = await db.get(AnalysisSession, id_b)

    if session_a is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {body.session_id_a} not found",
        )
    if session_b is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {body.session_id_b} not found",
        ) from None

    # Must be same analysis type
    if session_a.analysis_type != session_b.analysis_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot compare different analysis types: "
                f"{session_a.analysis_type.value} vs {session_b.analysis_type.value}"
            ),
        )

    # Must both be completed
    from app.domain.models import AnalysisStatus

    if session_a.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session {body.session_id_a} is not completed (status: {session_a.status.value})",
        )
    if session_b.status != AnalysisStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session {body.session_id_b} is not completed (status: {session_b.status.value})",
        )

    result = compare_sessions(session_a, session_b)

    return {
        "data": result.model_dump(mode="json"),
        "meta": {"request_id": ""},
    }


@router.get(
    "/sessions",
    response_model=dict,
    summary="List sessions available for comparison",
)
async def list_compare_sessions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User | None, Depends(get_optional_current_user)],
    analysis_type: str | None = Query(
        None,
        description="Filter by analysis type",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """List completed analysis sessions that can be compared."""
    from sqlalchemy import func, select

    from app.domain.models import AnalysisStatus, AnalysisType

    stmt = select(AnalysisSession).where(
        AnalysisSession.status == AnalysisStatus.COMPLETED,
    )

    if analysis_type:
        try:
            at = AnalysisType(analysis_type)
            stmt = stmt.where(AnalysisSession.analysis_type == at)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid analysis type: {analysis_type}. "
                f"Valid types: {[t.value for t in AnalysisType]}",
            ) from None

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt) or 0

    # Paginate
    stmt = stmt.order_by(AnalysisSession.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    sessions = list(result.scalars().all())

    items = []
    for s in sessions:
        items.append({
            "id": str(s.id),
            "title": s.title,
            "analysis_type": s.analysis_type.value if s.analysis_type else "unknown",
            "status": s.status.value if s.status else "unknown",
            "provider": s.provider_used,
            "model": s.model_used,
            "total_tokens": s.total_tokens,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {
        "data": items,
        "meta": {
            "request_id": "",
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_more": (page * page_size) < total,
        },
    }
