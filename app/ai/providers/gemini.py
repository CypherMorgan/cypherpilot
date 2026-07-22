"""Google Gemini provider adapter.

Communicates with the Google AI Studio / Gemini API using the
``generateContent`` REST endpoint.  No Google SDK is required —
all communication is via ``httpx``.

Free tier is supported — ``gemini-2.0-flash`` is used by default.

Configuration via environment variables:
    - ``AI__GEMINI_API_KEY`` — API key from AI Studio (required)
    - ``AI__GEMINI_MODEL`` — Model name (default: ``gemini-2.0-flash``)
"""

from __future__ import annotations

import contextlib
import time
from typing import Any

import httpx

from app.ai.models import AIRequest, AIResponse, ProviderMetadata, TokenUsage
from app.ai.response_validator import parse_json_response
from app.exceptions import (
    AuthenticationError,
    InvalidResponseError,
    ProviderError,
    ProviderTimeoutError,
    RateLimitError,
)


class GeminiProvider:
    """Adapter for the Google Gemini API (generateContent)."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialise the Gemini provider.

        Args:
            api_key: Google AI Studio API key.
            model: Default model identifier.
            http_client: Optional shared ``httpx.AsyncClient``.
                A default client with a 60-second timeout is created if
                none is provided.
        """
        if not api_key:
            raise ValueError("Gemini API key is required")

        self._api_key = api_key
        self._model = model
        self._http = http_client or httpx.AsyncClient(timeout=60.0)

    @property
    def name(self) -> str:
        return "gemini"

    async def generate(self, request: AIRequest) -> AIResponse:
        """Send a generateContent request to the Gemini API.

        Args:
            request: The rendered prompt and configuration.

        Returns:
            A normalized ``AIResponse`` with content, optional parsed
            model, token usage, and provider metadata.

        Raises:
            AuthenticationError: If the API key is invalid.
            RateLimitError: If rate-limited by Gemini.
            ProviderTimeoutError: If the request times out.
            ProviderError: For any other provider error.
        """
        start = time.monotonic()

        model = request.model or self._model

        # Gemini uses systemInstruction at the top level, not as a message role
        contents: list[dict[str, Any]] = [
            {"role": "user", "parts": [{"text": request.user_message}]},
        ]

        payload: dict[str, Any] = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": request.system_prompt}],
            },
            "generationConfig": {
                "temperature": request.temperature or 0.2,
                "maxOutputTokens": request.max_tokens or 4096,
            },
        }

        url = f"{self.BASE_URL}/models/{model}:generateContent"

        try:
            response = await self._http.post(
                url,
                params={"key": self._api_key},
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                f"Gemini request timed out after {self._http.timeout}s",
            ) from exc

        latency_ms = int((time.monotonic() - start) * 1000)

        if response.status_code == 401 or response.status_code == 403:
            raise AuthenticationError(
                "Gemini authentication failed. Check your API key.",
            )

        if response.status_code == 429:
            raise RateLimitError(
                "Gemini rate limit exceeded. Try again later.",
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                f"Gemini returned HTTP {response.status_code}",
                detail={
                    "status_code": response.status_code,
                    "body": response.text[:500],
                },
            ) from exc

        data: dict[str, Any] = response.json()

        # Extract response content from candidates
        candidates = data.get("candidates", [])
        if not candidates:
            # Gemini may return blocked responses with no candidates
            block_reason = (
                data.get("promptFeedback", {}).get("blockReason", "unknown")
            )
            raise ProviderError(
                f"Gemini returned no candidates (block reason: {block_reason})",
                detail={"response": data},
            )

        candidate = candidates[0]
        parts = candidate.get("content", {}).get("parts", [])
        content = "".join(part.get("text", "") for part in parts)

        if not content:
            raise ProviderError(
                "Gemini returned an empty response",
                detail={"response": data},
            )

        # Parse structured response if a response model was requested
        parsed = None
        if request.response_model and content:
            with contextlib.suppress(InvalidResponseError):
                _, parsed = parse_json_response(content, request.response_model)

        # Extract usage information
        usage_data = data.get("usageMetadata", {})
        usage = TokenUsage(
            prompt_tokens=usage_data.get("promptTokenCount", 0),
            completion_tokens=usage_data.get("candidatesTokenCount", 0),
            total_tokens=usage_data.get("totalTokenCount", 0),
        )

        return AIResponse(
            content=content,
            parsed=parsed,
            usage=usage,
            provider=ProviderMetadata(
                provider_name=self.name,
                model=model,
                latency_ms=latency_ms,
            ),
        )
