"""Webhook API schemas (request/response models)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

# ── Supported event names ─────────────────────────────────────────

EVENT_ANALYSIS_COMPLETED = "analysis.completed"
EVENT_ANALYSIS_FAILED = "analysis.failed"
EVENT_TEST_PING = "test.ping"

ALLOWED_EVENTS: frozenset[str] = frozenset(
    {
        EVENT_ANALYSIS_COMPLETED,
        EVENT_ANALYSIS_FAILED,
    }
)

SECRET_PREFIX = "whsec_"
SECRET_LENGTH = 32
MASK_SUFFIX = 4


def mask_secret(secret: str) -> str:
    """Return a display-safe masked form of a webhook secret."""
    if len(secret) <= MASK_SUFFIX:
        return "****"
    return f"{SECRET_PREFIX}****{secret[-MASK_SUFFIX:]}"


# ── Requests ──────────────────────────────────────────────────────


class WebhookCreate(BaseModel):
    """Payload for creating a webhook."""

    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=500)
    events: list[str] = Field(min_length=1, max_length=10)
    secret: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return value

    @field_validator("events")
    @classmethod
    def _validate_events(cls, value: list[str]) -> list[str]:
        normalized = sorted({event.strip() for event in value if event.strip()})
        invalid = [event for event in normalized if event not in ALLOWED_EVENTS]
        if invalid:
            raise ValueError(
                f"Unsupported event(s): {', '.join(sorted(invalid))}. "
                f"Allowed: {', '.join(sorted(ALLOWED_EVENTS))}"
            )
        if not normalized:
            raise ValueError("At least one event is required")
        return normalized


class WebhookUpdate(BaseModel):
    """Payload for updating a webhook (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    url: str | None = Field(default=None, min_length=1, max_length=500)
    events: list[str] | None = Field(default=None, min_length=1, max_length=10)
    is_active: bool | None = None
    regenerate_secret: bool = False

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return value

    @field_validator("events")
    @classmethod
    def _validate_events(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized = sorted({event.strip() for event in value if event.strip()})
        invalid = [event for event in normalized if event not in ALLOWED_EVENTS]
        if invalid:
            raise ValueError(
                f"Unsupported event(s): {', '.join(sorted(invalid))}. "
                f"Allowed: {', '.join(sorted(ALLOWED_EVENTS))}"
            )
        if not normalized:
            raise ValueError("At least one event is required")
        return normalized

    @model_validator(mode="after")
    def _require_change(self) -> WebhookUpdate:
        if (
            self.name is None
            and self.url is None
            and self.events is None
            and self.is_active is None
            and not self.regenerate_secret
        ):
            raise ValueError("At least one field must be provided")
        return self


# ── Responses ─────────────────────────────────────────────────────


class DeliverySummary(BaseModel):
    """Latest delivery outcome for a webhook (denormalized for lists)."""

    delivery_id: uuid.UUID
    event: str
    status: str
    attempts: int
    last_status_code: int | None = None
    last_error: str | None = None
    created_at: datetime


class WebhookResponse(BaseModel):
    """Webhook detail response (secret is masked)."""

    id: uuid.UUID
    name: str
    url: str
    events: list[str]
    secret_masked: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_delivery: DeliverySummary | None = None


class WebhookListResponse(BaseModel):
    """Paginated webhook list response."""

    items: list[WebhookResponse]
    total: int


class WebhookTestResult(BaseModel):
    """Result of a test-ping delivery."""

    delivery_id: uuid.UUID
    event: str
    status: str
    attempts: int
    last_status_code: int | None = None
    last_error: str | None = None
