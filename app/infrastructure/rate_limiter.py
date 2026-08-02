"""In-memory sliding-window rate limiter.

A simple, dependency-free limiter intended for single-process
deployments. Each key (user id, team id, or client IP) keeps a deque
of hit timestamps on a monotonic clock; a hit is allowed while fewer
than ``limit`` hits fall inside the current window.

Buckets are pruned lazily on every check and a hard cap on tracked
keys bounds memory usage, so the limiter never grows without bound.
For multi-instance deployments this should be replaced with a shared
store (Redis, etc.), but the interface can stay the same.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitStatus:
    """Outcome of a rate-limit check for a single bucket."""

    limited: bool
    """True when the request would exceed the bucket limit."""
    limit: int
    """Bucket capacity (max requests per window)."""
    remaining: int
    """Tokens left after this check (0 when limited)."""
    reset_after: int
    """Seconds until the window rolls over (the caller may retry)."""
    key: str
    """Bucket key the status refers to."""


class SlidingWindowRateLimiter:
    """Asyncio-safe sliding-window counter keyed by string.

    All mutating operations are serialised behind an ``asyncio.Lock``
    so concurrent request handlers cannot corrupt a bucket. The check
    itself is cheap: one dict lookup, a prune pass over expired hits,
    and an append at the tail.
    """

    def __init__(self, max_keys: int = 100_000) -> None:
        self._max_keys = max_keys
        self._buckets: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitStatus:
        """Record one hit for ``key`` and evaluate the bucket status.

        Args:
            key: Unique bucket identifier (e.g. ``user:<uuid>``).
            limit: Maximum hits allowed per window. Must be >= 1.
            window_seconds: Sliding window length in seconds.

        Returns:
            A :class:`RateLimitStatus` describing whether the hit was
            allowed and the remaining/reset information for headers.
        """
        if limit < 1:
            raise ValueError("limit must be >= 1")

        async with self._lock:
            now = time.monotonic()
            cutoff = now - window_seconds
            hits = self._buckets.get(key)

            # Fresh bucket: record the hit and allow it.
            if hits is None:
                self._evict_oldest_if_full()
                self._buckets[key] = deque([now])
                return RateLimitStatus(
                    limited=False,
                    limit=limit,
                    remaining=limit - 1,
                    reset_after=window_seconds,
                    key=key,
                )

            # Drop hits that have fallen out of the window.
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= limit:
                # Over capacity: reject without recording. reset_after is
                # the time until the oldest hit leaves the window.
                reset_after = self._reset_after(hits, now, window_seconds)
                return RateLimitStatus(
                    limited=True,
                    limit=limit,
                    remaining=0,
                    reset_after=reset_after,
                    key=key,
                )

            # Under capacity: record the hit and report remaining.
            hits.append(now)
            return RateLimitStatus(
                limited=False,
                limit=limit,
                remaining=limit - len(hits),
                reset_after=self._reset_after(hits, now, window_seconds),
                key=key,
            )

    async def reset(self, key: str) -> None:
        """Drop the bucket for ``key`` (used by tests / admin tools)."""
        async with self._lock:
            self._buckets.pop(key, None)

    def _reset_after(
        self,
        hits: deque[float],
        now: float,
        window_seconds: int,
    ) -> int:
        """Seconds until the oldest hit expires (minimum 1)."""
        if not hits:
            return max(1, window_seconds)
        seconds = int(window_seconds - (now - hits[0])) + 1
        return max(1, seconds)

    def _evict_oldest_if_full(self) -> None:
        """Bound memory by dropping the oldest bucket at capacity."""
        if len(self._buckets) < self._max_keys:
            return
        # Dicts preserve insertion order, so the first key is the oldest.
        self._buckets.pop(next(iter(self._buckets)))
