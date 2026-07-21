"""Shared fixtures for team module tests."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure SQLite in-memory for tests
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from app.infrastructure.database import Base
from app.modules.auth.config import AuthConfig
from app.modules.auth.models import User, UserRole
from app.modules.auth.service import AuthService


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
        username="testuser",
        email="test@example.com",
        display_name="Test User",
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
        username="testuser2",
        email="test2@example.com",
        display_name="Test User 2",
        hashed_password=password_hash,
        role=UserRole.USER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_config() -> AuthConfig:
    return AuthConfig()
