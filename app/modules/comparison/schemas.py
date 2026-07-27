"""Pydantic schemas for session comparison."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ── Session info ───────────────────────────────────────────────


class SessionInfo(BaseModel):
    """Lightweight session metadata for comparison headers."""

    id: str
    title: str | None = None
    analysis_type: str
    status: str
    provider: str | None = None
    model: str | None = None
    total_tokens: int | None = None
    latency_ms: int | None = None
    created_at: str | None = None


# ── Diff types ─────────────────────────────────────────────────


class ScalarDiff(BaseModel):
    """Diff for a single scalar field (string, number, etc.)."""

    field: str
    value_a: Any = None
    value_b: Any = None
    changed: bool = False


class ItemStatus(BaseModel):
    """Status of a list item in the comparison."""

    status: str = Field(
        description="'added', 'removed', 'changed', or 'unchanged'"
    )
    item: dict[str, Any] = Field(description="The item data")


class SectionDiff(BaseModel):
    """Diff for a named list section (e.g. root_causes, functional_tests)."""

    section: str
    count_a: int = 0
    count_b: int = 0
    added: list[dict[str, Any]] = Field(default_factory=list)
    removed: list[dict[str, Any]] = Field(default_factory=list)
    changed: list[dict[str, Any]] = Field(default_factory=list)
    unchanged: list[dict[str, Any]] = Field(default_factory=list)


# ── Root comparison result ────────────────────────────────────


class ComparisonResult(BaseModel):
    """Full comparison result between two analysis sessions."""

    session_a: SessionInfo
    session_b: SessionInfo

    # Metadata comparison
    metadata_diffs: list[ScalarDiff] = Field(default_factory=list)

    # Summary comparison
    summary_a: str | None = None
    summary_b: str | None = None

    # Content section diffs (module-specific)
    section_diffs: list[SectionDiff] = Field(default_factory=list)

    # Raw output data for reference
    raw_a: dict[str, Any] | None = None
    raw_b: dict[str, Any] | None = None


class CompareRequest(BaseModel):
    """POST /compare request body."""

    session_id_a: str = Field(description="First session ID to compare")
    session_id_b: str = Field(description="Second session ID to compare")
