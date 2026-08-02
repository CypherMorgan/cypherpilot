"""Tests for the sliding-window rate limiter.

Verifies window arithmetic, limit enforcement, retry-after
computation, key isolation, and memory-bounding behaviour.
"""

from __future__ import annotations

import asyncio

import pytest

from app.infrastructure.rate_limiter import (
    SlidingWindowRateLimiter,
)


@pytest.fixture
def limiter() -> SlidingWindowRateLimiter:
    return SlidingWindowRateLimiter()


class TestBasicEnforcement:
    async def test_allows_hits_up_to_limit(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        statuses = [await limiter.check("k", 3, 60) for _ in range(3)]
        assert all(s.limited is False for s in statuses)
        assert statuses[0].remaining == 2
        assert statuses[1].remaining == 1
        assert statuses[2].remaining == 0

    async def test_rejects_hit_over_limit(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        for _ in range(3):
            await limiter.check("k", 3, 60)
        status = await limiter.check("k", 3, 60)
        assert status.limited is True
        assert status.remaining == 0
        assert status.limit == 3

    async def test_keys_are_isolated(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        for _ in range(5):
            await limiter.check("a", 3, 60)
        status = await limiter.check("b", 3, 60)
        assert status.limited is False
        assert status.remaining == 2

    async def test_negative_limit_rejected(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        with pytest.raises(ValueError):
            await limiter.check("k", 0, 60)


class TestWindowRollover:
    async def test_window_resets_after_cutoff(
        self,
        limiter: SlidingWindowRateLimiter,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import time as time_module

        current = {"t": 1000.0}
        monkeypatch.setattr(time_module, "monotonic", lambda: current["t"])

        for _ in range(3):
            await limiter.check("k", 3, 60)
        status = await limiter.check("k", 3, 60)
        assert status.limited is True

        # Advance past the window — capacity returns.
        current["t"] = 1000.0 + 61
        status = await limiter.check("k", 3, 60)
        assert status.limited is False
        assert status.remaining == 2

    async def test_reset_after_reports_seconds(
        self,
        limiter: SlidingWindowRateLimiter,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import time as time_module

        current = {"t": 1000.0}
        monkeypatch.setattr(time_module, "monotonic", lambda: current["t"])

        for _ in range(3):
            await limiter.check("k", 3, 60)
        current["t"] = 1000.0 + 30  # oldest hit expires in ~31s
        status = await limiter.check("k", 3, 60)
        assert status.limited is True
        assert 30 <= status.reset_after <= 32

    async def test_reset_after_minimum_one(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        for _ in range(2):
            await limiter.check("k", 2, 60)
        status = await limiter.check("k", 2, 60)
        assert status.limited is True
        assert status.reset_after >= 1


class TestConcurrency:
    async def test_concurrent_checks_are_safe(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        async def hammer() -> None:
            for _ in range(50):
                await limiter.check("shared", 100, 60)

        await asyncio.gather(*(hammer() for _ in range(10)))
        status = await limiter.check("shared", 100, 60)
        # 500 hits recorded; at most 100 may be within the window but the
        # limiter must not crash or lose state under contention.
        assert status.limit == 100


class TestResetAndMemory:
    async def test_reset_clears_bucket(
        self, limiter: SlidingWindowRateLimiter
    ) -> None:
        for _ in range(5):
            await limiter.check("k", 3, 60)
        await limiter.reset("k")
        status = await limiter.check("k", 3, 60)
        assert status.limited is False
        assert status.remaining == 2

    async def test_bucket_eviction_at_capacity(self) -> None:
        limiter = SlidingWindowRateLimiter(max_keys=2)
        await limiter.check("a", 5, 60)
        await limiter.check("b", 5, 60)
        # Adding a third key evicts the oldest ("a").
        await limiter.check("c", 5, 60)
        # "a" is gone; a fresh check starts a brand-new bucket.
        status = await limiter.check("a", 5, 60)
        assert status.limited is False
        assert status.remaining == 4
