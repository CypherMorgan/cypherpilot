"""Tests for API Test Generation API endpoints.

Uses a minimal FastAPI test app with the service dependency mocked,
eliminating the need for a running database or lifespan.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from app.domain.models import AnalysisStatus
from app.exceptions import NotFoundError, get_error_code
from app.modules.api_test_generation.models import (
    EndpointGenInfo,
    GeneratedFile,
    OpenApiGenerateResponse,
)
from app.modules.api_test_generation.router import _get_service, router
from app.modules.api_test_generation.service import (
    ApiTestGenerationService,
)
from app.modules.auth.middleware import get_optional_current_user


@pytest.fixture
def mock_service() -> AsyncMock:
    """Create a mock API test generation service."""
    session_id = uuid4()
    svc = AsyncMock(spec=ApiTestGenerationService)
    svc.analyze.return_value = OpenApiGenerateResponse(
        session_id=session_id,
        status=AnalysisStatus.COMPLETED.value,
        spec_title="Pet Store API",
        spec_version="1.0.0",
        endpoint_count=6,
        files=[GeneratedFile(filename="test_pets.py", path="generated-tests/test_pets.py", size=100)],
        endpoints=[EndpointGenInfo(path="/pets", method="get", tests_generated=4)],
        download_url=f"/openapi/sessions/{session_id}/download",
        provider="test-provider",
        model="test-model",
        total_tokens=800,
        latency_ms=500,
    )
    svc.get_session.return_value = OpenApiGenerateResponse(
        session_id=uuid4(),
        status=AnalysisStatus.COMPLETED.value,
        spec_title="Pet Store API",
        spec_version="1.0.0",
        endpoint_count=6,
        files=[],
        endpoints=[],
        download_url="/openapi/sessions/mock/download",
        provider="test-provider",
        model="test-model",
        total_tokens=800,
        latency_ms=500,
    )
    svc.list_sessions.return_value = ([], 0)
    svc.download_zip.return_value = b"fake-zip-content"
    return svc


@pytest.fixture
async def client(mock_service: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with the service dependency overridden."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[_get_service] = lambda: mock_service
    app.dependency_overrides[get_optional_current_user] = lambda: None

    # Register exception handler for NotFoundError (matches app/main.py)
    @app.exception_handler(NotFoundError)
    async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": get_error_code(exc),
                    "message": str(exc),
                    "detail": exc.detail or {},
                },
                "meta": {
                    "request_id": getattr(request.state, "request_id", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestGenerateEndpoint:
    """Tests for POST /openapi/analyze."""

    @pytest.fixture
    def valid_payload(self, petstore_yaml: str) -> dict:
        return {
            "spec": petstore_yaml,
            "spec_format": "yaml",
            "title": "Pet Store Tests",
        }

    async def test_analyze_success(self, client: AsyncClient, valid_payload: dict) -> None:
        """A valid request should return 200 with generation data."""
        response = await client.post("/openapi/analyze", json=valid_payload)
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "meta" in body
        assert body["data"]["spec_title"] == "Pet Store API"
        assert body["data"]["endpoint_count"] == 6

    async def test_analyze_with_empty_spec(self, client: AsyncClient) -> None:
        """An empty spec should return 422."""
        response = await client.post(
            "/openapi/analyze",
            json={"spec": "", "spec_format": "yaml"},
        )
        assert response.status_code == 422

    async def test_analyze_with_missing_spec(self, client: AsyncClient) -> None:
        """A missing spec field should return 422."""
        response = await client.post(
            "/openapi/analyze",
            json={"spec_format": "yaml"},
        )
        assert response.status_code == 422

    async def test_analyze_with_paths_filter(self, client: AsyncClient, valid_payload: dict) -> None:
        """A request with paths filter should succeed."""
        payload = {**valid_payload, "paths": ["/pets"]}
        response = await client.post("/openapi/analyze", json=payload)
        assert response.status_code == 200

    async def test_analyze_with_context(self, client: AsyncClient, valid_payload: dict) -> None:
        """A request with context should succeed."""
        payload = {**valid_payload, "context": "Using pytest-asyncio"}
        response = await client.post("/openapi/analyze", json=payload)
        assert response.status_code == 200

    async def test_analyze_with_json_format(self, client: AsyncClient, petstore_yaml: str) -> None:
        """A request with JSON format should succeed."""
        import json as json_mod

        import yaml
        raw = yaml.safe_load(petstore_yaml)
        json_str = json_mod.dumps(raw)
        payload = {"spec": json_str, "spec_format": "json"}
        response = await client.post("/openapi/analyze", json=payload)
        assert response.status_code == 200

    async def test_analyze_invalid_spec_format(self, client: AsyncClient) -> None:
        """An invalid spec_format value should return 422."""
        response = await client.post(
            "/openapi/analyze",
            json={"spec": "openapi: 3.1.0", "spec_format": "toml"},
        )
        assert response.status_code == 422


class TestGetSessionEndpoint:
    """Tests for GET /openapi/sessions/{session_id}."""

    async def test_get_session_success(self, client: AsyncClient) -> None:
        """Getting an existing session should return session data."""
        session_id = uuid4()
        response = await client.get(f"/openapi/sessions/{session_id}")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert body["data"]["spec_title"] == "Pet Store API"

    async def test_get_session_not_found(self, client: AsyncClient) -> None:
        """Getting a nonexistent session should return 404."""
        mock_service = AsyncMock(spec=ApiTestGenerationService)
        mock_service.get_session.side_effect = NotFoundError(
            "Session not found",
            detail={"session_id": str(uuid4())},
        )
        client._transport.app.dependency_overrides[_get_service] = lambda: mock_service

        response = await client.get(f"/openapi/sessions/{uuid4()}")
        assert response.status_code == 404

    async def test_get_session_invalid_uuid(self, client: AsyncClient) -> None:
        """An invalid UUID should return 422."""
        response = await client.get("/openapi/sessions/not-a-uuid")
        assert response.status_code == 422


class TestListSessionsEndpoint:
    """Tests for GET /openapi/sessions."""

    async def test_list_sessions(self, client: AsyncClient) -> None:
        """Listing sessions should return paginated results."""
        response = await client.get("/openapi/sessions")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert isinstance(body["data"], list)
        assert "meta" in body
        assert "pagination" in body["meta"]

    async def test_list_sessions_with_pagination(self, client: AsyncClient) -> None:
        """Listing sessions with pagination params should work."""
        response = await client.get("/openapi/sessions?page=1&page_size=10")
        assert response.status_code == 200


class TestDownloadEndpoint:
    """Tests for GET /openapi/sessions/{session_id}/download."""

    async def test_download_success(self, client: AsyncClient) -> None:
        """Downloading should return a ZIP file."""
        session_id = uuid4()
        response = await client.get(f"/openapi/sessions/{session_id}/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert "content-disposition" in response.headers
        assert ".zip" in response.headers["content-disposition"]

    async def test_download_not_found(self, client: AsyncClient) -> None:
        """Downloading for a nonexistent session should return 404."""
        mock_service = AsyncMock(spec=ApiTestGenerationService)
        mock_service.download_zip.return_value = None
        client._transport.app.dependency_overrides[_get_service] = lambda: mock_service

        response = await client.get(f"/openapi/sessions/{uuid4()}/download")
        assert response.status_code == 404
