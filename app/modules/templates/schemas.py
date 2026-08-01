"""Pydantic schemas for analysis template request/response bodies."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ── Supported source types ──────────────────────────────────────
# Keep in sync with the InputSourceType enum used by Failure Analysis.

SOURCE_TYPES = ("plain_text", "markdown", "ci_log", "stack_trace")

# ── Request schemas ─────────────────────────────────────────────


class CreateTemplateRequest(BaseModel):
    """POST /templates"""

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Template name",
    )
    description: str | None = Field(
        None,
        max_length=500,
        description="Optional template description",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=100_000,
        description="The failure output text this template captures",
    )
    source_type: str = Field(
        "plain_text",
        description="Input format: plain_text, markdown, ci_log, stack_trace",
    )


class UpdateTemplateRequest(BaseModel):
    """PATCH /templates/{template_id}"""

    name: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        description="New template name",
    )
    description: str | None = Field(
        None,
        max_length=500,
        description="New template description",
    )
    content: str | None = Field(
        None,
        min_length=1,
        max_length=100_000,
        description="New failure output text",
    )
    source_type: str | None = Field(
        None,
        description="New input format: plain_text, markdown, ci_log, stack_trace",
    )


# ── Response schemas ────────────────────────────────────────────


class TemplateResponse(BaseModel):
    """Public template representation."""

    id: uuid.UUID
    name: str
    description: str | None
    content: str
    source_type: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TemplateListResponse(BaseModel):
    """Paginated template list."""

    items: list[TemplateResponse]
    total: int
    page: int
    page_size: int
