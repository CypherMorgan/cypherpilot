"""CSV exporter for Failure Analysis results.

Produces a flattened spreadsheet with one row per root cause, fix,
affected component, test failure, and list item. UTF-8 with a byte
order mark so Excel opens non-ASCII content correctly.
"""

from __future__ import annotations

import csv
import io

from app.modules.failure_analysis.exporters.base import FailureExporter
from app.modules.failure_analysis.models import FailureAnalysisResult

# Union of all columns; each row only fills the ones relevant to it.
_FIELDS = [
    "section",
    "id",
    "title",
    "description",
    "category",
    "severity",
    "priority",
    "root_cause_id",
    "failing_file",
    "failing_line",
    "error_message",
    "effort_estimate",
    "code_example",
    "related_files",
    "impact",
    "related_root_causes",
    "test_name",
    "test_file",
    "duration_seconds",
    "retry_count",
    "value",
]

_UTF8_BOM = "\ufeff"


class CsvExporter(FailureExporter):
    """Exports analysis results as a flattened CSV spreadsheet."""

    def export(self, result: FailureAnalysisResult) -> str:
        """Convert the analysis result to CSV (UTF-8 with BOM)."""
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=_FIELDS,
            lineterminator="\r\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in self._rows(result):
            writer.writerow(row)
        return _UTF8_BOM + buffer.getvalue()

    @staticmethod
    def _rows(result: FailureAnalysisResult) -> list[dict[str, object]]:
        """Flatten the analysis result into CSV rows."""
        rows: list[dict[str, object]] = []

        for rc in result.root_causes:
            rows.append(
                {
                    "section": "root_cause",
                    "id": rc.id,
                    "title": rc.title,
                    "description": rc.description,
                    "category": rc.category.value,
                    "severity": rc.severity.value,
                    "failing_file": rc.failing_file,
                    "failing_line": rc.failing_line,
                    "error_message": rc.error_message,
                }
            )

        for fix in result.suggested_fixes:
            rows.append(
                {
                    "section": "suggested_fix",
                    "id": fix.id,
                    "title": fix.description,
                    "root_cause_id": fix.root_cause_id,
                    "priority": fix.priority.value,
                    "effort_estimate": fix.effort_estimate,
                    "code_example": fix.code_example,
                    "related_files": ", ".join(fix.related_files),
                }
            )

        for component in result.affected_components:
            rows.append(
                {
                    "section": "affected_component",
                    "id": component.id,
                    "title": component.name,
                    "impact": component.impact,
                    "related_root_causes": ", ".join(
                        component.related_root_causes
                    ),
                }
            )

        for failure in result.test_failures:
            rows.append(
                {
                    "section": "test_failure",
                    "id": failure.id,
                    "title": failure.test_name,
                    "test_file": failure.test_file,
                    "error_message": failure.error_message,
                    "duration_seconds": failure.duration_seconds,
                    "retry_count": failure.retry_count,
                }
            )

        for detail in result.environment_details:
            rows.append({"section": "environment_detail", "value": detail})
        for recommendation in result.recommendations:
            rows.append({"section": "recommendation", "value": recommendation})
        for test in result.related_tests:
            rows.append({"section": "related_test", "value": test})

        return rows
