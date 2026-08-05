"""Tests for webhook delivery primitives.

Covers payload canonicalization, HMAC signing, payload building, and the
retry/recording behavior of ``deliver_webhook`` (with an injected
``httpx.MockTransport`` so no real network I/O occurs).
"""

from __future__ import annotations

import hashlib
import hmac
from types import SimpleNamespace

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import WebhookConfig
from app.domain.models import AnalysisStatus, AnalysisType
from app.modules.webhooks.delivery import (
    DELIVERY_HEADER,
    EVENT_HEADER,
    SIGNATURE_HEADER,
    build_analysis_payload,
    canonical_body,
    deliver_webhook,
    new_test_payload,
    sign_payload,
)
from app.modules.webhooks.tests.conftest import create_delivery, create_webhook

_SECRET = "whsec_testsecret1234567890"


class TestCanonicalBody:
    """Payload canonicalization must be deterministic."""

    def test_same_payload_same_bytes(self) -> None:
        payload = {"b": 2, "a": 1, "nested": {"z": "x", "y": True}}
        assert canonical_body(payload) == canonical_body(payload)

    def test_key_order_does_not_matter(self) -> None:
        first = canonical_body({"a": 1, "b": 2})
        second = canonical_body({"b": 2, "a": 1})
        assert first == second

    def test_returns_bytes(self) -> None:
        assert isinstance(canonical_body({"a": 1}), bytes)


class TestSignPayload:
    """HMAC-SHA256 signing must produce verifiable signatures."""

    def test_prefix_and_length(self) -> None:
        signature = sign_payload(_SECRET, canonical_body({"a": 1}))
        assert signature.startswith("sha256=")
        assert len(signature) == 7 + 64

    def test_verifies_over_canonical_body(self) -> None:
        body = canonical_body({"event": "analysis.completed"})
        signature = sign_payload(_SECRET, body)
        digest = hmac.new(
            _SECRET.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()
        assert signature == f"sha256={digest}"

    def test_tampered_body_fails_verification(self) -> None:
        body = canonical_body({"event": "analysis.completed"})
        tampered = canonical_body({"event": "analysis.failed"})
        assert sign_payload(_SECRET, body) != sign_payload(_SECRET, tampered)


def _fake_session(**overrides: object) -> SimpleNamespace:
    """An AnalysisSession-like object with sane defaults."""
    base: dict[str, object] = {
        "id": "11111111-1111-1111-1111-111111111111",
        "analysis_type": AnalysisType.FAILURE_ANALYSIS,
        "title": "Payments test run",
        "status": AnalysisStatus.COMPLETED,
        "provider_used": "openai",
        "model_used": "gpt-4o",
        "total_tokens": 1234,
        "latency_ms": 890,
        "error_message": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


class TestBuildAnalysisPayload:
    """Payload building must produce a stable, defensive shape."""

    def test_completed_payload(self) -> None:
        payload = build_analysis_payload(
            "analysis.completed", _fake_session()
        )
        assert payload["event"] == "analysis.completed"
        assert payload["session_id"] == "11111111-1111-1111-1111-111111111111"
        assert payload["analysis_type"] == "failure-analysis"
        assert payload["status"] == "completed"
        assert payload["title"] == "Payments test run"
        assert payload["provider"] == "openai"
        assert payload["model"] == "gpt-4o"
        assert payload["total_tokens"] == 1234
        assert payload["latency_ms"] == 890
        assert payload["error_message"] is None
        assert "timestamp" in payload

    def test_failed_payload_uses_error_message(self) -> None:
        payload = build_analysis_payload(
            "analysis.failed",
            _fake_session(status=AnalysisStatus.FAILED),
            error_message="Provider timeout",
        )
        assert payload["error_message"] == "Provider timeout"

    def test_failed_payload_falls_back_to_session_error(self) -> None:
        payload = build_analysis_payload(
            "analysis.failed",
            _fake_session(
                status=AnalysisStatus.FAILED,
                error_message="stored error",
            ),
        )
        assert payload["error_message"] == "stored error"

    def test_none_fields_survive(self) -> None:
        payload = build_analysis_payload(
            "analysis.completed",
            _fake_session(
                analysis_type=None,
                status=None,
                provider_used=None,
                model_used=None,
                total_tokens=None,
                latency_ms=None,
            ),
        )
        assert payload["analysis_type"] is None
        assert payload["status"] is None
        assert payload["provider"] is None
        assert payload["total_tokens"] is None


class TestTestPayload:
    """The test ping payload must carry the ping event."""

    def test_shape(self) -> None:
        payload = new_test_payload()
        assert payload["event"] == "test.ping"
        assert payload["delivery_id"]
        assert "timestamp" in payload


class TestDeliverWebhook:
    """Delivery must sign, retry, and record outcomes."""

    async def test_success_records_delivered(
        self,
        db_session: AsyncSession,
        test_user: object,
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        delivery = await create_delivery(db_session, webhook.id)
        received: dict[str, object] = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            received["body"] = request.content
            received["headers"] = request.headers
            return httpx.Response(200)

        config = WebhookConfig(
            retry_attempts=3, retry_backoff_base_seconds=0
        )
        await deliver_webhook(
            db_session,
            delivery,
            webhook,
            config=config,
            transport=httpx.MockTransport(handler),
        )

        assert delivery.status == "delivered"
        assert delivery.attempts == 1
        assert delivery.last_status_code == 200
        assert delivery.last_error is None

        body = received["body"]
        assert isinstance(body, bytes)
        headers = received["headers"]
        assert isinstance(headers, httpx.Headers)
        assert headers.get(EVENT_HEADER) == "analysis.completed"
        assert headers.get(DELIVERY_HEADER) == str(delivery.id)
        assert headers.get(SIGNATURE_HEADER) == sign_payload(_SECRET, body)

    async def test_retries_then_succeeds(
        self,
        db_session: AsyncSession,
        test_user: object,
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        delivery = await create_delivery(db_session, webhook.id)
        call_count = 0

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(500)
            return httpx.Response(200)

        config = WebhookConfig(
            retry_attempts=3, retry_backoff_base_seconds=0
        )
        await deliver_webhook(
            db_session,
            delivery,
            webhook,
            config=config,
            transport=httpx.MockTransport(handler),
        )

        assert call_count == 2
        assert delivery.status == "delivered"
        assert delivery.attempts == 2

    async def test_exhausts_retries_and_records_failed(
        self,
        db_session: AsyncSession,
        test_user: object,
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        delivery = await create_delivery(db_session, webhook.id)

        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503)

        config = WebhookConfig(
            retry_attempts=3, retry_backoff_base_seconds=0
        )
        await deliver_webhook(
            db_session,
            delivery,
            webhook,
            config=config,
            transport=httpx.MockTransport(handler),
        )

        assert delivery.status == "failed"
        assert delivery.attempts == 3
        assert delivery.last_status_code == 503
        assert delivery.last_error == "HTTP 503"

    async def test_network_error_records_failed(
        self,
        db_session: AsyncSession,
        test_user: object,
    ) -> None:
        webhook = await create_webhook(db_session, test_user.id)
        delivery = await create_delivery(db_session, webhook.id)

        async def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        config = WebhookConfig(
            retry_attempts=1, retry_backoff_base_seconds=0
        )
        await deliver_webhook(
            db_session,
            delivery,
            webhook,
            config=config,
            transport=httpx.MockTransport(handler),
        )

        assert delivery.status == "failed"
        assert delivery.attempts == 1
        assert delivery.last_status_code is None
        assert delivery.last_error is not None
        assert "ConnectError" in delivery.last_error
