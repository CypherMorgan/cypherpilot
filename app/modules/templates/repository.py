"""Repository for analysis template persistence.

All queries are scoped by owner (``user_id``) so users can only ever
see, update, or delete their own templates.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.templates.models import Template


class TemplateRepository:
    """Data access for the templates table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        name: str,
        description: str | None,
        content: str,
        source_type: str,
    ) -> Template:
        """Insert and commit a new template for the given user."""
        template = Template(
            user_id=user_id,
            name=name,
            description=description,
            content=content,
            source_type=source_type,
        )
        self._session.add(template)
        await self._session.commit()
        await self._session.refresh(template)
        return template

    async def get(
        self,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Template | None:
        """Fetch one template owned by ``user_id``, or None."""
        statement = select(Template).where(
            Template.id == template_id,
            Template.user_id == user_id,
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list(
        self,
        user_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Template], int]:
        """Paginated list of the user's templates plus the total count."""
        count_statement = select(func.count()).select_from(Template).where(
            Template.user_id == user_id,
        )
        total = int(await self._session.scalar(count_statement) or 0)

        statement = (
            select(Template)
            .where(Template.user_id == user_id)
            .order_by(Template.updated_at.desc(), Template.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list((await self._session.scalars(statement)).all())
        return items, total

    async def update(
        self,
        template: Template,
        *,
        name: str | None = None,
        description: str | None = None,
        content: str | None = None,
        source_type: str | None = None,
    ) -> Template:
        """Apply partial updates in place, commit, and refresh."""
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if content is not None:
            template.content = content
        if source_type is not None:
            template.source_type = source_type
        await self._session.commit()
        await self._session.refresh(template)
        return template

    async def delete(self, template: Template) -> None:
        """Delete a template and commit."""
        await self._session.delete(template)
        await self._session.commit()
