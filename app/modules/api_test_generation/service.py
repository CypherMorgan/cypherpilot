"""API Test Generation service.

Orchestrates the end-to-end generation pipeline:
1. Parse the OpenAPI spec (programmatic)
2. Generate structural scaffolding (conftest.py, README)
3. Render prompt templates with parsed endpoint data
4. Call the AI provider to generate test code
5. Package generated files into a ZIP archive
6. Persist the session with results
7. Return the generation response
"""

from __future__ import annotations

import time
import uuid as _uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.ai import (
    AIProvider,
    AIRequest,
    AIResponse,
    PromptManager,
    ProviderRegistry,
    response_validator,
)
from app.domain.models import AnalysisStatus, AnalysisType
from app.exceptions import (
    AnalysisError,
    InvalidResponseError,
    NotFoundError,
    ProviderUnavailableError,
)
from app.infrastructure.models.analysis_session import AnalysisSession
from app.modules.api_test_generation.exporters.pytest_generator import PytestGenerator
from app.modules.api_test_generation.models import (
    EndpointGenInfo,
    GeneratedFile,
    OpenApiGenerateRequest,
    OpenApiGenerateResponse,
    OpenApiSessionListItem,
)
from app.modules.api_test_generation.repository import (
    ApiTestGenerationRepository,
)
from app.modules.api_test_generation.spec_parser import (
    ExtractedEndpoint,
    OpenApiParser,
    ParsedSpec,
)

_logger = get_logger(__name__)


class ApiTestGenerationService:
    """Orchestrates the API test generation pipeline."""

    def __init__(
        self,
        db_session: AsyncSession,
        provider_registry: ProviderRegistry,
        prompt_manager: PromptManager,
        active_provider: str,
    ) -> None:
        self._repository = ApiTestGenerationRepository(db_session)
        self._provider_registry = provider_registry
        self._prompt_manager = prompt_manager
        self._active_provider = active_provider
        self._parser = OpenApiParser()
        self._pytest_gen = PytestGenerator()

    # ── Public API ──────────────────────────────────────────────

    async def analyze(
        self,
        request: OpenApiGenerateRequest,
        user_id: _uuid.UUID | None = None,
    ) -> OpenApiGenerateResponse:
        """Run the full test generation pipeline.

        Args:
            request: The validated generation request.

        Returns:
            The generation response with session info and file listing.

        Raises:
            AnalysisError: If any step in the pipeline fails.
            ProviderUnavailableError: If the configured provider is
                not registered.
            ValidationError: If the OpenAPI spec cannot be parsed.
        """
        # ── Session tracking ─────────────────────────────────────
        session: AnalysisSession | None = None

        try:
            # 1. Parse the spec
            parsed = self._parser.parse(request.spec, request.spec_format)

            # 2. Filter endpoints if requested
            endpoints = self._filter_endpoints(parsed.endpoints, request.paths)

            if not endpoints:
                raise AnalysisError(
                    "No endpoints found to generate tests for",
                    detail={
                        "total_endpoints": len(parsed.endpoints),
                        "requested_paths": request.paths,
                    },
                )

            # 3. Create the session (status=PROCESSING)
            title = request.title or f"{parsed.title} v{parsed.version}"
            session = AnalysisSession(
                title=title,
                analysis_type=AnalysisType.API_TEST_GENERATION,
                status=AnalysisStatus.PROCESSING,
                input_content=request.spec[:10000],  # Store truncated spec
                input_source_type=f"openapi_{request.spec_format}",
                user_id=user_id,
            )
            session = await self._repository.create(session)
            _logger.info(
                "API test generation session created",
                session_id=str(session.id),
                spec_title=parsed.title,
                endpoint_count=len(endpoints),
            )


            # 4. Generate scaffolding (programmatic)
            conftest_content = self._pytest_gen.generate_conftest(
                servers=parsed.servers,
                security_schemes=parsed.security_schemes,
            )
            readme_content = self._pytest_gen.generate_readme(
                spec_title=parsed.title,
                spec_version=parsed.version,
                servers=parsed.servers,
                endpoint_count=len(endpoints),
            )

            # 5. Get the AI provider
            provider = self._provider_registry.get(self._active_provider)

            # 6-7. Call AI and parse response (retry once on parse failure)
            max_attempts = 2
            test_files = None
            for attempt in range(max_attempts):
                ai_response = await self._call_ai_for_tests(
                    provider=provider,
                    parsed=parsed,
                    endpoints=endpoints,
                    context=request.context or "",
                )
                try:
                    test_files = self._parse_generated_files(ai_response, session)
                    break  # success
                except InvalidResponseError:
                    if attempt == max_attempts - 1:
                        raise  # last attempt, propagate
                    _logger.warning(
                        "AI response parse failed, retrying",
                        session_id=str(session.id) if session else "pre-creation",
                        attempt=attempt + 1,
                    )

            # 8. Build ZIP archive
            assert test_files is not None  # loop above always sets or raises
            file_list = [
                {"filename": "conftest.py", "content": conftest_content},
                {"filename": "README.md", "content": readme_content},
            ]
            file_list.extend(test_files)

            zip_bytes = self._pytest_gen.build_zip(
                conftest_content=conftest_content,
                readme_content=readme_content,
                test_files=test_files,
            )
            zip_b64 = self._pytest_gen.encode_zip_content(zip_bytes)

            # 9. Build per-endpoint generation summary
            endpoint_info = [
                EndpointGenInfo(
                    path=ep.path,
                    method=ep.method,
                    tests_generated=self._count_tests_for_endpoint(test_files),
                )
                for ep in endpoints
            ]

            # 10. Build output data
            output_files_meta = [
                GeneratedFile(
                    filename=tf["filename"],
                    path=f"generated-tests/{tf['filename']}",
                    size=len(tf["content"].encode("utf-8")),
                )
                for tf in file_list
            ]

            output_data = {
                "spec_title": parsed.title,
                "spec_version": parsed.version,
                "endpoint_count": len(endpoints),
                "files": [
                    f.model_dump(mode="json") for f in output_files_meta
                ],
                "endpoints": [
                    e.model_dump(mode="json") for e in endpoint_info
                ],
                "zip_content": zip_b64,
            }

            # 11. Update session with success
            session = await self._repository.update(
                session.id,
                {
                    "status": AnalysisStatus.COMPLETED,
                    "output_data": output_data,
                    "provider_used": ai_response.provider.provider_name,
                    "model_used": ai_response.provider.model,
                    "prompt_tokens": ai_response.usage.prompt_tokens,
                    "completion_tokens": ai_response.usage.completion_tokens,
                    "total_tokens": ai_response.usage.total_tokens,
                    "latency_ms": ai_response.provider.latency_ms,
                },
            )

            if session is None:
                raise AnalysisError("Session was deleted during generation")

            download_url = f"/api/v1/openapi/sessions/{session.id}/download"

            return OpenApiGenerateResponse(
                session_id=session.id,
                status=AnalysisStatus.COMPLETED.value,
                spec_title=parsed.title,
                spec_version=parsed.version,
                endpoint_count=len(endpoints),
                files=output_files_meta,
                endpoints=endpoint_info,
                download_url=download_url,
                provider=ai_response.provider.provider_name,
                model=ai_response.provider.model,
                total_tokens=ai_response.usage.total_tokens,
                latency_ms=ai_response.provider.latency_ms,
            )

        except Exception as exc:
            error_msg = str(exc)

            # If session was created, mark it as failed
            if session is not None:
                await self._repository.update(
                    session.id,
                    {
                        "status": AnalysisStatus.FAILED,
                        "error_message": error_msg,
                    },
                )

            if isinstance(exc, ProviderUnavailableError | InvalidResponseError | AnalysisError):
                raise

            raise AnalysisError(
                f"API test generation failed: {error_msg}",
                detail={"session_id": str(session.id) if session else "none"},
            ) from exc

    async def get_session(
        self, session_id: UUID
    ) -> OpenApiGenerateResponse:
        """Retrieve a completed generation session by ID.

        Args:
            session_id: UUID of the generation session.

        Returns:
            The generation response with stored metadata.

        Raises:
            NotFoundError: If the session does not exist or has no output.
        """
        session = await self._repository.get_with_output(session_id)
        if session is None:
            raise NotFoundError(
                f"Generation session not found: {session_id}",
                detail={"session_id": str(session_id)},
            )

        if session.output_data is None:
            raise NotFoundError(
                f"Generation session {session_id} has no output data",
                detail={"session_id": str(session_id), "status": str(session.status)},
            )

        od = session.output_data
        files = [
            GeneratedFile(**f) for f in od.get("files", [])
        ]
        endpoints = [
            EndpointGenInfo(**e) for e in od.get("endpoints", [])
        ]

        download_url = f"/api/v1/openapi/sessions/{session.id}/download"

        return OpenApiGenerateResponse(
            session_id=session.id,
            status=session.status.value if hasattr(session.status, "value") else str(session.status),
            spec_title=od.get("spec_title", ""),
            spec_version=od.get("spec_version", ""),
            endpoint_count=od.get("endpoint_count", 0),
            files=files,
            endpoints=endpoints,
            download_url=download_url,
            provider=session.provider_used,
            model=session.model_used,
            total_tokens=session.total_tokens or 0,
            latency_ms=session.latency_ms or 0,
        )

    async def list_sessions(
        self,
        page: int = 1,
        page_size: int = 20,
        user_id: _uuid.UUID | None = None,
    ) -> tuple[list[OpenApiSessionListItem], int]:
        """List API test generation sessions with pagination."""
        return await self._repository.list_sessions(
            page=page,
            page_size=page_size,
            user_id=user_id,
        )

    async def delete_session(self, session_id: UUID) -> None:
        """Delete an API test generation session by ID.

        Args:
            session_id: UUID of the session to delete.

        Raises:
            NotFoundError: If the session does not exist.
        """
        deleted = await self._repository.delete(session_id)
        if not deleted:
            raise NotFoundError(
                f"Analysis session not found: {session_id}",
                detail={"session_id": str(session_id)},
            )

    async def download_zip(self, session_id: UUID) -> bytes | None:
        """Get the ZIP archive bytes for a completed session.

        Args:
            session_id: UUID of the generation session.

        Returns:
            ZIP archive bytes, or ``None`` if not available.
        """
        session = await self._repository.get_with_output(session_id)
        if session is None or session.output_data is None:
            return None

        zip_b64 = session.output_data.get("zip_content")
        if not zip_b64:
            return None

        return self._pytest_gen.decode_zip_content(zip_b64)

    # ── Private helpers ─────────────────────────────────────────

    def _filter_endpoints(
        self,
        endpoints: list[ExtractedEndpoint],
        paths: list[str] | None,
    ) -> list[ExtractedEndpoint]:
        """Filter endpoints by path if requested.

        If ``paths`` is None or empty, all endpoints are returned.
        Otherwise, only endpoints whose path matches one of the
        provided paths are returned.
        """
        if not paths:
            return endpoints

        path_set = set(paths)
        return [ep for ep in endpoints if ep.path in path_set]

    def _group_endpoints_by_tag(
        self,
        endpoints: list[ExtractedEndpoint],
    ) -> dict[str, list[ExtractedEndpoint]]:
        """Group endpoints by their OpenAPI tags.

        An endpoint with multiple tags appears in each group.
        Endpoints without tags are grouped under ``"default"``.
        """
        groups: dict[str, list[ExtractedEndpoint]] = {}
        for ep in endpoints:
            for tag in (ep.tags or ["default"]):
                groups.setdefault(tag, []).append(ep)
        return groups

    async def _call_ai_for_tests(
        self,
        provider: AIProvider,
        parsed: ParsedSpec,
        endpoints: list[ExtractedEndpoint],
        context: str,
    ) -> AIResponse:
        """Call the AI provider to generate test code.

        Groups endpoints by tag and renders a prompt with the
        structured spec data for each group, calling the AI once
        for all endpoints.
        """
        # Prepare endpoint data for template rendering
        endpoint_dicts = []
        for ep in endpoints:
            ep_dict = {
                "path": ep.path,
                "method": ep.method,
                "summary": ep.summary or "",
                "description": ep.description or "",
                "operation_id": ep.operation_id or "",
                "tags": ep.tags,
                "deprecated": ep.deprecated,
                "parameters": [
                    {
                        "name": p.name,
                        "location": p.location,
                        "schema_type": p.schema_type,
                        "required": p.required,
                        "description": p.description or "",
                    }
                    for p in ep.parameters
                ],
                "request_body": (
                    {
                        "required": ep.request_body.required,
                        "content_type": ep.request_body.content_type,
                        "schema_ref": ep.request_body.schema_ref or "",
                        "description": ep.request_body.description or "",
                    }
                    if ep.request_body
                    else None
                ),
                "responses": {
                    status: {
                        "description": resp.description or "",
                        "schema_ref": resp.schema_ref or "",
                    }
                    for status, resp in ep.responses.items()
                },
            }
            endpoint_dicts.append(ep_dict)

        # Prepare schema data for template
        schema_dicts = [
            {
                "name": s.name,
                "type": s.type,
                "description": s.description or "",
                "properties": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "required": p.required,
                        "description": p.description or "",
                    }
                    for p in s.properties
                ],
            }
            for s in parsed.schemas
        ]

        # Build auth schemes summary
        auth_summary = ", ".join(
            f"{name} ({scheme.type})"
            for name, scheme in parsed.security_schemes.items()
        ) or "None"

        # Render prompt
        prompt = self._prompt_manager.load(
            analysis_type="api-test-generation",
            context={
                "spec_title": parsed.title,
                "spec_version": parsed.version,
                "servers": parsed.servers,
                "auth_schemes": auth_summary,
                "schemas": schema_dicts,
                "endpoints": endpoint_dicts,
                "context": context,
            },
            version="v1",
        )

        ai_request = AIRequest(
            system_prompt=prompt.system_prompt,
            user_message=prompt.user_message,
            temperature=0.2,
            max_tokens=16384,
        )

        start_time = time.monotonic()
        try:
            ai_response: AIResponse = await provider.generate(ai_request)
        except Exception as exc:
            elapsed = int((time.monotonic() - start_time) * 1000)
            _logger.error(
                "AI provider call failed",
                provider=provider.name,
                elapsed_ms=elapsed,
                error=str(exc),
            )
            raise

        elapsed = int((time.monotonic() - start_time) * 1000)
        _logger.info(
            "AI provider response received",
            provider=provider.name,
            elapsed_ms=elapsed,
            prompt_tokens=ai_response.usage.prompt_tokens,
            completion_tokens=ai_response.usage.completion_tokens,
            has_parsed=ai_response.parsed is not None,
        )

        return ai_response

    def _parse_generated_files(
        self,
        ai_response: AIResponse,
        session: AnalysisSession,
    ) -> list[dict[str, str]]:
        """Parse AI response to extract generated test files.

        Tries the parsed response first, then falls back to manual
        JSON parsing.
        """
        raw = None

        if ai_response.parsed is not None:
            try:
                raw = ai_response.parsed.model_dump()
            except Exception:
                raw = None

        if raw is None:
            try:
                # Validate JSON is parseable, then use directly as dict
                raw_text, _ = response_validator.parse_json_response(
                    content=ai_response.content,
                    response_model=None,
                )
                # Manually parse the JSON since validator returns None for parsed
                import json as _json
                raw = _json.loads(raw_text)
            except (InvalidResponseError, _json.JSONDecodeError) as exc:
                _logger.error(
                    "Failed to parse AI response for API test generation",
                    session_id=str(session.id),
                    error=str(exc),
                )
                raise InvalidResponseError(
                    "AI provider returned unparseable response for test generation",
                    detail={"session_id": str(session.id)},
                ) from exc

        if not isinstance(raw, dict):
            raise InvalidResponseError(
                "AI response is not a valid JSON object",
                detail={"session_id": str(session.id)},
            )

        files_raw = raw.get("files", [])
        if not isinstance(files_raw, list):
            raise InvalidResponseError(
                "AI response missing 'files' array",
                detail={"session_id": str(session.id)},
            )

        files: list[dict[str, str]] = []
        for f in files_raw:
            if isinstance(f, dict) and "filename" in f and "content" in f:
                files.append({
                    "filename": str(f["filename"]),
                    "content": str(f["content"]),
                })

        if not files:
            raise InvalidResponseError(
                "AI response contains no valid test files",
                detail={"session_id": str(session.id)},
            )

        return files

    def _count_tests_for_endpoint(
        self,
        test_files: list[dict[str, str]],
    ) -> int:
        """Estimate the number of test functions for an endpoint.

        Counts occurrences of ``test_`` in the relevant test file.
        This is a rough estimate; exact counting would require
        AST parsing.
        """
        count = 0
        for tf in test_files:
            # Count test function definitions
            count += tf.get("content", "").count("async def test_")
        return count or 1  # At least 1 test per endpoint
