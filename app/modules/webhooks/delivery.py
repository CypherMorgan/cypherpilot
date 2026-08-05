"""Webhook delivery — payload building, HMAC signing, and HTTP delivery.

Design notes:
- The body is canonicalized with ``json.dumps(sort_keys=True)`` so
  receivers can recompute the signature over the exact bytes sent.
- Signatures use HMAC-SHA256 and are delivered in the
  ``X-CypherPilot-Signature`` header as ``sha256=<hex>``.
- Delivery retries on network errors and non-2xx responses with linear
  backoff, up to ``retry_attempts``. An injectable ``transport`` keeps
  the logic fully testable without real network I/O.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.config import WebhookConfig
from app.modules.webhooks.models import Webhook, WebhookDelivery
from app.modules.webhooks.repository import WebhookDeliveryRepository

_logger = get_logger(__name__)

SIGNATURE_HEADER = "X-CypherPilot-Signature"
EVENT_HEADER = "X-CypherPilot-Event"
DELIVERY_HEADER = "X-CypherPilot-Delivery"


def canonical_body(payload: dict[str, Any]) -> bytes:
    """Serialize a payload deterministically for signing and sending."""
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sign_payload(secret: str, body: bytes) -> str:
    """Return ``sha256=<hex>`` HMAC signature over ``body`` using ``secret``."""
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def build_analysis_payload(
    event: str,
    session: Any,
    *,
    error_message: str | None = None,
) -> dict[str, Any]:
    """Build the standard webhook payload for an analysis session.

    ``session`` is an ORM ``AnalysisSession`` (or an object exposing the
    same attributes). Fields are read defensively so both the completed
    and failed paths produce a stable payload shape.
    """
    return {
        "event": event,
        "session_id": str(session.id),
        "analysis_type": (
            session.analysis_type.value if session.analysis_type is not None else None
        ),
        "title": session.title,
        "status": session.status.value if session.status is not None else None,
        "provider": session.provider_used,
        "model": session.model_used,
        "total_tokens": session.total_tokens,
        "latency_ms": session.latency_ms,
        "error_message": error_message or session.error_message,
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def deliver_webhook(
    db: AsyncSession,
    delivery: WebhookDelivery,
    webhook: Webhook,
    *,
    config: WebhookConfig,
    transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    """Deliver ``delivery`` to ``webhook.url`` with retries, recording outcomes.

    Uses ``transport`` when provided (tests inject ``httpx.MockTransport``);
    otherwise a default async client performs the real request.
    """
    repository = WebhookDeliveryRepository(db)
    body = canonical_body(delivery.payload or {})
    headers = {
        "Content-Type": "application/json",
        EVENT_HEADER: delivery.event,
        DELIVERY_HEADER: str(delivery.id),
        SIGNATURE_HEADER: sign_payload(webhook.secret, body),
    }

    attempts = 0
    last_status_code: int | None = None
    last_error: str | None = None

    try:
        async with httpx.AsyncClient(
            transport=transport,
            timeout=config.request_timeout_seconds,
        ) as client:
            for attempt in range(1, config.retry_attempts + 1):
                attempts = attempt
                try:
                    response = await client.post(
                        webhook.url,
                        content=body,
                        headers=headers,
                    )
                    last_status_code = response.status_code
                    if response.is_success:
                        await repository.record_attempt(
                            delivery,
                            attempts=attempt,
                            status="delivered",
                            last_status_code=response.status_code,
                        )
                        _logger.info(
                            "Webhook delivered",
                            webhook_id=str(webhook.id),
                            event_name=delivery.event,
                            status_code=response.status_code,
                        )
                        return
                    last_error = f"HTTP {response.status_code}"
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"[:500]
                _logger.warning(
                    "Webhook delivery attempt failed",
                    webhook_id=str(webhook.id),
                    event_name=delivery.event,
                    attempt=attempt,
                    error=last_error,
                )
                if attempt < config.retry_attempts:
                    await asyncio.sleep(config.retry_backoff_base_seconds * attempt)
    except Exception as exc:
        last_error = f"{type(exc).__name__}: {exc}"[:500]

    await repository.record_attempt(
        delivery,
        attempts=attempts,
        status="failed",
        last_status_code=last_status_code,
        last_error=last_error,
    )
    _logger.warning(
        "Webhook delivery failed",
        webhook_id=str(webhook.id),
        event_name=delivery.event,
        attempts=attempts,
        error=last_error,
    )


def new_test_payload() -> dict[str, Any]:
    """Payload for a manual test ping."""
    return {
        "event": "test.ping",
        "message": "CypherPilot test ping",
        "delivery_id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
    }
