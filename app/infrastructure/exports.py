"""Shared helpers for session export endpoints.

Provides a common ``ExportFile`` payload, media-type lookup, and
download-filename construction used by every module's export endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

ExportFormat = Literal["markdown", "json", "csv"]

_EXPORT_EXTENSIONS: dict[str, str] = {
    "markdown": "md",
    "json": "json",
    "csv": "csv",
}

_EXPORT_MEDIA_TYPES: dict[str, str] = {
    "markdown": "text/markdown; charset=utf-8",
    "json": "application/json; charset=utf-8",
    "csv": "text/csv; charset=utf-8",
}


@dataclass(frozen=True)
class ExportFile:
    """A serialized export payload ready to be downloaded."""

    content: str
    media_type: str
    filename: str


def export_filename(prefix: str, session_id: UUID, format_name: str) -> str:
    """Build a download filename such as ``failure-analysis-<id>.md``."""
    extension = _EXPORT_EXTENSIONS.get(format_name, "txt")
    return f"{prefix}-{session_id}.{extension}"


def export_media_type(format_name: str) -> str:
    """Return the HTTP media type for an export format."""
    return _EXPORT_MEDIA_TYPES.get(format_name, "text/plain; charset=utf-8")
