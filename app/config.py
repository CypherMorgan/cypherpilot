"""Application configuration via pydantic-settings.

All configuration is loaded from environment variables or .env file.
Every config value has a default or is explicitly documented as required.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """PostgreSQL connection configuration.

    Environment variables (all with DATABASE_ prefix):
      DATABASE_URL       — Async URL for the app (default: postgresql+asyncpg://...)
      DATABASE_SYNC_URL  — Sync URL for Alembic migrations (default: postgresql://...)
      DATABASE_ECHO      — Log all SQL statements (default: false)
      DATABASE_POOL_SIZE — Connection pool size (default: 5)
      DATABASE_MAX_OVERFLOW — Max pool overflow connections (default: 10)
    """

    model_config = SettingsConfigDict(env_prefix="DATABASE_", extra="ignore")

    url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cypherpilot"
    """Async database URL for the application."""

    sync_url: str = "postgresql://postgres:postgres@localhost:5432/cypherpilot"
    """Sync database URL for Alembic migrations (psycopg2 driver)."""

    echo: bool = False
    """Log all SQL statements to stderr."""

    pool_size: int = 5
    max_overflow: int = 10


class AIConfig(BaseSettings):
    """AI provider configuration."""

    provider: str = ""
    """Active AI provider name. Must match a registered provider.

    Set to ``openrouter``, ``ollama``, or leave empty to skip AI
    provider validation (useful during infrastructure setup).
    Supported in future releases: ``openai``, ``claude``, ``gemini``, ``groq``.
    """

    # ── OpenRouter (default) ──────────────────────────────────
    openrouter_api_key: str = ""
    """OpenRouter API key. Required when provider is 'openrouter'."""

    openrouter_model: str = "openai/gpt-4o-mini"
    """Default OpenRouter model name."""

    # ── Ollama (local/offline) ────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    """Ollama server URL. Used when provider is 'ollama'."""

    ollama_model: str = "qwen3"
    """Default Ollama model name."""

    # ── Future providers ──────────────────────────────────────
    gemini_api_key: str = ""
    """Google Gemini API key. Required when provider is 'gemini' (future)."""

    gemini_model: str = "gemini-2.0-flash"
    """Default Gemini model name (future)."""

    # ── Shared settings ───────────────────────────────────────
    max_tokens: int = 4096
    """Default max output tokens for AI responses."""

    temperature: float = 0.2
    """Default temperature for AI responses."""


class StorageConfig(BaseSettings):
    """File storage configuration."""

    artifacts_dir: str = "./data/artifacts"
    """Directory for uploaded artifact storage."""

    max_upload_size_mb: int = 10
    """Maximum upload file size in megabytes."""


class RetentionConfig(BaseSettings):
    """Session retention policy configuration.

    Controls automatic cleanup of old analysis sessions.

    Can be configured via ``RETENTION__RETENTION_DAYS`` or
    ``SESSION_RETENTION_DAYS`` environment variable.
    """

    retention_days: int = Field(default=90)
    """Number of days to keep analysis sessions. Sessions older than
    this are eligible for automatic cleanup. Set to 0 to disable."""


class AppConfig(BaseSettings):
    """Top-level application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    debug: bool = False
    """Enable debug mode. Set DEBUG=true."""

    app_name: str = "CypherPilot"
    app_version: str = "0.4.9"

    log_level: str = "INFO"
    """Logging level: DEBUG, INFO, WARNING, ERROR."""

    cors_origins: str = "http://localhost:3000"
    """Allowed CORS origins (comma-separated string in .env).

    pydantic-settings treats ``str`` as a simple type and passes the raw env
    var value through without JSON parsing.  Split on comma to get the list
    of origins at the usage site.
    """

    prompts_dir: str = "./prompts"
    """Path to prompt template directory."""

    prompt_default_version: str = "v1"
    """Default prompt template version."""

    # Nested config sections (use default_factory so each AppConfig()
    # construction re-reads current environment variables rather than
    # freezing them at class-attribute-definition time).
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    retention: RetentionConfig = Field(default_factory=RetentionConfig)

    def validate_config(self) -> None:
        """Validate configuration at startup.

        Raises ConfigurationError if required values are missing.
        """
        if not self.ai.provider:
            return

        provider = self.ai.provider

        if provider == "openrouter" and not self.ai.openrouter_api_key:
            from app.exceptions import ConfigurationError

            raise ConfigurationError(
                "OPENROUTER_API_KEY is required when AI_PROVIDER is 'openrouter'",
                detail={
                    "provider": "openrouter",
                    "hint": "Set AI__OPENROUTER_API_KEY in .env or environment",
                },
            )

        if provider == "gemini" and not self.ai.gemini_api_key:
            from app.exceptions import ConfigurationError

            raise ConfigurationError(
                "GEMINI_API_KEY is required when AI_PROVIDER is 'gemini'",
                detail={
                    "provider": "gemini",
                    "hint": "Set AI__GEMINI_API_KEY in .env or environment",
                },
            )

        supported = {"openrouter", "ollama"}
        if provider not in supported:
            from app.exceptions import ConfigurationError

            raise ConfigurationError(
                f"Unsupported AI provider: '{provider}'. "
                f"Supported: {', '.join(sorted(supported))}",
                detail={
                    "provider": provider,
                    "supported": list(sorted(supported)),
                },
            )
