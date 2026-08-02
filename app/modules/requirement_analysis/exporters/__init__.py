"""Export layer for Requirement Analysis.

Provides abstract base class and concrete implementations
(Markdown, JSON, CSV) for exporting analysis results.

Usage::

    from app.modules.requirement_analysis.exporters import (
        MarkdownExporter, JsonExporter, CsvExporter, get_exporter
    )

    # Direct instantiation
    md = MarkdownExporter()
    markdown_output = md.export(result)

    # Via factory
    exporter = get_exporter("markdown")
    output = exporter.export(result)
"""

from app.modules.requirement_analysis.exporters.base import AnalysisExporter
from app.modules.requirement_analysis.exporters.csv_ import CsvExporter
from app.modules.requirement_analysis.exporters.json_ import JsonExporter
from app.modules.requirement_analysis.exporters.markdown import MarkdownExporter

_EXPORTERS: dict[str, type[AnalysisExporter]] = {
    "markdown": MarkdownExporter,
    "json": JsonExporter,
    "csv": CsvExporter,
}


def get_exporter(format_name: str) -> AnalysisExporter:
    """Return an exporter instance for the given format name.

    Args:
        format_name: ``"markdown"``, ``"json"`` or ``"csv"``.

    Returns:
        An ``AnalysisExporter`` instance.

    Raises:
        ValueError: If the format is not supported.
    """
    cls = _EXPORTERS.get(format_name.lower())
    if cls is None:
        supported = ", ".join(_EXPORTERS)
        raise ValueError(f"Unsupported export format: '{format_name}'. Supported: {supported}")
    return cls()


__all__ = [
    "AnalysisExporter",
    "CsvExporter",
    "JsonExporter",
    "MarkdownExporter",
    "get_exporter",
]
