"""AI Provider configuration routes.

Provides endpoints to read and update the AI provider configuration
at runtime without requiring a server restart or .env file edit.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from structlog import get_logger

from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openrouter import OpenRouterProvider
from app.ai.registry import ProviderRegistry
from app.ai.resilience import HealthTracker, ResilientProvider
from app.config import AIConfig
from app.domain.models import ResponseMeta

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)
_logger = get_logger(__name__)

# ── Request/Response models ─────────────────────────────────────


class AiSettingsResponse(BaseModel):
    """Current AI provider configuration (API keys masked)."""

    provider: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = ""
    ollama_base_url: str = ""
    ollama_model: str = ""
    gemini_api_key: str = ""
    gemini_model: str = ""
    max_tokens: int = 4096
    temperature: float = 0.2


class AiSettingsUpdate(BaseModel):
    """AI configuration update payload."""

    provider: str = Field(default="", pattern="^(openrouter|ollama|gemini|)$")
    openrouter_api_key: str = ""
    openrouter_model: str = ""
    ollama_base_url: str = ""
    ollama_model: str = ""
    gemini_api_key: str = ""
    gemini_model: str = ""
    max_tokens: int | None = None
    temperature: float | None = None


def _mask_key(key: str) -> str:
    """Return a masked version of an API key for display."""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _build_response(ai: AIConfig) -> AiSettingsResponse:
    """Build response with API keys masked."""
    return AiSettingsResponse(
        provider=ai.provider,
        openrouter_api_key=_mask_key(ai.openrouter_api_key),
        openrouter_model=ai.openrouter_model,
        ollama_base_url=ai.ollama_base_url,
        ollama_model=ai.ollama_model,
        gemini_api_key=_mask_key(ai.gemini_api_key),
        gemini_model=ai.gemini_model,
        max_tokens=ai.max_tokens,
        temperature=ai.temperature,
    )


def _parse_env_file() -> dict[str, str]:
    """Parse the .env file into a dict of key-value pairs.

    Handles quoted values and comment lines.
    """
    env_paths = [Path(".env"), Path(".env.local")]
    env_vars: dict[str, str] = {}
    for env_path in env_paths:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            env_vars[key] = value
    return env_vars


def _write_env_var(key: str, value: str) -> None:
    """Write or update a single environment variable in .env.local.

    If .env.local doesn't exist, it is created.
    """
    env_path = Path(".env.local")
    existing = {}
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
        for line in lines:
            stripped = line.strip()
            if stripped and "=" in stripped and not stripped.startswith("#"):
                k, _, _ = stripped.partition("=")
                existing[k.strip()] = line
    else:
        lines = []

    prefix = key.split("__")[0] if "__" in key else ""
    # Check if the key already exists
    found = False
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and stripped.startswith(prefix) and "=" in stripped:
            k, _, _ = stripped.partition("=")
            if k.strip() == key:
                new_lines.append(f'{key}="{value}"')
                found = True
                continue
        new_lines.append(line)

    if not found:
        new_lines.append(f'{key}="{value}"')

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _update_provider_registry(
    registry: ProviderRegistry | None, ai: AIConfig
) -> None:
    """Re-register providers in the registry after config changes.

    Rebuilds the ResilientProvider with the updated fallback chain.
    """
    if registry is None:
        return

    # Clear existing providers
    registry._providers = {}

    # Build available providers
    available: list[tuple[str, object]] = []
    if ai.openrouter_api_key:
        available.append((
            "openrouter",
            OpenRouterProvider(
                api_key=ai.openrouter_api_key,
                model=ai.openrouter_model,
            ),
        ))

    if ai.ollama_base_url:
        available.append((
            "ollama",
            OllamaProvider(
                base_url=ai.ollama_base_url,
                model=ai.ollama_model,
            ),
        ))

    if ai.gemini_api_key:
        available.append((
            "gemini",
            GeminiProvider(
                api_key=ai.gemini_api_key,
                model=ai.gemini_model,
            ),
        ))

    # Register individual providers for direct access
    for name, provider in available:
        registry.register(name, provider)  # type: ignore[arg-type]

    # Build ResilientProvider with fallback chain
    active_provider = ai.provider or (available[0][0] if available else "")
    if active_provider and available:
        primary = [(n, p) for n, p in available if n == active_provider]
        fallbacks = [(n, p) for n, p in available if n != active_provider]

        # Reuse existing health tracker if available, otherwise create new
        existing_resilient = registry._providers.get(active_provider)
        tracker: HealthTracker
        if isinstance(existing_resilient, ResilientProvider):
            tracker = existing_resilient.health_tracker
        else:
            tracker = HealthTracker()

        resilient = ResilientProvider(
            providers=primary + fallbacks,  # type: ignore[arg-type]
            health_tracker=tracker,
        )
        registry._providers[active_provider] = resilient


# ── Routes ──────────────────────────────────────────────────────


@router.get("/ai", response_model=dict)
async def get_ai_settings(request: Request) -> dict[str, Any]:
    """Return current AI provider configuration.

    API keys are masked for security (only first 4 + last 4 chars shown).
    """
    config = getattr(request.app.state, "config", None)
    if config is None or not hasattr(config, "ai"):
        return {
            "data": AiSettingsResponse().model_dump(),
            "meta": ResponseMeta().model_dump(),
        }

    return {
        "data": _build_response(config.ai).model_dump(),
        "meta": ResponseMeta().model_dump(),
    }


@router.put("/ai", response_model=dict)
async def update_ai_settings(
    request: Request,
    update: AiSettingsUpdate,
) -> dict[str, Any]:
    """Update AI provider configuration at runtime.

    Persists changes to ``.env.local`` and re-registers providers
    in the registry so new sessions use the updated config immediately.
    """
    config = getattr(request.app.state, "config", None)
    if config is None or not hasattr(config, "ai"):
        return {
            "data": _build_response(
                config.ai if config and hasattr(config, "ai") else AIConfig()
            ).model_dump(),
            "meta": ResponseMeta().model_dump(),
        }

    ai = config.ai

    # Update fields
    if update.provider:
        ai.provider = update.provider
    if update.openrouter_api_key:
        ai.openrouter_api_key = update.openrouter_api_key
    if update.openrouter_model:
        ai.openrouter_model = update.openrouter_model
    if update.ollama_base_url:
        ai.ollama_base_url = update.ollama_base_url
    if update.ollama_model:
        ai.ollama_model = update.ollama_model
    if update.gemini_api_key:
        ai.gemini_api_key = update.gemini_api_key
    if update.gemini_model:
        ai.gemini_model = update.gemini_model
    if update.max_tokens is not None:
        ai.max_tokens = update.max_tokens
    if update.temperature is not None:
        ai.temperature = update.temperature

    # Persist to .env.local
    mapping = {
        "AI__PROVIDER": update.provider,
        "AI__OPENROUTER_API_KEY": update.openrouter_api_key,
        "AI__OPENROUTER_MODEL": update.openrouter_model,
        "AI__OLLAMA_BASE_URL": update.ollama_base_url,
        "AI__OLLAMA_MODEL": update.ollama_model,
        "AI__GEMINI_API_KEY": update.gemini_api_key,
        "AI__GEMINI_MODEL": update.gemini_model,
    }
    for key, value in mapping.items():
        if value:
            _write_env_var(key, value)
            os.environ[key] = value

    # Re-register providers
    registry: ProviderRegistry | None = getattr(
        request.app.state, "provider_registry", None
    )
    _update_provider_registry(registry, ai)

    _logger.info(
        "AI settings updated",
        provider=ai.provider,
    )

    return {
        "data": _build_response(ai).model_dump(),
        "meta": ResponseMeta().model_dump(),
    }
