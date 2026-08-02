"""Tests for the Failure Analysis CSV exporter."""

from __future__ import annotations

import csv
import io

from app.modules.failure_analysis.exporters import CsvExporter, get_exporter
from app.modules.failure_analysis.models import (
    FailureAnalysisResult,
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
        assert "description" in header

    def test_export_rows_by_section(self, sample_analysis_result):
        """Every row should carry its source section label."""
        rows = _parse_rows(CsvExporter().export(sample_analysis_result))
        sections = [row["section"] for row in rows]
        assert sections.count("root_cause") == 2
        assert sections.count("suggested_fix") == 2
        assert sections.count("affected_component") == 2
        assert sections.count("test_failure") == 3
        assert sections.count("environment_detail") == 4
        assert sections.count("recommendation") == 3
        assert sections.count("related_test") == 3
        assert len(rows) == 19

    def test_export_contains_identifiers(self, sample_analysis_result):
        """Root cause and fix IDs should be present in the CSV."""
        rows = _parse_rows(CsvExporter().export(sample_analysis_result))
        root_causes = [row for row in rows if row["section"] == "root_cause"]
        assert [row["id"] for row in root_causes] == ["RC-001", "RC-002"]

        fixes = [row for row in rows if row["section"] == "suggested_fix"]
        assert [row["id"] for row in fixes] == ["FIX-001", "FIX-002"]

    def test_export_failure_fields(self, sample_analysis_result):
        """Test-failure rows should include the failure metadata columns."""
        rows = _parse_rows(CsvExporter().export(sample_analysis_result))
        failures = [row for row in rows if row["section"] == "test_failure"]
        assert failures[0]["test_file"] == "tests/integration/test_auth.py"
        assert failures[0]["duration_seconds"] == "1.2"

    def test_export_empty_sections(self):
        """Empty sections should produce only the header row."""
        result = FailureAnalysisResult(
            input_summary="Empty test.",
            summary="Empty summary.",
            root_causes=[],
            suggested_fixes=[],
            affected_components=[],
            test_failures=[],
            environment_details=[],
            recommendations=[],
            related_tests=[],
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
