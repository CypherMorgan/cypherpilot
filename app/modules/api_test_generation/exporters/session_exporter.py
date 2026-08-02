"""Session-level exporters for API Test Generation.

Exports a stored generation session (spec metadata + endpoint summary)
as Markdown, JSON, or CSV. Distinct from the pytest file generators in
``pytest_generator.py``, which build the downloadable test archive.

The base64 ``zip_content`` payload is always excluded from these
session-level exports; use the ZIP download endpoint for the archive.
"""

from __future__ import annotations

import csv
import io
import json
from abc import ABC, abstractmethod
from typing import Any

_UTF8_BOM = "\ufeff"


class SessionExporter(ABC):
    """Abstract base for exporting a stored generation session."""

    @abstractmethod
    def export(self, output_data: dict[str, Any]) -> str:
        """Convert the session's output data to the target format.

        Args:
            output_data: The ``AnalysisSession.output_data`` dict.

        Returns:
            The session as a formatted string.
        """


class MarkdownSessionExporter(SessionExporter):
    """Exports a session summary as a Markdown document."""

    def export(self, output_data: dict[str, Any]) -> str:
        """Convert the session's output data to Markdown."""
        lines: list[str] = []
        title = output_data.get("spec_title") or "API Test Generation Report"
        lines.append(f"# {title}")
        lines.append("")
        if output_data.get("spec_version"):
            lines.append(f"**Spec version:** {output_data['spec_version']}")
        lines.append(f"**Endpoints processed:** {output_data.get('endpoint_count', 0)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        endpoints = output_data.get("endpoints", [])
        lines.append("## Endpoints")
        lines.append("")
        lines.append("| Method | Path | Tests Generated |")
        lines.append("|--------|------|-----------------|")
        for endpoint in endpoints:
            lines.append(
                f"| {endpoint.get('method', '')} | `{endpoint.get('path', '')}` | "
                f"{endpoint.get('tests_generated', 0)} |"
            )
        if not endpoints:
            lines.append("_No endpoints in the spec._")
        lines.append("")

        files = output_data.get("files", [])
        lines.append("## Generated Files")
        lines.append("")
        for file_meta in files:
            lines.append(f"- `{file_meta.get('filename', '')}`")
        if not files:
            lines.append("_No files were generated._")

        return "\n".join(lines)


class JsonSessionExporter(SessionExporter):
    """Exports a session's output data as pretty-printed JSON."""

    def export(self, output_data: dict[str, Any]) -> str:
        """Convert the session's output data to formatted JSON."""
        payload = {
            key: value for key, value in output_data.items() if key != "zip_content"
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)


class CsvSessionExporter(SessionExporter):
    """Exports a session's endpoint summary as CSV (UTF-8 with BOM)."""

    def export(self, output_data: dict[str, Any]) -> str:
        """Convert the session's endpoint summary to CSV."""
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\r\n")
        writer.writerow(["method", "path", "tests_generated"])
        for endpoint in output_data.get("endpoints", []):
            writer.writerow(
                [
                    endpoint.get("method", ""),
                    endpoint.get("path", ""),
                    endpoint.get("tests_generated", 0),
                ]
            )
        return _UTF8_BOM + buffer.getvalue()


_SESSION_EXPORTERS: dict[str, type[SessionExporter]] = {
    "markdown": MarkdownSessionExporter,
    "json": JsonSessionExporter,
    "csv": CsvSessionExporter,
}


def get_session_exporter(format_name: str) -> SessionExporter:
    """Return a session exporter instance for the given format name.

    Args:
        format_name: ``"markdown"``, ``"json"`` or ``"csv"``.

    Returns:
        A ``SessionExporter`` instance.

    Raises:
        ValueError: If the format is not supported.
    """
    cls = _SESSION_EXPORTERS.get(format_name.lower())
    if cls is None:
        supported = ", ".join(_SESSION_EXPORTERS)
        raise ValueError(
            f"Unsupported export format: '{format_name}'. Supported: {supported}"
        )
    return cls()
