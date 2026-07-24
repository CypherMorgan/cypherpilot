"""Audit log service — business logic for logging and querying activity."""

from __future__ import annotations

import uuid as _uuid

from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.infrastructure.models.audit_log import AuditLog
from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas import AuditLogListResponse, AuditLogResponse

_logger = get_logger(__name__)


class AuditService:
    """Service for creating and querying audit log entries."""

    def __init__(self, session: AsyncSession) -> None:
        self._repository = AuditRepository(session)

    async def log(
        self,
        *,
        action: str,
        user_id: _uuid.UUID | None = None,
        team_id: _uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: _uuid.UUID | str | None = None,
        metadata: dict[str, object] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Create an audit log entry.  Fire-and-forget style — errors are
        logged but never raised to the caller."""
        try:
            entry = await self._repository.create(
                user_id=user_id,
                team_id=team_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                metadata=metadata,
                ip_address=ip_address,
            )
            _logger.info(
                "Audit event",
                action=action,
                user_id=str(user_id) if user_id else None,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
            )
            return entry
        except Exception:
            _logger.exception("Failed to write audit log", action=action)
            # Never block the caller — audit is best-effort
            return AuditLog(action=action)

    async def list_logs(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        team_id: _uuid.UUID | None = None,
        user_id: _uuid.UUID | None = None,
        action_prefix: str | None = None,
    ) -> AuditLogListResponse:
        """List audit logs with filtering and pagination."""
        items, total = await self._repository.list_logs(
            page=page,
            page_size=page_size,
            team_id=team_id,
            user_id=user_id,
            action_prefix=action_prefix,
        )
        return AuditLogListResponse(
            items=[AuditLogResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total,
        )
