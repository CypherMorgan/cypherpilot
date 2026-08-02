"""Export layer for Failure Analysis.

Provides abstract base class and concrete implementations
(Markdown, JSON, CSV) for exporting analysis results.

Usage::

    from app.modules.failure_analysis.exporters import (
        MarkdownExporter, JsonExporter, CsvExporter, get_exporter
    )

    # Direct instantiation
    md = MarkdownExporter()
    markdown_output = md.export(result)

    # Via factory
    exporter = get_exporter("markdown")
    output = exporter.export(result)
"""

from app.modules.failure_analysis.exporters.base import FailureExporter
from app.modules.failure_analysis.exporters.csv_ import CsvExporter
from app.modules.failure_analysis.exporters.json_ import JsonExporter
from app.modules.failure_analysis.exporters.markdown import MarkdownExporter

_EXPORTERS: dict[str, type[FailureExporter]] = {
    "markdown": MarkdownExporter,
    "json": JsonExporter,
    "csv": CsvExporter,
}


def get_exporter(format_name: str) -> FailureExporter:
    """Return an exporter instance for the given format name.

    Args:
        format_name: ``"markdown"``, ``"json"`` or ``"csv"``.

    Returns:
        A ``FailureExporter`` instance.

    Raises:
        ValueError: If the format is not supported.
    """
    cls = _EXPORTERS.get(format_name.lower())
    if cls is None:
        supported = ", ".join(_EXPORTERS)
        raise ValueError(f"Unsupported export format: '{format_name}'. Supported: {supported}")
    return cls()


__all__ = [
    "CsvExporter",
    "FailureExporter",
    "JsonExporter",
    "MarkdownExporter",
    "get_exporter",
]
