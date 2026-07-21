"""Failure Analysis service.

Orchestrates the end-to-end analysis pipeline:
1. Validate input
2. Render prompt templates with PromptManager
3. Call the AI provider via ProviderRegistry
4. Parse and validate the AI response
5. Persist the session with results
6. Return the structured analysis

Also supports multi-artifact analysis with file uploads.
"""

from __future__ import annotations

import time
import uuid as _uuid
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.ai import (
    AIProvider,
    AIRequest,
    AIResponse,
    PromptManager,
    PromptTemplate,
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
from app.modules.failure_analysis.artifact_service import (
    ArtifactMeta,
    build_artifact_context,
    delete_artifact_files,
    save_artifact,
)
from app.modules.failure_analysis.models import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisSessionListItem,
    ArtifactUpload,
    FailureAnalysisResult,
)
from app.modules.failure_analysis.repository import (
    FailureAnalysisRepository,
)

_logger = get_logger(__name__)


class FailureAnalysisService:
    """Orchestrates the failure analysis pipeline.

    Encapsulates all business logic for analyzing automation failures:
    rendering prompts, calling AI providers, parsing responses,
    persisting results, and retrieving session history.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        provider_registry: ProviderRegistry,
        prompt_manager: PromptManager,
        active_provider: str,
        artifacts_dir: str = "./data/artifacts",
        max_upload_size: int = 10 * 1024 * 1024,
    ) -> None:
        self._repository = FailureAnalysisRepository(db_session)
        self._provider_registry = provider_registry
        self._prompt_manager = prompt_manager
        self._active_provider = active_provider
        self._artifacts_dir = str(Path(artifacts_dir).resolve())
        self._max_upload_size = max_upload_size

    # ── Public API ──────────────────────────────────────────────

    async def analyze(
        self,
        request: AnalysisRequest,
        user_id: _uuid.UUID | None = None,
    ) -> AnalysisResponse:
        """Run the full analysis pipeline on the given input.

        Args:
            request: The validated analysis request.
            user_id: Optional user ID for session ownership.

        Returns:
            The structured analysis response with session metadata.

        Raises:
            AnalysisError: If any step in the pipeline fails.
            ProviderUnavailableError: If the configured provider is
                not registered.
        """
        # 1. Create the session (status=PROCESSING)
        session = AnalysisSession(
            title=request.title or _truncate_title(request.content),
            analysis_type=AnalysisType.FAILURE_ANALYSIS,
            status=AnalysisStatus.PROCESSING,
            input_source_type=request.source_type.value,
            input_content=request.content,
            output_format=request.output_format,
            user_id=user_id,
        )
        session = await self._repository.create(session)
        _logger.info(
            "Failure analysis session created",
            session_id=str(session.id),
        )

        try:
            # 2. Get the AI provider
            provider = self._provider_registry.get(self._active_provider)

            # 3. Render prompt templates
            prompt = self._prompt_manager.load(
                analysis_type="failure-analysis",
                context={
                    "artifact": request.content,
                    "context": request.context or "",
                },
                version="v1",
            )

            # 4. Call the AI provider
            ai_response = await self._call_provider(provider, prompt, session)

            # 5. Parse the response into structured result
            result = await self._parse_response(ai_response, session)

            # 6. Update session with success
            updated = await self._repository.update(
                session.id,
                {
                    "status": AnalysisStatus.COMPLETED,
                    "output_data": result.model_dump(mode="json"),
                    "provider_used": ai_response.provider.provider_name,
                    "model_used": ai_response.provider.model,
                    "prompt_tokens": ai_response.usage.prompt_tokens,
                    "completion_tokens": ai_response.usage.completion_tokens,
                    "total_tokens": ai_response.usage.total_tokens,
                    "latency_ms": ai_response.provider.latency_ms,
                },
            )

            if updated is None:
                raise AnalysisError("Session was deleted during analysis")

            return AnalysisResponse(
                session_id=updated.id,
                status=AnalysisStatus.COMPLETED.value,
                result=result,
                provider=ai_response.provider.provider_name,
                model=ai_response.provider.model,
                total_tokens=ai_response.usage.total_tokens,
                latency_ms=ai_response.provider.latency_ms,
            )

        except Exception as exc:
            # Mark the session as failed
            error_msg = str(exc)
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
                f"Failure analysis failed: {error_msg}",
                detail={"session_id": str(session.id)},
            ) from exc

    async def analyze_with_artifacts(
        self,
        request: AnalysisRequest,
        files: list[UploadFile],
        user_id: _uuid.UUID | None = None,
    ) -> AnalysisResponse:
        """Run analysis with uploaded artifact files.

        Accepts the same text request as ``analyze()``, plus a list of
        uploaded files. Text files (JSON, HTML, logs, etc.) are read and
        their contents are appended to the AI prompt. Image files are
        stored for reference.

        Args:
            request: The validated analysis request.
            files: List of uploaded files (FastAPI ``UploadFile``).

        Returns:
            The structured analysis response with artifact metadata.

        Raises:
            AnalysisError: If any step in the pipeline fails.
        """
        # 1. Create the session (status=PROCESSING)
        # Use first filename as title when content was empty (placeholder text)
        if not request.title and request.content.startswith("[Artifact-only submission"):
            fallback_title = files[0].filename if files and files[0].filename else "Artifact Analysis"
        elif not request.title:
            fallback_title = _truncate_title(request.content) if request.content.strip() else "Untitled Analysis"
        else:
            fallback_title = None

        session = AnalysisSession(
            title=request.title or fallback_title,
            analysis_type=AnalysisType.FAILURE_ANALYSIS,
            status=AnalysisStatus.PROCESSING,
            input_source_type=request.source_type.value,
            input_content=request.content,
            output_format=request.output_format,
            user_id=user_id,
        )
        session = await self._repository.create(session)
        _logger.info(
            "Multi-artifact analysis session created",
            session_id=str(session.id),
            file_count=len(files),
        )

        # 2. Save uploaded artifacts
        artifact_metas: list[ArtifactMeta] = []
        for upload in files:
            if upload.filename:
                meta = await save_artifact(
                    upload=upload,
                    artifacts_dir=self._artifacts_dir,
                    session_id=session.id,
                    max_size=self._max_upload_size,
                )
                artifact_metas.append(meta)

        try:
            # 3. Build the artifact context for the prompt
            artifact_context = build_artifact_context(
                self._artifacts_dir,
                artifact_metas,
            )

            # 4. Combine original content with artifact context
            combined_content = request.content
            if artifact_context:
                combined_content = (
                    f"## User-Provided Failure Description\n\n"
                    f"{request.content}"
                    f"{artifact_context}"
                )

            # 5. Get the AI provider
            provider = self._provider_registry.get(self._active_provider)

            # 6. Render prompt templates with enriched context
            prompt = self._prompt_manager.load(
                analysis_type="failure-analysis",
                context={
                    "artifact": combined_content,
                    "context": request.context or "",
                },
                version="v1",
            )

            # 7. Call the AI provider
            ai_response = await self._call_provider(provider, prompt, session)

            # 8. Parse the response into structured result
            result = await self._parse_response(ai_response, session)

            # 9. Store artifact metadata in output_data
            output = result.model_dump(mode="json")
            if artifact_metas:
                output["_artifacts"] = [
                    a.model_dump(mode="json") for a in artifact_metas
                ]
                output["_artifact_count"] = len(artifact_metas)

            # 10. Update session with success
            updated = await self._repository.update(
                session.id,
                {
                    "status": AnalysisStatus.COMPLETED,
                    "output_data": output,
                    "provider_used": ai_response.provider.provider_name,
                    "model_used": ai_response.provider.model,
                    "prompt_tokens": ai_response.usage.prompt_tokens,
                    "completion_tokens": ai_response.usage.completion_tokens,
                    "total_tokens": ai_response.usage.total_tokens,
                    "latency_ms": ai_response.provider.latency_ms,
                },
            )

            if updated is None:
                raise AnalysisError("Session was deleted during analysis")

            return AnalysisResponse(
                session_id=updated.id,
                status=AnalysisStatus.COMPLETED.value,
                result=result,
                provider=ai_response.provider.provider_name,
                model=ai_response.provider.model,
                total_tokens=ai_response.usage.total_tokens,
                latency_ms=ai_response.provider.latency_ms,
                artifacts=[
                    ArtifactUpload(
                        filename=a.filename,
                        file_type=a.file_type,
                        mime_type=a.mime_type,
                        file_size=a.file_size,
                        storage_path=a.storage_path,
                        content_preview=a.content_preview,
                    )
                    for a in artifact_metas
                ],
            )

        except Exception as exc:
            # Mark the session as failed
            error_msg = str(exc)
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
                f"Multi-artifact analysis failed: {error_msg}",
                detail={"session_id": str(session.id)},
            ) from exc

    async def get_session(
        self, session_id: UUID
    ) -> AnalysisResponse:
        """Retrieve a completed analysis session by ID.

        Args:
            session_id: UUID of the analysis session.

        Returns:
            The analysis response with stored result.

        Raises:
            NotFoundError: If the session does not exist.
        """
        session = await self._repository.get_with_output(session_id)
        if session is None:
            raise NotFoundError(
                f"Analysis session not found: {session_id}",
                detail={"session_id": str(session_id)},
            )

        if session.output_data is None:
            raise NotFoundError(
                f"Analysis session {session_id} has no output data",
                detail={"session_id": str(session_id), "status": str(session.status)},
            )

        result = FailureAnalysisResult.model_validate(session.output_data)

        return AnalysisResponse(
            session_id=session.id,
            status=session.status.value if hasattr(session.status, "value") else str(session.status),
            result=result,
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
    ) -> tuple[list[AnalysisSessionListItem], int]:
        """List failure analysis sessions with pagination.

        Returns:
            Tuple of ``(items, total_count)``.
        """
        return await self._repository.list_sessions(
            page=page,
            page_size=page_size,
            user_id=user_id,
        )

    async def delete_session(self, session_id: UUID) -> None:
        """Delete an analysis session by ID.

        Also removes any artifact files stored on disk for the session.

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

        # Clean up artifact files (best-effort — never throw)
        try:
            delete_artifact_files(self._artifacts_dir, session_id)
        except Exception as exc:
            _logger.warning(
                "Failed to delete artifact files",
                session_id=str(session_id),
                error=str(exc),
            )

    # ── Private helpers ─────────────────────────────────────────

    async def _call_provider(
        self,
        provider: AIProvider,
        prompt: PromptTemplate,
        session: AnalysisSession,
    ) -> AIResponse:
        """Call the AI provider and return the raw response.

        Logs timing and response summary for observability.
        """
        ai_request = AIRequest(
            system_prompt=prompt.system_prompt,
            user_message=prompt.user_message,
            response_model=FailureAnalysisResult,
            temperature=0.2,
            max_tokens=4096,
        )

        start_time = time.monotonic()
        try:
            ai_response: AIResponse = await provider.generate(ai_request)
        except Exception as exc:
            elapsed = int((time.monotonic() - start_time) * 1000)
            _logger.error(
                "AI provider call failed",
                session_id=str(session.id),
                provider=provider.name,
                elapsed_ms=elapsed,
                error=str(exc),
            )
            raise

        elapsed = int((time.monotonic() - start_time) * 1000)
        _logger.info(
            "AI provider response received",
            session_id=str(session.id),
            provider=provider.name,
            elapsed_ms=elapsed,
            prompt_tokens=ai_response.usage.prompt_tokens,
            completion_tokens=ai_response.usage.completion_tokens,
            has_parsed=ai_response.parsed is not None,
        )

        return ai_response

    async def _parse_response(
        self,
        ai_response: AIResponse,
        session: AnalysisSession,
    ) -> FailureAnalysisResult:
        """Parse and validate the AI response.

        If the provider already parsed the response (``parsed`` is not
        None), use that directly.  Otherwise, attempt to parse manually.
        """
        if ai_response.parsed is not None:
            if isinstance(ai_response.parsed, FailureAnalysisResult):
                return ai_response.parsed
            # Convert to FailureAnalysisResult if parsed as different model
            try:
                return FailureAnalysisResult.model_validate(
                    ai_response.parsed.model_dump()
                )
            except Exception:
                pass

        # Manual parse with response_validator
        try:
            _, parsed = response_validator.parse_json_response(
                content=ai_response.content,
                response_model=FailureAnalysisResult,
            )
        except InvalidResponseError as exc:
            _logger.error(
                "Failed to parse AI response",
                session_id=str(session.id),
                error=str(exc),
            )
            raise

        if parsed is None:
            raise InvalidResponseError(
                "AI provider returned empty or unparseable response",
                detail={"session_id": str(session.id)},
            )

        if not isinstance(parsed, FailureAnalysisResult):
            raise InvalidResponseError(
                "Response validation produced unexpected type",
                detail={
                    "session_id": str(session.id),
                    "type": type(parsed).__name__,
                },
            )

        return parsed


def _truncate_title(content: str, max_length: int = 100) -> str:
    """Generate a title from the first line of content."""
    first_line = content.strip().split("\n")[0]
    if len(first_line) > max_length:
        return first_line[: max_length - 3] + "..."
    return first_line
