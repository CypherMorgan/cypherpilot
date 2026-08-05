"""Webhook helper for services.

Provides a non-blocking ``fire_webhooks`` function that can be called
from any analysis service when a session completes or fails.  Errors are
swallowed — webhook delivery never breaks the main flow.
"""

from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import WebhookConfig
from app.modules.webhooks.service import WebhookService


async def fire_webhooks(
    db: AsyncSession,
    *,
    user_id: Any,
    event: str,
    payload: dict[str, Any],
    session_id: Any = None,
    config: WebhookConfig | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> None:
    """Deliver ``event`` to the user's matching webhooks. Best-effort."""
    if not user_id:
        return
    try:
        service = WebhookService(
            session=db,
            config=config,
            transport=transport,
        )
        await service.fire_event(
            user_id=user_id,
            event=event,
            payload=payload,
            session_id=session_id,
        )
    except Exception:
        # Webhooks are best-effort — never fail the main request
        pass
