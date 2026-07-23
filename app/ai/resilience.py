"""Provider Resilience Layer.

Wraps provider calls with:
- Exponential backoff retry with jitter on transient failures (429, 500, 503)
- Automatic fallback to the next configured provider
- Per-provider health tracking (success/failure counts, latency, last error)
- Better error messages for common failures

Usage::

    tracker = HealthTracker()
    resilient = ResilientProvider(
        providers=[("openrouter", openrouter), ("gemini", gemini)],
        health_tracker=tracker,
    )
    response = await resilient.generate(request)  # retries + fallbacks automatically
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any

from structlog import get_logger

from app.ai.models import AIRequest, AIResponse
from app.ai.protocol import AIProvider
from app.exceptions import (
    AuthenticationError,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)

_logger = get_logger(__name__)

# Transient errors that should trigger retry / fallback
_RETRYABLE_ERRORS = (RateLimitError, ProviderTimeoutError, ProviderUnavailableError)
# Auth errors are fatal for a provider — skip to next, don't retry
_AUTH_ERRORS = (AuthenticationError,)

# Retry configuration
_MAX_RETRIES = 2  # 2 retries = 3 total attempts per provider
_BASE_DELAY_S = 1.0
_MAX_DELAY_S = 8.0
_JITTER_RANGE = 0.5  # ±50% of computed delay


@dataclass
class ProviderHealthStats:
    """Health statistics for a single provider."""

    name: str
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: int = 0
    last_error: str = ""
    last_error_time: float = 0.0
    last_success_time: float = 0.0
    consecutive_failures: int = 0

    @property
    def avg_latency_ms(self) -> int:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0
        return self.total_latency_ms // total

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    @property
    def is_healthy(self) -> bool:
        """A provider is considered unhealthy after 5+ consecutive failures."""
        return self.consecutive_failures < 5

    def record_success(self, latency_ms: int) -> None:
        self.success_count += 1
        self.total_latency_ms += latency_ms
        self.last_success_time = time.time()
        self.consecutive_failures = 0

    def record_failure(self, error: str) -> None:
        self.failure_count += 1
        self.last_error = error
        self.last_error_time = time.time()
        self.consecutive_failures += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_latency_ms": self.avg_latency_ms,
            "success_rate": round(self.success_rate, 3),
            "is_healthy": self.is_healthy,
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time,
            "last_success_time": self.last_success_time,
        }


class HealthTracker:
    """Tracks health statistics across all providers."""

    def __init__(self) -> None:
        self._stats: dict[str, ProviderHealthStats] = {}

    def get(self, provider_name: str) -> ProviderHealthStats:
        if provider_name not in self._stats:
            self._stats[provider_name] = ProviderHealthStats(name=provider_name)
        return self._stats[provider_name]

    def all_stats(self) -> list[dict[str, Any]]:
        return [stats.to_dict() for stats in self._stats.values()]

    def reset(self) -> None:
        self._stats.clear()


class ResilientProvider:
    """Wraps multiple providers with retry, fallback, and health tracking.

    Tries the primary provider first with up to ``max_retries`` retries
    on transient errors.  If the primary fails (or is auth-fatal), falls
    through to the next provider in the chain.

    All attempts are tracked in the ``HealthTracker`` for observability.
    """

    def __init__(
        self,
        providers: list[tuple[str, AIProvider]],
        health_tracker: HealthTracker | None = None,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        """Initialise the resilient provider.

        Args:
            providers: Ordered list of ``(name, provider)`` tuples.
                The first is the primary; the rest are fallbacks.
            health_tracker: Shared health tracker instance.
            max_retries: Maximum retry attempts per provider on transient errors.
        """
        if not providers:
            raise ValueError("At least one provider is required")
        self._providers = providers
        self._tracker = health_tracker or HealthTracker()
        self._max_retries = max_retries

    @property
    def name(self) -> str:
        """Return the name of the primary provider."""
        return self._providers[0][0]

    @property
    def available_providers(self) -> list[str]:
        return [name for name, _ in self._providers]

    @property
    def health_tracker(self) -> HealthTracker:
        return self._tracker

    async def generate(self, request: AIRequest) -> AIResponse:
        """Send a request with retry + fallback across providers.

        Returns the first successful response.  If all providers fail,
        raises the last encountered error wrapped in ProviderUnavailableError.
        """
        last_error: Exception | None = None

        for provider_name, provider in self._providers:
            stats = self._tracker.get(provider_name)

            # Skip providers that have been failing repeatedly
            if not stats.is_healthy:
                _logger.warning(
                    "Skipping unhealthy provider",
                    provider=provider_name,
                    consecutive_failures=stats.consecutive_failures,
                )
                continue

            for attempt in range(self._max_retries + 1):
                try:
                    start = time.monotonic()
                    response = await provider.generate(request)
                    latency_ms = int((time.monotonic() - start) * 1000)

                    stats.record_success(latency_ms)

                    if attempt > 0:
                        _logger.info(
                            "Provider recovered after retry",
                            provider=provider_name,
                            attempt=attempt + 1,
                            latency_ms=latency_ms,
                        )

                    return response

                except _AUTH_ERRORS as exc:
                    # Auth errors are fatal for this provider — don't retry
                    error_msg = _friendly_error_message(exc, provider_name)
                    stats.record_failure(error_msg)
                    _logger.warning(
                        "Provider auth failed, trying next",
                        provider=provider_name,
                        error=error_msg,
                    )
                    last_error = exc
                    break  # skip to next provider

                except _RETRYABLE_ERRORS as exc:
                    error_msg = _friendly_error_message(exc, provider_name)
                    stats.record_failure(error_msg)
                    last_error = exc

                    if attempt < self._max_retries:
                        delay = _compute_delay(attempt)
                        _logger.warning(
                            "Provider retryable error, retrying",
                            provider=provider_name,
                            attempt=attempt + 1,
                            delay_ms=int(delay * 1000),
                            error=error_msg,
                        )
                        await asyncio.sleep(delay)
                    else:
                        _logger.warning(
                            "Provider exhausted retries, falling back",
                            provider=provider_name,
                            attempts=attempt + 1,
                            error=error_msg,
                        )

                except ProviderError as exc:
                    # Non-retryable provider errors — don't retry, try next
                    error_msg = _friendly_error_message(exc, provider_name)
                    stats.record_failure(error_msg)
                    _logger.warning(
                        "Provider non-retryable error",
                        provider=provider_name,
                        error=error_msg,
                    )
                    last_error = exc
                    break

                except Exception as exc:
                    # Unexpected errors — treat as non-retryable
                    error_msg = str(exc)
                    stats.record_failure(error_msg)
                    _logger.error(
                        "Provider unexpected error",
                        provider=provider_name,
                        error=error_msg,
                    )
                    last_error = exc
                    break

        # All providers failed
        providers_tried = [name for name, _ in self._providers]
        raise ProviderUnavailableError(
            f"All AI providers failed. Tried: {', '.join(providers_tried)}. "
            f"Last error: {_friendly_error_message(last_error, 'all')}",
            detail={
                "providers_tried": providers_tried,
                "last_error": str(last_error),
            },
        )


def _compute_delay(attempt: int) -> float:
    """Compute exponential backoff delay with jitter.

    Attempt 0 → ~1s, attempt 1 → ~2s, attempt 2 → ~4s, etc.
    """
    base: float = min(_BASE_DELAY_S * (2**attempt), _MAX_DELAY_S)
    jitter: float = random.uniform(-_JITTER_RANGE, _JITTER_RANGE) * base
    return max(0.1, base + jitter)


def _friendly_error_message(exc: Exception | None, provider: str) -> str:
    """Convert a provider exception into a user-friendly message."""
    if exc is None:
        return "Unknown error"

    if isinstance(exc, AuthenticationError):
        return f"Invalid API key for {provider}. Check your credentials."

    if isinstance(exc, RateLimitError):
        return f"Rate limit exceeded for {provider}. Try again later."

    if isinstance(exc, ProviderTimeoutError):
        return f"{provider} request timed out. The service may be slow."

    if isinstance(exc, ProviderUnavailableError):
        return f"{provider} service is unavailable."

    if isinstance(exc, ProviderError):
        detail = exc.detail or {}
        status = detail.get("status_code")
        if status:
            return f"{provider} returned HTTP {status}."
        return exc.message or f"{provider} returned an error."

    return str(exc)
