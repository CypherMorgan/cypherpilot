"""Comparison service — compare two analysis sessions."""

from __future__ import annotations

import json
from typing import Any

from structlog import get_logger

from app.infrastructure.models.analysis_session import AnalysisSession
from app.modules.comparison.schemas import (
    ComparisonResult,
    ScalarDiff,
    SectionDiff,
    SessionInfo,
)

_logger = get_logger(__name__)

# ── Section definitions per analysis type ──────────────────────
# Each key is a section name in output_data; value is the list field name.

_FAILURE_SECTIONS = [
    "root_causes",
    "suggested_fixes",
    "affected_components",
    "test_failures",
    "recommendations",
    "environment_details",
    "related_tests",
]

_REQUIREMENT_SECTIONS = [
    "functional_tests",
    "negative_tests",
    "boundary_tests",
    "edge_cases",
    "assumptions",
    "risks",
    "missing_requirements",
    "suggested_questions",
    "automation_candidates",
]

_API_TEST_SECTIONS: list[str] = []  # API test output is structurally different

_SECTION_MAP: dict[str, list[str]] = {
    "failure-analysis": _FAILURE_SECTIONS,
    "requirement-analysis": _REQUIREMENT_SECTIONS,
    "api-test-generation": _API_TEST_SECTIONS,
}


def _session_info(session: AnalysisSession) -> SessionInfo:
    """Extract lightweight info from an AnalysisSession."""
    return SessionInfo(
        id=str(session.id),
        title=session.title,
        analysis_type=session.analysis_type.value if session.analysis_type else "unknown",
        status=session.status.value if session.status else "unknown",
        provider=session.provider_used,
        model=session.model_used,
        total_tokens=session.total_tokens,
        latency_ms=session.latency_ms,
        created_at=session.created_at.isoformat() if session.created_at else None,
    )


def _compare_scalar(field: str, a: Any, b: Any) -> ScalarDiff:
    """Compare two scalar values."""
    return ScalarDiff(
        field=field,
        value_a=a,
        value_b=b,
        changed=str(a) != str(b),
    )


def _diff_list_by_id(
    list_a: list[dict[str, Any]],
    list_b: list[dict[str, Any]],
) -> SectionDiff:
    """Compare two lists of items by their 'id' field.

    Items without an 'id' are compared by content hash.
    """
    map_a = {item.get("id", json.dumps(item, sort_keys=True)): item for item in list_a}
    map_b = {item.get("id", json.dumps(item, sort_keys=True)): item for item in list_b}

    ids_a = set(map_a.keys())
    ids_b = set(map_b.keys())

    added = [map_b[i] for i in sorted(ids_b - ids_a)]
    removed = [map_a[i] for i in sorted(ids_a - ids_b)]

    changed = []
    unchanged = []
    for i in sorted(ids_a & ids_b):
        item_a = map_a[i]
        item_b = map_b[i]
        if item_a == item_b:
            unchanged.append(item_a)
        else:
            changed.append({"a": item_a, "b": item_b})

    return SectionDiff(
        section="",
        count_a=len(list_a),
        count_b=len(list_b),
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
    )


def _compare_sections(
    output_a: dict[str, Any],
    output_b: dict[str, Any],
    sections: list[str],
) -> list[SectionDiff]:
    """Compare named list sections between two outputs."""
    diffs = []
    for section in sections:
        list_a = output_a.get(section, [])
        list_b = output_b.get(section, [])

        if not isinstance(list_a, list):
            list_a = [list_a] if list_a else []
        if not isinstance(list_b, list):
            list_b = [list_b] if list_b else []

        diff = _diff_list_by_id(list_a, list_b)
        diff.section = section
        diffs.append(diff)

    return diffs


def compare_sessions(
    session_a: AnalysisSession,
    session_b: AnalysisSession,
) -> ComparisonResult:
    """Compare two analysis sessions and return structured diffs."""
    info_a = _session_info(session_a)
    info_b = _session_info(session_b)

    # Metadata diffs
    metadata_diffs = [
        _compare_scalar("provider", info_a.provider, info_b.provider),
        _compare_scalar("model", info_a.model, info_b.model),
        _compare_scalar("total_tokens", info_a.total_tokens, info_b.total_tokens),
        _compare_scalar("latency_ms", info_a.latency_ms, info_b.latency_ms),
    ]

    # Parse output data
    output_a = session_a.output_data or {}
    output_b = session_b.output_data or {}

    # Summary
    summary_a = output_a.get("summary") or output_a.get("input_summary")
    summary_b = output_b.get("summary") or output_b.get("input_summary")

    # Section diffs
    analysis_type = info_a.analysis_type
    sections = _SECTION_MAP.get(analysis_type, [])
    section_diffs = _compare_sections(output_a, output_b, sections)

    return ComparisonResult(
        session_a=info_a,
        session_b=info_b,
        metadata_diffs=metadata_diffs,
        summary_a=summary_a,
        summary_b=summary_b,
        section_diffs=section_diffs,
        raw_a=output_a,
        raw_b=output_b,
    )
