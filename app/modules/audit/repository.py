"""Audit log repository — database operations for audit_logs."""

from __future__ import annotations

import uuid as _uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.audit_log import AuditLog


class AuditRepository:
    """Repository for audit log CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: _uuid.UUID | None = None,
        team_id: _uuid.UUID | None = None,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        metadata: dict[str, object] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Create and persist a new audit log entry."""
        entry = AuditLog(
            user_id=user_id,
            team_id=team_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            extra_data=metadata,
            ip_address=ip_address,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_logs(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        team_id: _uuid.UUID | None = None,
        user_id: _uuid.UUID | None = None,
        action_prefix: str | None = None,
    ) -> tuple[list[AuditLog], int]:
        """List audit logs with optional filtering and pagination.

        Returns:
            Tuple of (items, total_count).
        """
        query = select(AuditLog).order_by(AuditLog.created_at.desc())
        count_query = select(func.count(AuditLog.id))

        if team_id is not None:
            query = query.where(AuditLog.team_id == team_id)
            count_query = count_query.where(AuditLog.team_id == team_id)

        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)

        if action_prefix:
            query = query.where(AuditLog.action.startswith(action_prefix))
            count_query = count_query.where(AuditLog.action.startswith(action_prefix))

        # Get total count
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self._session.execute(query)
        items = list(result.scalars().all())

        return items, total
