"""Health check endpoint.

Provides a liveness probe with sub-component status checks
(database connectivity, AI provider reachability, etc.).

The overall endpoint always returns 200 so that container orchestrators
(Docker, K8s) see a responsive application.  Individual check failures
are reported in the ``checks`` object without changing the HTTP status.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from structlog import get_logger

from app.ai.registry import ProviderRegistry
from app.ai.resilience import HealthTracker
from app.domain.models import ResponseMeta
from app.infrastructure.database import DatabaseManager

router = APIRouter(tags=["Health"])
_logger = get_logger(__name__)


@router.get("/health")
async def health_check(request: Request) -> dict[str, Any]:
    """Return application health status including sub-component checks.

    Docker health checks should read ``data.status`` — it reflects the
    overall application health.  Currently always ``healthy`` since the
    app is resilient to individual downstream failures.
    """
    config = getattr(request.app.state, "config", None)
    db_manager: DatabaseManager | None = getattr(
        request.app.state, "db_manager", None
    )
    registry: ProviderRegistry | None = getattr(
        request.app.state, "provider_registry", None
    )

    # Determine the active provider and model from config
    active_provider: str | None = None
    active_model: str | None = None
    if config and hasattr(config, "ai"):
        active_provider = config.ai.provider or None
        if active_provider == "openrouter":
            active_model = config.ai.openrouter_model
        elif active_provider == "ollama":
            active_model = config.ai.ollama_model
        elif active_provider == "gemini":
            active_model = config.ai.gemini_model
    # Fall back to the first registered provider name if config is empty
    if not active_provider and registry and registry.available:
        active_provider = registry.available[0]

    # Check database connectivity
    db_check: dict[str, str | int] = {"status": "not_configured"}
    if db_manager is not None:
        start = time.monotonic()
        is_healthy = await db_manager.check_connection()
        elapsed_ms = round((time.monotonic() - start) * 1000)
        if is_healthy:
            db_check = {"status": "healthy", "latency_ms": elapsed_ms}
        else:
            db_check = {"status": "unhealthy", "latency_ms": elapsed_ms}

    # Build provider health summary
    health_tracker: HealthTracker | None = getattr(
        request.app.state, "health_tracker", None
    )
    provider_health: dict[str, Any] = {"status": "not_configured"}
    if registry and registry.available:
        provider_health = {
            "status": "healthy",
            "available": registry.available,
            "active": active_provider,
        }
        if health_tracker and active_provider:
            stats = health_tracker.get(active_provider)
            provider_health["active_healthy"] = stats.is_healthy
            provider_health["active_success_rate"] = round(stats.success_rate, 3)
            provider_health["active_avg_latency_ms"] = stats.avg_latency_ms

    return {
        "data": {
            "status": "healthy",
            "app_name": getattr(config, "app_name", "CypherPilot"),
            "app_version": getattr(config, "app_version", "0.5.2"),
            "active_provider": active_provider,
            "active_model": active_model,
            "checks": {
                "database": db_check,
                "providers": provider_health,
            },
        },
        "meta": ResponseMeta(
            request_id=getattr(request.state, "request_id", ""),
            timestamp=datetime.utcnow(),
        ).model_dump(),
    }
