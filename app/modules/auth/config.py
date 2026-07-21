"""Auth-specific configuration.

Reads from environment variables with AUTH_ prefix.
Secret key defaults to a development-only value and MUST be overridden
in production via ``AUTH__SECRET_KEY`` environment variable.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthConfig(BaseSettings):
    """Authentication configuration.

    Environment variables (all with AUTH_ prefix):
      AUTH__SECRET_KEY       — JWT signing secret (REQUIRED in production)
      AUTH__TOKEN_ALGORITHM — JWT algorithm (default: HS256)
      AUTH__TOKEN_EXPIRE_MINUTES — Token lifetime (default: 1440 = 24h)
    """

    model_config = SettingsConfigDict(
        env_prefix="AUTH__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    secret_key: str = "dev-secret-change-me-in-production"
    """JWT signing secret. Override with AUTH__SECRET_KEY in production."""

    token_algorithm: str = "HS256"
    """JWT algorithm."""

    token_expire_minutes: int = 1440
    """Access token lifetime in minutes (default: 24 hours)."""
