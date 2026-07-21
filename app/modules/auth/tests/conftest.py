"""Shared fixtures for auth module tests."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

# Set test environment BEFORE any app imports
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DATABASE_ECHO", "false")
os.environ.setdefault("AI__OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("AI__PROVIDER", "openrouter")

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import DatabaseManager
from app.main import create_app
from app.modules.auth.config import AuthConfig
from app.modules.auth.service import AuthService


@pytest.fixture
async def db_manager() -> AsyncGenerator[DatabaseManager, None]:
    """In-memory SQLite database with all tables created."""
    manager = DatabaseManager(
        database_url="sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    await manager.create_all()
    yield manager
    await manager.drop_all()
    await manager.close()


@pytest.fixture
async def db_session(
    db_manager: DatabaseManager,
) -> AsyncGenerator[AsyncSession, None]:
    """Fresh database session for a single test."""
    async with db_manager.session() as session:
        yield session


@pytest.fixture
def auth_config() -> AuthConfig:
    """Test auth configuration."""
    return AuthConfig(
        secret_key="test-secret-key-for-unit-tests-min-32",
        token_algorithm="HS256",
        token_expire_minutes=60,
    )


@pytest.fixture
def auth_service(
    db_session: AsyncSession,
    auth_config: AuthConfig,
) -> AuthService:
    """AuthService bound to the test database."""
    return AuthService(session=db_session, config=auth_config)


@pytest.fixture
async def app() -> AsyncGenerator:
    """Test app with in-memory database."""
    app = create_app()
    async with LifespanManager(app):
        db_manager = getattr(app.state, "db_manager", None)
        if db_manager is not None:
            await db_manager.create_all()
        yield app


@pytest.fixture
async def client(
    app,
) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for integration tests."""
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client
