"""Webhook API routes.

Endpoints:
  GET    /webhooks             — List webhooks (with latest delivery)
  POST   /webhooks             — Create a webhook
  GET    /webhooks/{id}        — Get one webhook
  PATCH  /webhooks/{id}        — Update a webhook
  DELETE /webhooks/{id}        — Delete a webhook
  POST   /webhooks/{id}/test   — Send a test ping
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import WebhookConfig
from app.infrastructure.database import get_db
from app.modules.auth.middleware import get_current_user
from app.modules.auth.models import User
from app.modules.webhooks.schemas import (
    WebhookCreate,
    WebhookUpdate,
)
from app.modules.webhooks.service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _get_webhook_config(request: Request) -> WebhookConfig:
    """Extract the webhook config from app state (set during lifespan)."""
    return request.app.state.config.webhooks  # type: ignore[no-any-return]


async def _get_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    config: Annotated[WebhookConfig, Depends(_get_webhook_config)],
) -> WebhookService:
    return WebhookService(session=db, config=config)


@router.get(
    "",
    summary="List webhooks",
    description="List webhooks for the current user, each with its latest delivery outcome.",
)
async def list_webhooks(
    service: Annotated[WebhookService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """List the authenticated user's webhooks."""
    result = await service.list_webhooks(user_id=user.id)
    return {"data": result.model_dump(mode="json")}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create webhook",
    description="Create a webhook endpoint for the current user.",
)
async def create_webhook(
    data: WebhookCreate,
    service: Annotated[WebhookService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Create a webhook (secret generated server-side when omitted)."""
    result = await service.create_webhook(user_id=user.id, data=data)
    return {"data": result.model_dump(mode="json")}


@router.get(
    "/{webhook_id}",
    summary="Get webhook",
    description="Get a single webhook owned by the current user.",
)
async def get_webhook(
    webhook_id: uuid.UUID,
    service: Annotated[WebhookService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Get one webhook."""
    result = await service.get_webhook(webhook_id=webhook_id, user_id=user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    return {"data": result.model_dump(mode="json")}


@router.patch(
    "/{webhook_id}",
    summary="Update webhook",
    description="Update a webhook owned by the current user.",
)
async def update_webhook(
    webhook_id: uuid.UUID,
    data: WebhookUpdate,
    service: Annotated[WebhookService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Update a webhook (name/url/events/active/secret regeneration)."""
    result = await service.update_webhook(
        webhook_id=webhook_id,
        user_id=user.id,
        data=data,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    return {"data": result.model_dump(mode="json")}


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete webhook",
    description="Delete a webhook owned by the current user.",
)
async def delete_webhook(
    webhook_id: uuid.UUID,
    service: Annotated[WebhookService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a webhook."""
    deleted = await service.delete_webhook(webhook_id=webhook_id, user_id=user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )


@router.post(
    "/{webhook_id}/test",
    summary="Test webhook",
    description="Send a test ping to the webhook URL and return the delivery outcome.",
)
async def test_webhook(
    webhook_id: uuid.UUID,
    service: Annotated[WebhookService, Depends(_get_service)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Send a test.ping event and return the outcome."""
    result = await service.test_webhook(webhook_id=webhook_id, user_id=user.id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    return {"data": result.model_dump(mode="json")}
