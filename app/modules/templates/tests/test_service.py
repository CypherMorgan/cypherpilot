"""Tests for the TemplateService business logic."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.templates.schemas import (
    CreateTemplateRequest,
    UpdateTemplateRequest,
)
from app.modules.templates.service import TemplateService


def _make_service(db_session: AsyncSession) -> TemplateService:
    return TemplateService(session=db_session)


def _create_payload(**overrides: str) -> CreateTemplateRequest:
    base = {
        "name": "Stack Trace",
        "description": "Null pointer in checkout",
        "content": "java.lang.NullPointerException at CheckoutService",
        "source_type": "stack_trace",
    }
    base.update(overrides)
    return CreateTemplateRequest(**base)


class TestCreateTemplate:
    """Tests for create_template."""

    async def test_create_success(self, db_session, test_user):
        service = _make_service(db_session)
        result = await service.create_template(
            _create_payload(), user_id=test_user.id
        )

        assert result.id is not None
        assert result.name == "Stack Trace"
        assert result.description == "Null pointer in checkout"
        assert result.content == "java.lang.NullPointerException at CheckoutService"
        assert result.source_type == "stack_trace"
        assert result.created_at is not None

    async def test_create_default_source_type(self, db_session, test_user):
        service = _make_service(db_session)
        result = await service.create_template(
            _create_payload(source_type="plain_text"), user_id=test_user.id
        )
        assert result.source_type == "plain_text"

    async def test_create_invalid_source_type(self, db_session, test_user):
        service = _make_service(db_session)
        with pytest.raises(ValueError, match="Invalid source_type"):
            await service.create_template(
                _create_payload(source_type="bogus"), user_id=test_user.id
            )


class TestListTemplates:
    """Tests for list_templates."""

    async def test_list_empty(self, db_session, test_user):
        service = _make_service(db_session)
        result = await service.list_templates(test_user.id)

        assert result.items == []
        assert result.total == 0

    async def test_list_returns_own_templates(self, db_session, test_user, test_user2):
        service = _make_service(db_session)
        await service.create_template(_create_payload(name="Mine"), user_id=test_user.id)
        await service.create_template(
            _create_payload(name="Theirs"), user_id=test_user2.id
        )

        result = await service.list_templates(test_user.id)

        assert result.total == 1
        assert [t.name for t in result.items] == ["Mine"]

    async def test_list_pagination(self, db_session, test_user):
        service = _make_service(db_session)
        for i in range(3):
            await service.create_template(
                _create_payload(name=f"Template {i}"), user_id=test_user.id
            )

        result = await service.list_templates(test_user.id, page=1, page_size=2)
        assert result.total == 3
        assert len(result.items) == 2

        result2 = await service.list_templates(test_user.id, page=2, page_size=2)
        assert len(result2.items) == 1


class TestGetTemplate:
    """Tests for get_template."""

    async def test_get_own_template(self, db_session, test_user):
        service = _make_service(db_session)
        created = await service.create_template(
            _create_payload(), user_id=test_user.id
        )

        result = await service.get_template(created.id, test_user.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Stack Trace"

    async def test_get_missing_returns_none(self, db_session, test_user):
        service = _make_service(db_session)
        result = await service.get_template(
            uuid.UUID("00000000-0000-0000-0000-000000000001"), test_user.id
        )
        assert result is None

    async def test_cannot_get_another_users_template(
        self, db_session, test_user, test_user2
    ):
        service = _make_service(db_session)
        created = await service.create_template(
            _create_payload(), user_id=test_user.id
        )

        result = await service.get_template(created.id, test_user2.id)

        assert result is None


class TestUpdateTemplate:
    """Tests for update_template."""

    async def test_update_partial(self, db_session, test_user):
        service = _make_service(db_session)
        created = await service.create_template(
            _create_payload(), user_id=test_user.id
        )

        result = await service.update_template(
            created.id,
            UpdateTemplateRequest(name="Renamed"),
            user_id=test_user.id,
        )

        assert result is not None
        assert result.name == "Renamed"
        assert result.content == "java.lang.NullPointerException at CheckoutService"
        assert result.description == "Null pointer in checkout"

    async def test_update_missing_returns_none(self, db_session, test_user):
        service = _make_service(db_session)
        result = await service.update_template(
            uuid.UUID("00000000-0000-0000-0000-000000000001"),
            UpdateTemplateRequest(name="Renamed"),
            user_id=test_user.id,
        )
        assert result is None

    async def test_cannot_update_another_users_template(
        self, db_session, test_user, test_user2
    ):
        service = _make_service(db_session)
        created = await service.create_template(
            _create_payload(), user_id=test_user.id
        )

        result = await service.update_template(
            created.id,
            UpdateTemplateRequest(name="Hijacked"),
            user_id=test_user2.id,
        )

        assert result is None

    async def test_update_invalid_source_type(self, db_session, test_user):
        service = _make_service(db_session)
        created = await service.create_template(
            _create_payload(), user_id=test_user.id
        )

        with pytest.raises(ValueError, match="Invalid source_type"):
            await service.update_template(
                created.id,
                UpdateTemplateRequest(source_type="nope"),
                user_id=test_user.id,
            )


class TestDeleteTemplate:
    """Tests for delete_template."""

    async def test_delete_own_template(self, db_session, test_user):
        service = _make_service(db_session)
        created = await service.create_template(
            _create_payload(), user_id=test_user.id
        )

        deleted = await service.delete_template(created.id, test_user.id)

        assert deleted is True
        assert await service.get_template(created.id, test_user.id) is None

    async def test_delete_missing_returns_false(self, db_session, test_user):
        service = _make_service(db_session)
        deleted = await service.delete_template(
            uuid.UUID("00000000-0000-0000-0000-000000000001"), test_user.id
        )
        assert deleted is False

    async def test_cannot_delete_another_users_template(
        self, db_session, test_user, test_user2
    ):
        service = _make_service(db_session)
        created = await service.create_template(
            _create_payload(), user_id=test_user.id
        )

        deleted = await service.delete_template(created.id, test_user2.id)

        assert deleted is False
        assert await service.get_template(created.id, test_user.id) is not None
