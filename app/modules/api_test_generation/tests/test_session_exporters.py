"""Tests for API Test Generation session-level exporters."""

from __future__ import annotations

import csv
import io
import json

import pytest

from app.modules.api_test_generation.exporters.session_exporter import (
    CsvSessionExporter,
    JsonSessionExporter,
    MarkdownSessionExporter,
    get_session_exporter,
)

_UTF8_BOM = "\ufeff"


@pytest.fixture
def sample_output_data() -> dict:
    """A stored session ``output_data`` dict like the repository returns."""
    return {
        "spec_title": "Pet Store API",
        "spec_version": "1.0.0",
        "endpoint_count": 3,
        "files": [
            {"filename": "test_pets.py", "content": "import pytest"},
            {"filename": "conftest.py", "content": "import asyncio"},
        ],
        "endpoints": [
            {"method": "get", "path": "/pets", "tests_generated": 2},
            {"method": "post", "path": "/pets", "tests_generated": 1},
            {"method": "get", "path": "/pets/{petId}", "tests_generated": 2},
        ],
        "zip_content": "UEsDBBQACAgIAAAAAAAAAAAAAAA=",
    }


class TestMarkdownSessionExporter:
    """Tests for the Markdown session exporter."""

    def test_export_title(self, sample_output_data):
        """Output should include the spec title as the document heading."""
        output = MarkdownSessionExporter().export(sample_output_data)
        assert "# Pet Store API" in output

    def test_export_endpoint_table(self, sample_output_data):
        """Output should include the endpoints table with methods and paths."""
        output = MarkdownSessionExporter().export(sample_output_data)
        assert "## Endpoints" in output
        assert "| GET |" not in output  # methods are lowercase as stored
        assert "`/pets`" in output
        assert "`/pets/{petId}`" in output

    def test_export_generated_files(self, sample_output_data):
        """Output should list the generated files."""
        output = MarkdownSessionExporter().export(sample_output_data)
        assert "## Generated Files" in output
        assert "`test_pets.py`" in output
        assert "`conftest.py`" in output

    def test_export_no_zip_content(self, sample_output_data):
        """The ZIP payload should never appear in a Markdown export."""
        output = MarkdownSessionExporter().export(sample_output_data)
        assert "UEsDB" not in output

    def test_export_empty_endpoints(self):
        """A session with no endpoints should show a placeholder."""
        output = MarkdownSessionExporter().export(
            {"spec_title": "Empty", "endpoint_count": 0, "endpoints": [], "files": []}
        )
        assert "_No endpoints in the spec._" in output
        assert "_No files were generated._" in output


class TestJsonSessionExporter:
    """Tests for the JSON session exporter."""

    def test_export_valid_json(self, sample_output_data):
        """Output should be valid JSON."""
        output = JsonSessionExporter().export(sample_output_data)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_export_excludes_zip_content(self, sample_output_data):
        """The ZIP payload should be excluded from the JSON export."""
        parsed = json.loads(JsonSessionExporter().export(sample_output_data))
        assert "zip_content" not in parsed

    def test_export_preserves_endpoints(self, sample_output_data):
        """Endpoint summary should be preserved in the JSON export."""
        parsed = json.loads(JsonSessionExporter().export(sample_output_data))
        assert parsed["spec_title"] == "Pet Store API"
        assert len(parsed["endpoints"]) == 3


class TestCsvSessionExporter:
    """Tests for the CSV session exporter."""

    def test_export_starts_with_bom(self, sample_output_data):
        """Output should start with a UTF-8 BOM for Excel compatibility."""
        output = CsvSessionExporter().export(sample_output_data)
        assert output.startswith(_UTF8_BOM)

    def test_export_rows(self, sample_output_data):
        """Each endpoint should be a row with method, path, and count."""
        reader = csv.reader(
            io.StringIO(
                CsvSessionExporter().export(sample_output_data).lstrip(_UTF8_BOM)
            )
        )
        rows = list(reader)
        assert rows[0] == ["method", "path", "tests_generated"]
        assert rows[1] == ["get", "/pets", "2"]
        assert len(rows) == 4

    def test_export_empty_endpoints(self):
        """A session with no endpoints should have just the header row."""
        output = CsvSessionExporter().export(
            {"endpoints": [], "files": [], "spec_title": "Empty"}
        )
        rows = list(
            csv.reader(io.StringIO(output.lstrip(_UTF8_BOM)))
        )
        assert rows == [["method", "path", "tests_generated"]]


class TestGetSessionExporter:
    """Tests for the get_session_exporter factory."""

    def test_get_markdown(self):
        """Should return a MarkdownSessionExporter for 'markdown'."""
        assert isinstance(get_session_exporter("markdown"), MarkdownSessionExporter)

    def test_get_json(self):
        """Should return a JsonSessionExporter for 'json'."""
        assert isinstance(get_session_exporter("json"), JsonSessionExporter)

    def test_get_csv(self):
        """Should return a CsvSessionExporter for 'csv'."""
        assert isinstance(get_session_exporter("csv"), CsvSessionExporter)

    def test_case_insensitive(self):
        """Format name should be case-insensitive."""
        assert isinstance(get_session_exporter("CSV"), CsvSessionExporter)

    def test_unsupported_format_raises(self):
        """Unsupported format should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            get_session_exporter("pdf")
