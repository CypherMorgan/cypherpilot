"""CSV exporter for Requirement Analysis results.

Produces a flattened spreadsheet with one row per test case, edge case,
risk, missing requirement, automation candidate, and list item. UTF-8
with a byte order mark so Excel opens non-ASCII content correctly.
"""

from __future__ import annotations

import csv
import io

from app.modules.requirement_analysis.exporters.base import AnalysisExporter
from app.modules.requirement_analysis.models import (
    RequirementAnalysisResult,
    TestCase,
)

# Union of all columns; each row only fills the ones relevant to it.
_FIELDS = [
    "section",
    "id",
    "title",
    "description",
    "priority",
    "preconditions",
    "steps",
    "expected_result",
    "tags",
    "boundary_value",
    "severity",
    "likelihood",
    "mitigation",
    "impact",
    "recommendation",
    "feasibility",
    "effort_estimate",
    "value_reason",
    "importance",
    "topic",
    "test_case_id",
    "value",
]

_UTF8_BOM = "\ufeff"


class CsvExporter(AnalysisExporter):
    """Exports analysis results as a flattened CSV spreadsheet."""

    def export(self, result: RequirementAnalysisResult) -> str:
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
    def _rows(result: RequirementAnalysisResult) -> list[dict[str, object]]:
        """Flatten the analysis result into CSV rows."""
        rows: list[dict[str, object]] = []

        for functional in result.functional_tests:
            rows.append(CsvExporter._test_row("functional_test", functional))
        for negative in result.negative_tests:
            rows.append(CsvExporter._test_row("negative_test", negative))
        for boundary in result.boundary_tests:
            row = CsvExporter._test_row("boundary_test", boundary)
            row["boundary_value"] = boundary.boundary_value
            rows.append(row)

        for edge in result.edge_cases:
            rows.append(
                {
                    "section": "edge_case",
                    "id": edge.id,
                    "title": edge.title,
                    "description": edge.description,
                    "impact": edge.impact,
                    "recommendation": edge.recommendation,
                }
            )

        for risk in result.risks:
            rows.append(
                {
                    "section": "risk",
                    "id": risk.id,
                    "description": risk.description,
                    "severity": risk.severity.value,
                    "likelihood": risk.likelihood,
                    "mitigation": risk.mitigation,
                }
            )

        for missing in result.missing_requirements:
            rows.append(
                {
                    "section": "missing_requirement",
                    "id": missing.id,
                    "topic": missing.topic,
                    "description": missing.description,
                    "importance": missing.importance.value,
                }
            )

        for candidate in result.automation_candidates:
            rows.append(
                {
                    "section": "automation_candidate",
                    "id": candidate.id,
                    "test_case_id": candidate.test_case_id,
                    "feasibility": candidate.feasibility.value,
                    "effort_estimate": candidate.effort_estimate,
                    "value_reason": candidate.value_reason,
                }
            )

        for assumption in result.assumptions:
            rows.append({"section": "assumption", "value": assumption})
        for question in result.suggested_questions:
            rows.append({"section": "suggested_question", "value": question})

        return rows

    @staticmethod
    def _test_row(section: str, test: TestCase) -> dict[str, object]:
        """Flatten a test-case model into a CSV row."""
        return {
            "section": section,
            "id": test.id,
            "title": test.title,
            "description": test.description,
            "priority": test.priority.value,
            "preconditions": "; ".join(test.preconditions),
            "steps": "; ".join(test.steps),
            "expected_result": test.expected_result,
            "tags": ", ".join(test.tags),
        }
