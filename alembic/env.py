"""Alembic environment configuration for async SQLAlchemy.

Online mode uses an async engine (asyncpg) via ``run_sync``.
Offline mode generates plain SQL using the sync URL.

Environment variables:
  DATABASE_SYNC_URL — Override the sync database URL (default: from alembic.ini)
  DATABASE_URL     — Override the async database URL for online mode
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.infrastructure.database import Base

# Import all models so they register on Base.metadata for autogenerate.
# Each model module must be listed here or imported in models/__init__.py.
from app.infrastructure.models import AnalysisSession  # noqa: F401
from app.modules.auth.models import User  # noqa: F401
from app.modules.teams.models import Team, TeamMember  # noqa: F401

# Alembic Config object
config = context.config

# Set up Python loggers from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL statements to a file rather than executing directly.
    The sync URL is used (no async required).
    """
    sync_url = os.environ.get(
        "DATABASE_SYNC_URL",
        config.get_main_option("sqlalchemy.url", "postgresql://localhost:5432/cypherpilot"),
    )

    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Configure and run migrations on a sync-style connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using an async engine."""
    async_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/cypherpilot",
    )

    connectable = create_async_engine(async_url, poolclass=pool.NullPool)

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Uses ``asyncio.run()`` to drive the async engine.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
