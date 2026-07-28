/** TypeScript types for the Failure Analysis module. */

// ── Enums (union types) ───────────────────────────────────────────

export type FailureSeverity = "critical" | "high" | "medium" | "low";

export type FailureCategory =
  | "assertion_error"
  | "timeout"
  | "environment"
  | "dependency"
  | "configuration"
  | "data_issue"
  | "permission"
  | "network"
  | "compilation"
  | "unknown";

export type FixPriority = "critical" | "high" | "medium" | "low";

export type InputSourceType =
  | "plain_text"
  | "markdown"
  | "ci_log"
  | "stack_trace";

// ── Input model ───────────────────────────────────────────────────

export interface AnalysisRequest {
  content: string;
  source_type?: InputSourceType;
  title?: string | null;
  context?: string | null;
  output_format?: string;
}

// ── Data models ───────────────────────────────────────────────────

export interface StackFrame {
  file: string;
  line: number;
  function?: string;
  code?: string;
}

export interface RootCause {
  id: string;
  title: string;
  description: string;
  category: FailureCategory;
  severity: FailureSeverity;
  failing_file?: string | null;
  failing_line?: number | null;
  stack_trace?: StackFrame[];
  error_message?: string;
}

export interface SuggestedFix {
  id: string;
  root_cause_id: string;
  description: string;
  priority: FixPriority;
  effort_estimate?: string;
  code_example?: string | null;
  related_files?: string[];
}

export interface AffectedComponent {
  id: string;
  name: string;
  impact: string;
  related_root_causes?: string[];
}

export interface TestFailure {
  id: string;
  test_name: string;
  test_file?: string;
  error_message?: string;
  duration_seconds?: number | null;
  retry_count?: number;
}

export interface FailureAnalysisResult {
  input_summary: string;
  analysis_timestamp: string;
  summary: string;
  root_causes: RootCause[];
  suggested_fixes: SuggestedFix[];
  affected_components: AffectedComponent[];
  test_failures: TestFailure[];
  environment_details: string[];
  recommendations: string[];
  related_tests: string[];
}

// ── API response ──────────────────────────────────────────────────

export interface ArtifactMeta {
  filename: string;
  file_type: "text" | "image" | "other";
  mime_type?: string;
  file_size: number;
  storage_path?: string;
  content_preview?: string;
}

export interface AnalysisResponse {
  session_id: string;
  status: string;
  result: FailureAnalysisResult;
  provider?: string | null;
  model?: string | null;
  total_tokens?: number;
  latency_ms?: number;
  artifacts?: ArtifactMeta[];
}

export interface AnalysisSessionListItem {
  session_id: string;
  title?: string | null;
  source_type?: string | null;
  status: string;
  provider?: string | null;
  total_tokens?: number;
  created_at: string;
  updated_at: string;
  input_summary?: string | null;
}

// ── Batch Analysis ─────────────────────────────────────────────────

export interface BatchInputItem {
  content: string;
  source_type?: InputSourceType;
  title?: string | null;
  context?: string | null;
}

export interface BatchAnalysisRequest {
  inputs: BatchInputItem[];
}

export interface BatchResultItem {
  index: number;
  session_id: string;
  status: "completed" | "failed";
  result?: FailureAnalysisResult | null;
  error?: string | null;
  provider?: string | null;
  model?: string | null;
  total_tokens?: number;
  latency_ms?: number;
}

export interface BatchAnalysisResponse {
  batch_id: string;
  total: number;
  completed: number;
  failed: number;
  results: BatchResultItem[];
}
