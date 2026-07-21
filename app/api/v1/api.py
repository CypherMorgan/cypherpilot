"""V1 API router aggregator.

Imports and includes all v1 route modules.
New modules register here, not in main.py.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.cleanup import router as cleanup_router
from app.api.v1.health import router as health_router
from app.api.v1.settings import router as settings_router
from app.modules.api_test_generation.router import router as api_test_generation_router
from app.modules.auth.router import router as auth_router
from app.modules.failure_analysis.router import (
    router as failure_analysis_router,
)
from app.modules.requirement_analysis.router import (
    router as requirement_analysis_router,
)
from app.modules.teams.router import router as teams_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(teams_router)
router.include_router(cleanup_router)
router.include_router(health_router)
router.include_router(settings_router)
router.include_router(requirement_analysis_router)
router.include_router(api_test_generation_router)
router.include_router(failure_analysis_router)
