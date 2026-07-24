"""Audit logging helpers for router handlers.

Provides a non-blocking ``log_audit`` function that can be called
from any FastAPI handler to record an audit event.  Errors are
swallowed — audit logging never breaks the main flow.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.service import AuditService


def _get_client_ip(request: Request | None) -> str | None:
    """Extract client IP from request, respecting X-Forwarded-For."""
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def log_audit(
    db: AsyncSession,
    *,
    action: str,
    user_id: Any = None,
    team_id: Any = None,
    resource_type: str | None = None,
    resource_id: Any = None,
    metadata: dict[str, object] | None = None,
    request: Request | None = None,
) -> None:
    """Log an audit event.  Non-blocking — errors are swallowed."""
    try:
        service = AuditService(session=db)
        await service.log(
            action=action,
            user_id=user_id,
            team_id=team_id,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata,
            ip_address=_get_client_ip(request),
        )
    except Exception:
        # Audit logging is best-effort — never fail the main request
        pass
