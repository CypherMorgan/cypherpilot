"""Shared fixtures for webhooks module tests."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure SQLite in-memory for tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from app.infrastructure.database import Base
from app.infrastructure.models import AnalysisSession  # noqa: F401
from app.modules.auth.models import User, UserRole
from app.modules.auth.service import AuthService
from app.modules.teams.models import Team  # noqa: F401
from app.modules.webhooks.models import Webhook, WebhookDelivery


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    password_hash = AuthService.hash_password("password123")
    user = User(
        username="whuser",
        email="wh@example.com",
        display_name="Webhook User",
        hashed_password=password_hash,
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user2(db_session: AsyncSession) -> User:
    """Create a second test user."""
    password_hash = AuthService.hash_password("password456")
    user = User(
        username="whuser2",
        email="wh2@example.com",
        display_name="Webhook User 2",
        hashed_password=password_hash,
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def create_webhook(
    db_session: AsyncSession,
    user_id: uuid.UUID,
    *,
    name: str = "CI Hook",
    url: str = "https://example.com/hook",
    events: list[str] | None = None,
    secret: str = "whsec_testsecret1234567890",
    is_active: bool = True,
) -> Webhook:
    """Create a webhook row directly in the database."""
    webhook = Webhook(
        user_id=user_id,
        name=name,
        url=url,
        events=events or ["analysis.completed"],
        secret=secret,
        is_active=is_active,
    )
    db_session.add(webhook)
    await db_session.commit()
    await db_session.refresh(webhook)
    return webhook


async def create_delivery(
    db_session: AsyncSession,
    webhook_id: uuid.UUID,
    *,
    event: str = "analysis.completed",
    session_id: uuid.UUID | None = None,
    payload: dict[str, object] | None = None,
) -> WebhookDelivery:
    """Create a pending delivery row directly in the database."""
    delivery = WebhookDelivery(
        webhook_id=webhook_id,
        event=event,
        session_id=session_id,
        payload=payload or {"event": event},
        status="pending",
        attempts=0,
        max_attempts=3,
    )
    db_session.add(delivery)
    await db_session.commit()
    await db_session.refresh(delivery)
    return delivery
