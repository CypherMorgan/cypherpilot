"""Shared fixtures for the rate-limit module tests.

Sets environment variables BEFORE any app imports so ``create_app()``
builds against in-memory SQLite with test-friendly auth/rate settings.
"""

from __future__ import annotations

import os

# Must be set before `from app.main import create_app` runs (the module
# builds an app instance at import time).
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DATABASE_ECHO", "false")
os.environ.setdefault("AI__OPENROUTER_API_KEY", "test-key-for-unit-tests")
os.environ.setdefault("AI__PROVIDER", "openrouter")
