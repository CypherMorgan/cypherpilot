"""Pydantic schemas for Automation Failure Analysis.

Every analysis produces a ``FailureAnalysisResult`` with structured
sections for root cause, stack trace analysis, suggested fixes,
and affected components.

These models are the contract between the AI response parser, the
service layer, and the export layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

# ── Enums ─────────────────────────────────────────────────────────

class FailureSeverity(StrEnum):
    """Severity level for identified failures."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FailureCategory(StrEnum):
    """Category of the identified failure."""

    ASSERTION_ERROR = "assertion_error"
    TIMEOUT = "timeout"
    ENVIRONMENT = "environment"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    DATA_ISSUE = "data_issue"
    PERMISSION = "permission"
    NETWORK = "network"
    COMPILATION = "compilation"
    UNKNOWN = "unknown"


class FixPriority(StrEnum):
    """Priority level for suggested fixes."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InputSourceType(StrEnum):
    """Supported input source types."""

    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    CI_LOG = "ci_log"
    STACK_TRACE = "stack_trace"


# ── Input schema ──────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    """Input payload for the failure analysis endpoint."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=100_000,
        description="The failure output to analyze (CI log, stack trace, error message, etc.).",
    )
    source_type: InputSourceType = Field(
        default=InputSourceType.PLAIN_TEXT,
        description="The format of the input content.",
    )
    title: str | None = Field(
        default=None,
        max_length=255,
        description="Optional title for the analysis session.",
    )
    context: str | None = Field(
        default=None,
        max_length=10_000,
        description="Optional additional context (e.g. test framework, CI platform, language).",
    )
    output_format: str = Field(
        default="json",
        description="Desired output format: 'json', 'markdown', or 'both'.",
    )


# ── Batch Analysis ────────────────────────────────────────────────


class BatchInputItem(BaseModel):
    """A single input within a batch analysis request."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=100_000,
        description="The failure output to analyze.",
    )
    source_type: InputSourceType = Field(
        default=InputSourceType.PLAIN_TEXT,
        description="The format of the input content.",
    )
    title: str | None = Field(
        default=None,
        max_length=255,
        description="Optional title for this analysis.",
    )
    context: str | None = Field(
        default=None,
        max_length=10_000,
        description="Optional additional context.",
    )


class BatchAnalysisRequest(BaseModel):
    """Input payload for batch failure analysis."""

    inputs: list[BatchInputItem] = Field(
        ...,
        min_length=2,
        max_length=20,
        description="List of failure inputs to analyze (2-20 items).",
    )


class BatchResultItem(BaseModel):
    """A single result within a batch analysis response."""

    index: int = Field(description="Index of the input in the batch (0-based).")
    session_id: UUID = Field(description="ID of the created analysis session.")
    status: str = Field(description="Status: completed or failed.")
    result: FailureAnalysisResult | None = Field(
        default=None,
        description="Analysis result if successful.",
    )
    error: str | None = Field(
        default=None,
        description="Error message if failed.",
    )
    provider: str | None = Field(default=None)
    model: str | None = Field(default=None)
    total_tokens: int = Field(default=0)
    latency_ms: int = Field(default=0)


class BatchAnalysisResponse(BaseModel):
    """Response from a batch analysis request."""

    batch_id: str = Field(description="UUID grouping all sessions in this batch.")
    total: int = Field(description="Total number of inputs.")
    completed: int = Field(description="Number of successfully completed analyses.")
    failed: int = Field(description="Number of failed analyses.")
    results: list[BatchResultItem] = Field(
        description="Individual analysis results, in input order.",
    )


# ── Multi-artifact input ─────────────────────────────────────────

class ArtifactUpload(BaseModel):
    """Reference to an uploaded artifact for analysis.

    This model is populated server-side after file upload; it is not
    sent by the client directly.
    """

    filename: str = Field(description="Original filename.")
    file_type: str = Field(
        description="Artifact type: 'text', 'image', or 'other'.",
    )
    mime_type: str = Field(default="", description="Detected MIME type.")
    file_size: int = Field(default=0, description="File size in bytes.")
    storage_path: str = Field(description="Relative path under artifacts directory.")
    content_preview: str = Field(
        default="",
        description="First 500 characters for text files, empty for images.",
    )


# ── Shared models ─────────────────────────────────────────────────

class StackFrame(BaseModel):
    """A single frame from a stack trace."""

    file: str = Field(description="Source file path.")
    line: int = Field(description="Line number in the source file.")
    function: str = Field(default="", description="Function or method name.")
    code: str = Field(default="", description="The source code line, if available.")


class RootCause(BaseModel):
    """Identified root cause of a failure."""

    id: str = Field(description="Unique identifier (e.g. RC-001).")
    title: str = Field(description="Short, descriptive title of the root cause.")
    description: str = Field(description="Detailed explanation of why the failure occurred.")
    category: FailureCategory = Field(description="Category of the failure.")
    severity: FailureSeverity = Field(description="How severe this failure is.")
    failing_file: str | None = Field(default=None, description="Primary file where the failure manifests.")
    failing_line: int | None = Field(default=None, description="Primary line number of the failure.")
    stack_trace: list[StackFrame] = Field(
        default_factory=list,
        description="Relevant stack trace frames.",
    )
    error_message: str = Field(
        default="",
        description="The specific error message or assertion that failed.",
    )


class SuggestedFix(BaseModel):
    """A suggested fix for a root cause."""

    id: str = Field(description="Unique identifier (e.g. FIX-001).")
    root_cause_id: str = Field(description="Reference to the root cause (e.g. RC-001).")
    description: str = Field(description="What needs to be changed to fix the issue.")
    priority: FixPriority = Field(description="How urgently this fix should be applied.")
    effort_estimate: str = Field(default="", description="Rough effort estimate (e.g. '30 minutes').")
    code_example: str | None = Field(
        default=None,
        description="Optional code snippet showing the fix.",
    )
    related_files: list[str] = Field(
        default_factory=list,
        description="Files that need to be modified.",
    )


class AffectedComponent(BaseModel):
    """A component affected by the failure."""

    id: str = Field(description="Unique identifier (e.g. CMP-001).")
    name: str = Field(description="Name of the affected component or service.")
    impact: str = Field(description="How this component is affected by the failure.")
    related_root_causes: list[str] = Field(
        default_factory=list,
        description="Root cause IDs related to this component.",
    )


class TestFailure(BaseModel):
    """Details about a specific test that failed."""

    id: str = Field(description="Unique identifier (e.g. TF-001).")
    test_name: str = Field(description="Full name of the failing test.")
    test_file: str = Field(default="", description="Test file path.")
    error_message: str = Field(default="", description="The assertion error or exception message.")
    duration_seconds: float | None = Field(default=None, description="How long the test ran before failing.")
    retry_count: int = Field(default=0, description="Number of times this test was retried.")


# ── Root output model ─────────────────────────────────────────────

class FailureAnalysisResult(BaseModel):
    """Complete structured output of a failure analysis.

    This is the document produced by the AI and stored in
    ``AnalysisSession.output_data``.
    """

    # Metadata
    input_summary: str = Field(
        description="One-paragraph summary of the failure input."
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this analysis was generated.",
    )

    # Analysis sections
    summary: str = Field(
        description="High-level summary of the failure and its impact."
    )
    root_causes: list[RootCause] = Field(
        description="Identified root causes of the failure.",
    )
    suggested_fixes: list[SuggestedFix] = Field(
        description="Suggested fixes for each root cause.",
    )
    affected_components: list[AffectedComponent] = Field(
        description="Components affected by the failure.",
    )
    test_failures: list[TestFailure] = Field(
        description="Individual test failures contained in the input.",
    )
    environment_details: list[str] = Field(
        description="Relevant environment or configuration details.",
    )
    recommendations: list[str] = Field(
        description="General recommendations to prevent similar failures.",
    )
    related_tests: list[str] = Field(
        description="Other tests that might be affected or should be re-run.",
    )


# ── API response schema ───────────────────────────────────────────

class AnalysisResponse(BaseModel):
    """API response after a successful failure analysis."""

    session_id: UUID = Field(description="ID of the analysis session.")
    status: str = Field(description="Current status of the session.")
    result: FailureAnalysisResult = Field(
        description="The complete analysis result."
    )
    provider: str | None = Field(default=None, description="AI provider used.")
    model: str | None = Field(default=None, description="AI model used.")
    total_tokens: int = Field(default=0, description="Total tokens consumed.")
    latency_ms: int = Field(default=0, description="AI call duration in milliseconds.")
    artifacts: list[ArtifactUpload] = Field(
        default_factory=list,
        description="Uploaded artifact files attached to this analysis.",
    )


class AnalysisSessionListItem(BaseModel):
    """Lightweight summary for listing past analysis sessions."""

    session_id: UUID
    title: str | None = None
    source_type: str | None = None
    status: str
    provider: str | None = None
    total_tokens: int = 0
    created_at: datetime
    updated_at: datetime
    input_summary: str | None = None
