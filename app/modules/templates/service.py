"""Analysis template service — business logic for reusable templates.

Templates are strictly user-scoped: every operation takes the owner's
``user_id`` and all repository queries are filtered by it, so users can
never read or modify another user's templates.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.modules.templates.repository import TemplateRepository
from app.modules.templates.schemas import (
    SOURCE_TYPES,
    CreateTemplateRequest,
    TemplateListResponse,
    TemplateResponse,
    UpdateTemplateRequest,
)

_logger = get_logger(__name__)


class TemplateService:
    """Encapsulates analysis template logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TemplateRepository(session)

    @staticmethod
    def _validate_source_type(source_type: str | None) -> str | None:
        """Validate a source type value, raising ValueError if invalid."""
        if source_type is not None and source_type not in SOURCE_TYPES:
            raise ValueError(
                f"Invalid source_type '{source_type}'. Must be one of: "
                + ", ".join(SOURCE_TYPES)
            )
        return source_type

    # ── CRUD ────────────────────────────────────────────────────

    async def create_template(
        self,
        data: CreateTemplateRequest,
        user_id: uuid.UUID,
    ) -> TemplateResponse:
        """Create a new template owned by ``user_id``."""
        self._validate_source_type(data.source_type)
        template = await self._repo.create(
            user_id=user_id,
            name=data.name,
            description=data.description,
            content=data.content,
            source_type=data.source_type,
        )
        _logger.info(
            "Template created",
            template_id=str(template.id),
            user_id=str(user_id),
            name=template.name,
        )
        return TemplateResponse.model_validate(template)

    async def list_templates(
        self,
        user_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> TemplateListResponse:
        """Paginated list of the user's templates."""
        templates, total = await self._repo.list(
            user_id,
            page=page,
            page_size=page_size,
        )
        return TemplateListResponse(
            items=[TemplateResponse.model_validate(t) for t in templates],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_template(
        self,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> TemplateResponse | None:
        """Fetch one of the user's templates, or None if not found."""
        template = await self._repo.get(template_id, user_id)
        if template is None:
            return None
        return TemplateResponse.model_validate(template)

    async def update_template(
        self,
        template_id: uuid.UUID,
        data: UpdateTemplateRequest,
        user_id: uuid.UUID,
    ) -> TemplateResponse | None:
        """Partially update one of the user's templates.

        Returns None if the template does not exist or belongs to
        another user.
        """
        template = await self._repo.get(template_id, user_id)
        if template is None:
            return None

        self._validate_source_type(data.source_type)
        template = await self._repo.update(
            template,
            name=data.name,
            description=data.description,
            content=data.content,
            source_type=data.source_type,
        )
        _logger.info(
            "Template updated",
            template_id=str(template.id),
            user_id=str(user_id),
        )
        return TemplateResponse.model_validate(template)

    async def delete_template(
        self,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete one of the user's templates.

        Returns False if the template does not exist or belongs to
        another user.
        """
        template = await self._repo.get(template_id, user_id)
        if template is None:
            return False
        await self._repo.delete(template)
        _logger.info(
            "Template deleted",
            template_id=str(template_id),
            user_id=str(user_id),
        )
        return True
