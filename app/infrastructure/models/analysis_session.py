"""AnalysisSession ORM model.

Represents a single AI-powered analysis session — the root entity of
the CypherPilot domain.  Every analysis (requirement analysis, API test
generation, failure analysis) is captured as a session.

Schema (evolved for Phase 3 — Requirement Analysis)::

    analysis_sessions
    ─────────────────
    id              UUID PRIMARY KEY
    title           VARCHAR
    type            VARCHAR NOT NULL
    status          VARCHAR NOT NULL DEFAULT 'pending'
    input_source_type   VARCHAR          — type of input
    input_content       TEXT             — raw input text
    input_filename      VARCHAR          — original filename if uploaded
    output_data         JSONB            — full structured output
    output_format       VARCHAR          — requested export format
    provider_used       VARCHAR          — AI provider name
    model_used          VARCHAR          — AI model name
    prompt_tokens       INTEGER          — input token count
    completion_tokens   INTEGER          — output token count
    total_tokens        INTEGER          — total token count
    latency_ms          INTEGER          — AI call duration
    error_message       TEXT             — failure reason if status=FAILED
    config              JSONB
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models import AnalysisStatus, AnalysisType
from app.infrastructure.database import Base
from app.infrastructure.models.base import TimestampMixin, UUIDMixin


class AnalysisSession(Base, UUIDMixin, TimestampMixin):
    """An analysis session — root aggregate of the CypherPilot domain."""

    __tablename__ = "analysis_sessions"

    # ── Ownership (nullable for backward compatibility) ──────────

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    team_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    analysis_type: Mapped[AnalysisType] = mapped_column(
        Enum(
            AnalysisType,
            name="analysis_type_enum",
            create_constraint=True,
            values_callable=lambda cls: [m.value for m in cls],
        ),
        nullable=False,
    )

    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(
            AnalysisStatus,
            name="analysis_status_enum",
            create_constraint=True,
            values_callable=lambda cls: [m.value for m in cls],
        ),
        nullable=False,
        default=AnalysisStatus.PENDING,
    )

    # ── Input fields ────────────────────────────────────────────

    input_source_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    input_content: Mapped[str | None] = mapped_column(
        Text(),
        nullable=True,
        default=None,
    )

    input_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )

    # ── Output fields ───────────────────────────────────────────

    output_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON(),
        nullable=True,
        default=None,
    )

    output_format: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        default=None,
    )

    # ── AI provider tracking ────────────────────────────────────

    provider_used: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    model_used: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )

    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer(),
        nullable=True,
        default=None,
    )

    completion_tokens: Mapped[int | None] = mapped_column(
        Integer(),
        nullable=True,
        default=None,
    )

    total_tokens: Mapped[int | None] = mapped_column(
        Integer(),
        nullable=True,
        default=None,
    )

    latency_ms: Mapped[int | None] = mapped_column(
        Integer(),
        nullable=True,
        default=None,
    )

    # ── Error tracking ──────────────────────────────────────────

    error_message: Mapped[str | None] = mapped_column(
        Text(),
        nullable=True,
        default=None,
    )

    # ── Config (generic extensibility) ──────────────────────────

    config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON(),
        nullable=True,
        default=None,
    )
