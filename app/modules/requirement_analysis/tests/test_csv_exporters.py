"""Tests for the Requirement Analysis CSV exporter."""

from __future__ import annotations

import csv
import io

from app.modules.requirement_analysis.exporters import CsvExporter, get_exporter
from app.modules.requirement_analysis.models import (
    PriorityAssessment,
    PriorityLevel,
    RequirementAnalysisResult,
)

_UTF8_BOM = "\ufeff"


def _parse_rows(output: str) -> list[dict[str, str]]:
    """Parse CSV output (BOM stripped) into a list of row dicts."""
    reader = csv.DictReader(io.StringIO(output.lstrip(_UTF8_BOM)))
    return list(reader)


class TestCsvExporter:
    """Tests for the CSV exporter."""

    def test_export_starts_with_bom(self, sample_analysis_result):
        """Output should start with a UTF-8 BOM for Excel compatibility."""
        output = CsvExporter().export(sample_analysis_result)
        assert output.startswith(_UTF8_BOM)

    def test_export_has_header_row(self, sample_analysis_result):
        """The first data row should be the header with expected columns."""
        output = CsvExporter().export(sample_analysis_result)
        reader = csv.reader(io.StringIO(output.lstrip(_UTF8_BOM)))
        header = next(reader)
        assert header[0] == "section"
        assert "id" in header
        assert "title" in header
        assert "priority" in header

    def test_export_rows_by_section(self, sample_analysis_result):
        """Every row should carry its source section label."""
        rows = _parse_rows(CsvExporter().export(sample_analysis_result))
        sections = [row["section"] for row in rows]
        assert sections.count("functional_test") == 2
        assert sections.count("negative_test") == 1
        assert sections.count("boundary_test") == 1
        assert sections.count("edge_case") == 1
        assert sections.count("assumption") == 2
        assert sections.count("risk") == 1
        assert sections.count("missing_requirement") == 1
        assert sections.count("suggested_question") == 2
        assert sections.count("automation_candidate") == 1
        assert len(rows) == 12

    def test_export_contains_test_ids(self, sample_analysis_result):
        """Test case IDs should be present in the CSV."""
        rows = _parse_rows(CsvExporter().export(sample_analysis_result))
        functional = [
            row for row in rows if row["section"] == "functional_test"
        ]
        assert [row["id"] for row in functional] == [
            "TC-FUNC-001",
            "TC-FUNC-002",
        ]

    def test_export_boundary_value(self, sample_analysis_result):
        """Boundary test rows should include the boundary value."""
        rows = _parse_rows(CsvExporter().export(sample_analysis_result))
        boundary = [row for row in rows if row["section"] == "boundary_test"]
        assert boundary[0]["boundary_value"] == "128 characters"

    def test_export_risk_severity(self, sample_analysis_result):
        """Risk rows should include severity and mitigation."""
        rows = _parse_rows(CsvExporter().export(sample_analysis_result))
        risk = [row for row in rows if row["section"] == "risk"]
        assert risk[0]["severity"] == "critical"
        assert "rate limiting" in risk[0]["mitigation"]

    def test_export_empty_sections(self):
        """Empty sections should produce only the header row."""
        result = RequirementAnalysisResult(
            input_summary="Empty test.",
            functional_tests=[],
            negative_tests=[],
            boundary_tests=[],
            edge_cases=[],
            assumptions=[],
            risks=[],
            missing_requirements=[],
            suggested_questions=[],
            automation_candidates=[],
            priority_assessment=PriorityAssessment(
                overall_priority=PriorityLevel.MEDIUM,
                critical_path_items=[],
                quick_wins=[],
                reasoning="Empty test.",
            ),
        )
        output = CsvExporter().export(result)
        rows = _parse_rows(output)
        assert rows == []


class TestGetExporterCsv:
    """Tests for the get_exporter factory with CSV."""

    def test_get_csv_exporter(self):
        """Should return a CsvExporter for 'csv'."""
        assert isinstance(get_exporter("csv"), CsvExporter)

    def test_csv_case_insensitive(self):
        """CSV format name should be case-insensitive."""
        assert isinstance(get_exporter("CSV"), CsvExporter)
