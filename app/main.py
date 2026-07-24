"""CypherPilot application factory.

Creates and configures the FastAPI application instance.
Wires dependencies, mounts middleware, and registers routes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structlog import get_logger

from app.ai.prompt_manager import PromptManager
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openrouter import OpenRouterProvider
from app.ai.registry import ProviderRegistry
from app.ai.resilience import HealthTracker, ResilientProvider
from app.api.v1.api import router as v1_router
from app.config import AppConfig
from app.exceptions import (
    ConfigurationError,
    CypherPilotError,
    NotFoundError,
    ProviderError,
    ValidationError,
    get_error_code,
)
from app.infrastructure.database import DatabaseManager
from app.infrastructure.models import (  # noqa: F401 — registers models on Base.metadata
    AnalysisSession,
)
from app.infrastructure.models.audit_log import (
    AuditLog,  # noqa: F401 — registers AuditLog on Base.metadata
)
from app.logging_ import configure_logging
from app.middleware.request_id import RequestIDMiddleware
from app.modules.auth.config import AuthConfig
from app.modules.auth.models import User  # noqa: F401 — registers User on Base.metadata
from app.modules.teams.models import (  # noqa: F401 — registers Team/TeamMember on Base.metadata
    Team,
    TeamMember,
)

_logger = get_logger(__name__)


def _build_error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    detail: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build a consistent error response envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "detail": detail or {},
            },
            "meta": {
                "request_id": getattr(request.state, "request_id", ""),
                "timestamp": datetime.utcnow().isoformat(),
            },
        },
    )


def _register_error_handlers(app: FastAPI) -> None:
    """Register exception handlers for all CypherPilot exceptions."""

    @app.exception_handler(ValidationError)
    async def handle_validation_error(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return _build_error_response(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            code=get_error_code(exc),
            message=str(exc),
            detail=exc.detail,
        )

    @app.exception_handler(NotFoundError)
    async def handle_not_found(
        request: Request, exc: NotFoundError
    ) -> JSONResponse:
        return _build_error_response(
            request,
            status_code=status.HTTP_404_NOT_FOUND,
            code=get_error_code(exc),
            message=str(exc),
            detail=exc.detail,
        )

    @app.exception_handler(ProviderError)
    async def handle_provider_error(
        request: Request, exc: ProviderError
    ) -> JSONResponse:
        return _build_error_response(
            request,
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=get_error_code(exc),
            message=str(exc),
            detail=exc.detail,
        )

    @app.exception_handler(ConfigurationError)
    async def handle_configuration_error(
        request: Request, exc: ConfigurationError
    ) -> JSONResponse:
        return _build_error_response(
            request,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=get_error_code(exc),
            message=str(exc),
            detail=exc.detail,
        )

    @app.exception_handler(CypherPilotError)
    async def handle_cypherpilot_error(
        request: Request, exc: CypherPilotError
    ) -> JSONResponse:
        return _build_error_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=get_error_code(exc),
            message=str(exc),
            detail=exc.detail,
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        _logger.error("Unhandled exception", exc_info=exc)
        return _build_error_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
        )


def create_app(config: AppConfig | None = None) -> FastAPI:
    """Create and return a configured FastAPI application instance.

    Args:
        config: Pre-loaded configuration. If None, loads from environment.
    """
    if config is None:
        config = AppConfig()
        config.validate_config()

    app = FastAPI(
        title="CypherPilot API",
        version=config.app_version,
        description="AI-Powered Quality Engineering Platform API",
        lifespan=_make_lifespan(config),  # type: ignore[arg-type]
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in config.cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID middleware
    app.add_middleware(RequestIDMiddleware)

    # Register error handlers
    _register_error_handlers(app)

    # Mount v1 API router
    app.include_router(v1_router)

    return app


def _make_lifespan(config: AppConfig) -> Callable[..., AsyncIterator[None]]:
    # Note: FastAPI's lifespan parameter type is more specific (AbstractAsyncContextManager),
    # but this is accepted by FastAPI at runtime. The arg-type mismatch is suppressed at the call site.
    """Create the lifespan context manager bound to the given config."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Application lifespan handler.

        Startup: initialise database engine, store config, configure logging.
        Shutdown: dispose of database engine and release resources.
        """
        # ── Startup ──────────────────────────────────────────
        app.state.config = config
        configure_logging(config.log_level)

        # Initialise the async database engine (lazy — no connection yet)
        db_manager = DatabaseManager(
            database_url=config.database.url,
            echo=config.database.echo,
        )
        app.state.db_manager = db_manager

        # Initialise auth configuration
        auth_config = AuthConfig()
        app.state.auth_config = auth_config

        # Initialise the provider registry with resilience
        registry = ProviderRegistry()
        health_tracker = HealthTracker()
        registered_providers: list[str] = []

        # Build available providers
        available: list[tuple[str, Any]] = []
        if config.ai.openrouter_api_key:
            available.append((
                "openrouter",
                OpenRouterProvider(
                    api_key=config.ai.openrouter_api_key,
                    model=config.ai.openrouter_model,
                ),
            ))
            registered_providers.append("openrouter")

        if config.ai.ollama_base_url:
            available.append((
                "ollama",
                OllamaProvider(
                    base_url=config.ai.ollama_base_url,
                    model=config.ai.ollama_model,
                ),
            ))
            registered_providers.append("ollama")

        if config.ai.gemini_api_key:
            available.append((
                "gemini",
                GeminiProvider(
                    api_key=config.ai.gemini_api_key,
                    model=config.ai.gemini_model,
                ),
            ))
            registered_providers.append("gemini")

        # Register individual providers for direct access
        for name, provider in available:
            registry.register(name, provider)

        # Build ResilientProvider with fallback chain
        active_provider = config.ai.provider or (available[0][0] if available else "")
        if active_provider and available:
            # Reorder: primary first, then all others as fallbacks
            primary = [(n, p) for n, p in available if n == active_provider]
            fallbacks = [(n, p) for n, p in available if n != active_provider]
            resilient = ResilientProvider(
                providers=primary + fallbacks,
                health_tracker=health_tracker,
            )
            # Register resilient wrapper under the active provider name
            # (overwriting the individual registration)
            registry._providers[active_provider] = resilient

        app.state.provider_registry = registry
        app.state.health_tracker = health_tracker

        # Initialise the prompt manager
        prompt_manager = PromptManager(config.prompts_dir)
        app.state.prompt_manager = prompt_manager

        _logger.info(
            "Application started",
            app_name=config.app_name,
            app_version=config.app_version,
            ai_provider=config.ai.provider or "(none configured)",
            registered_providers=registered_providers,
            database_url=config.database.url,
        )

        yield

        # ── Shutdown ─────────────────────────────────────────
        await db_manager.close()
        _logger.info("Application shutting down")

    return lifespan  # type: ignore[return-value]


app = create_app()
