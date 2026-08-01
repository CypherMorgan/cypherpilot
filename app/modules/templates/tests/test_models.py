"""Tests for the Template ORM model."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.modules.templates.models import Template


class TestTemplateModel:
    """Model-level tests for templates."""

    async def test_create_template(self, db_session, test_user):
        """Creating a template persists all fields."""
        template = Template(
            user_id=test_user.id,
            name="CI Log Failure",
            description="Common pipeline flake",
            content="ERROR: build failed at step 3",
            source_type="ci_log",
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        assert template.id is not None
        assert isinstance(template.id, uuid.UUID)
        assert template.user_id == test_user.id
        assert template.name == "CI Log Failure"
        assert template.description == "Common pipeline flake"
        assert template.content == "ERROR: build failed at step 3"
        assert template.source_type == "ci_log"
        assert template.created_at is not None
        assert template.updated_at is not None

    async def test_default_source_type(self, db_session, test_user):
        """source_type defaults to plain_text when not provided."""
        template = Template(
            user_id=test_user.id,
            name="Plain Text",
            content="Some failure text",
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        assert template.source_type == "plain_text"

    async def test_description_optional(self, db_session, test_user):
        """description is nullable."""
        template = Template(
            user_id=test_user.id,
            name="No Description",
            content="Content",
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)

        assert template.description is None

    async def test_user_foreign_key(self, db_session, test_user):
        """Templates are linked to their owner via user_id FK."""
        template = Template(
            user_id=test_user.id,
            name="Owned",
            content="Content",
        )
        db_session.add(template)
        await db_session.commit()

        stored = await db_session.scalar(
            select(Template).where(Template.name == "Owned")
        )
        assert stored is not None
        assert stored.user_id == test_user.id
