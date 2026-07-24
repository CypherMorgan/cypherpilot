"""Configuration tests."""

from __future__ import annotations

import pytest

from app.config import AppConfig
from app.exceptions import ConfigurationError


def test_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default configuration values are sensible."""
    # Isolate from conftest module-level env vars and .env file
    monkeypatch.delenv("AI__PROVIDER", raising=False)
    monkeypatch.delenv("AI__OPENROUTER_API_KEY", raising=False)
    config = AppConfig(_env_file=None)
    assert config.app_name == "CypherPilot"
    assert config.app_version == "0.5.2"
    assert config.log_level == "INFO"
    assert config.ai.provider == ""
    assert config.ai.openrouter_model == "openai/gpt-4o-mini"
    assert config.ai.ollama_model == "qwen3"


def test_config_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables override defaults."""
    monkeypatch.setenv("APP_NAME", "CypherPilot-Test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    config = AppConfig(_env_file=None)
    assert config.app_name == "CypherPilot-Test"
    assert config.log_level == "DEBUG"


def test_config_database_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Database config provides sensible defaults."""
    # Remove env overrides to test the compiled default URL
    for key in ("DATABASE_URL", "DATABASE__URL", "DATABASE_SYNC_URL"):
        monkeypatch.delenv(key, raising=False)
    config = AppConfig(_env_file=None)
    assert "postgresql" in config.database.url
    assert "asyncpg" in config.database.url
    assert config.database.pool_size == 5


def test_config_openrouter_api_key_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validation fails when openrouter provider is selected but no key is set."""
    monkeypatch.setenv("AI__PROVIDER", "openrouter")
    monkeypatch.delenv("AI__OPENROUTER_API_KEY", raising=False)

    config = AppConfig(_env_file=None)
    with pytest.raises(ConfigurationError) as exc:
        config.validate_config()

    assert "OPENROUTER_API_KEY" in str(exc.value)


def test_config_openrouter_api_key_validation_passes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validation passes when openrouter provider has a key set."""
    monkeypatch.setenv("AI__PROVIDER", "openrouter")
    monkeypatch.setenv("AI__OPENROUTER_API_KEY", "test-key-123")

    config = AppConfig(_env_file=None)
    config.validate_config()  # Should not raise
